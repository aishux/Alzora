from fivetran_connector_sdk import Connector, Logging as log, Operations as op
import json
import logging
import certifi
from pytidb import TiDBClient
from datetime import datetime, timezone


# -----------------------------
# Schema helper
# -----------------------------
# The `schema` function declares the destination schema that Fivetran expects.
# It must return a list of dictionaries where each dict describes a table + its
# primary key columns (and optional typed columns). The connector SDK uses this
# to know how to write/upsert records.
def schema(configuration: dict):
    # Ensure the required config key is present
    if 'TABLES_PRIMARY_KEY_COLUMNS' not in configuration:
        raise ValueError("Could not find 'TABLES_PRIMARY_KEY_COLUMNS' in configuration")
    
    schema_list = []

    tables_and_primary_key_columns = configuration["TABLES_PRIMARY_KEY_COLUMNS"]

    for table_name, primary_key_column in tables_and_primary_key_columns.items():
        # Add a simple table entry for each configured table + its primary key
        schema_list.append({"table": table_name, "primary_key": [primary_key_column]})

    # Optional: vector table metadata. These are appended to the schema list
    # and include a typed column (JSON) for the vector payload so Fivetran will
    # treat it as structured JSON on destination (e.g. BigQuery JSON column).
    if configuration.get("VECTOR_TABLES_DATA"):
        vector_tables_data = configuration["VECTOR_TABLES_DATA"]
        for table_name, table_data in vector_tables_data.items():
            schema_list.append({
                "table": table_name,
                "primary_key": [table_data["primary_key_column"]],
                "columns": {table_data["vector_column"]: "JSON"}
            })

    return schema_list


# -----------------------------
# Utility: parse embedding string
# -----------------------------
# The connector sometimes reads embeddings serialized as strings (e.g. "[0.1, 0.2]")
# This helper tries JSON parsing first and falls back to a cheap CSV-like parse.
# Returns: list[float] or None on failure.
def parse_embedding_string_to_list(s):
    if s is None:
        return None
    # fast try: JSON parse
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            # Ensure floats — defensive cast
            return [float(x) for x in parsed]
    except Exception:
        pass
    # fallback: strip brackets and split
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if inner == "":
            return []
        parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
        out = []
        for p in parts:
            if p == "":
                continue
            try:
                out.append(float(p))
            except Exception:
                # Important: log the failed parse so operator can inspect bad data
                logging.warning(f"Failed to parse embedding element '{p}'")
                return None
        return out
    return None


# -----------------------------
# Utility: parse timestamp from state
# -----------------------------
# The connector stores the last processed timestamp per-table in `state`.
# This helper turns that string into a timezone-aware datetime or returns a
# sentinel far-past datetime if parsing fails or value is missing.
def parse_state_timestamp(timestamp_str):
    """
    Parse the last_timestamp from the state dictionary.
    If the timestamp is not present or invalid, return a default datetime.
    Args:
        timestamp_str: a string representing the last processed timestamp
    Returns:
        A datetime object representing the last processed timestamp.
    """
    if not timestamp_str:
        return datetime(1990, 1, 1, tzinfo=timezone.utc)
    try:
        # Use fromisoformat after normalizing Z -> +00:00 so it parses cleanly
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        # Return a safe default (far past) if parsing fails
        return datetime(1990, 1, 1, tzinfo=timezone.utc)


# -----------------------------
# Row processing
# -----------------------------
# Normalize timezone on datetime fields and parse vector columns when present.
def process_row(row_data, table_name, configuration, is_vector_table):

    if row_data.get("created_at") and hasattr(row_data["created_at"], "tzinfo") and row_data["created_at"].tzinfo is None:
        row_data["created_at"] = row_data["created_at"].replace(tzinfo=timezone.utc)

    if row_data.get("updated_at") and hasattr(row_data["updated_at"], "tzinfo") and row_data["updated_at"].tzinfo is None:
        row_data["updated_at"] = row_data["updated_at"].replace(tzinfo=timezone.utc)

    # If this is a configured vector table, parse the embedding column
    if is_vector_table:
        embedding_column = configuration[table_name]["vector_column"]
        raw_embeddings = row_data.get(embedding_column)
        emb_list = parse_embedding_string_to_list(raw_embeddings)
        if emb_list is not None:
            # Put the parsed list into a JSON-friendly Python list; Fivetran will
            # write it as JSON to destinations that support JSON types.
            row_data[embedding_column] = emb_list

    return row_data


# -----------------------------
# Core ingestion: fetch and upsert
# -----------------------------
# Fetch rows newer than the stored state and upsert them to the destination
# using the Fivetran operations API.
def fetch_and_upsert_data(cursor: TiDBClient, table_name: str, state: dict, configuration:dict, is_vector_table: bool = False):
    # Read last processed timestamp for this table from state (string)
    last_created = state.get(f"{table_name}_last_created", "1990-01-01T00:00:00Z")
    last_created_timestamp = parse_state_timestamp(timestamp_str=last_created)

    tidb_timestamp = last_created.replace("T", " ").replace("Z", "")

    tidb_query = f"SELECT * FROM {table_name} WHERE created_at > '{tidb_timestamp}' ORDER BY created_at"
    
    # Execute query and expect an iterable of dict-like rows
    query_result = cursor.query(tidb_query).to_list()

    for row in query_result:
        # Process the row (normalize datetimes, parse embeddings)
        row_data = process_row(row, table_name, configuration, is_vector_table)
        # Upsert into destination using Fivetran's operations API
        op.upsert(table=table_name, data=row_data)

        # If the row has a created_at and it's newer than our last seen
        if row_data.get("created_at") and row_data["created_at"] > last_created_timestamp:
            last_created_timestamp = row_data["created_at"]

    # Persist the last processed timestamp back to state
    state[f"{table_name}_last_created"] = last_created_timestamp.isoformat()

    # Instruct the connector framework to checkpoint (persist) state
    op.checkpoint(state)


# -----------------------------
# TiDB connection helper
# -----------------------------
def create_tidb_connection(configuration:dict):
    user = configuration.get("TIDB_USER")
    password = configuration.get("TIDB_PASS")
    host = configuration.get("TIDB_HOST")
    port = configuration.get("TIDB_PORT")
    database = configuration.get("TIDB_DATABASE")

    # Build DSN conservatively.
    TIDB_DATABASE_URL = (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?ssl_ca={certifi.where()}"
    )

    connection = TiDBClient.connect(TIDB_DATABASE_URL)

    return connection


# -----------------------------
# Update function called by the connector
# -----------------------------
# This is the main loop invoked by the Fivetran runtime. It must be idempotent
# and should be robust to retries. Keep the function small and push heavy work
# into helper functions so errors can be handled in isolation.
def update(configuration: dict, state: dict):
    # Create a TiDB connection
    connection = create_tidb_connection(configuration=configuration)

    # Read list of tables from configuration. Expect a dict mapping table->pk
    tables = configuration["TABLES_PRIMARY_KEY_COLUMNS"].keys()

    # Iterate the non-vector tables first
    for table_name in tables:
        fetch_and_upsert_data(cursor=connection, table_name=table_name, state=state, configuration=configuration)
    
    # Process optional vector tables
    if configuration.get("VECTOR_TABLES_DATA"):

        vector_tables = configuration["VECTOR_TABLES_DATA"].keys()

        for table_name in vector_tables:
            fetch_and_upsert_data(cursor=connection, table_name=table_name, state=state, configuration=configuration, is_vector_table=True)


# -----------------------------
# Connector bootstrap
# -----------------------------
connector = Connector(update=update, schema=schema)

# Allow running this script directly for local debugging
if __name__ == "__main__":
    # Load configuration from file when running locally
    with open("configuration.json", "r") as f:
        configuration = json.load(f)
    # Run the connector in debug mode with the provided configuration    
    connector.debug(configuration=configuration)
