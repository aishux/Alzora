from fivetran_connector_sdk import Connector, Logging as log, Operations as op
import json
import logging
import certifi
from pytidb import TiDBClient
from datetime import datetime, timezone


# Define the schema function to specify the destination schema for the connector.
def schema(configuration: dict):
    # Ensure the required config key is present
    if 'TABLES_PRIMARY_KEY_COLUMNS' not in configuration:
        raise ValueError("Could not find 'TABLES_PRIMARY_KEY_COLUMNS' in configuration")
    
    schema_list = []

    tables_and_primary_key_columns = configuration["TABLES_PRIMARY_KEY_COLUMNS"]

    for table_name, primary_key_column in tables_and_primary_key_columns.items():
        schema_list.append({"table": table_name, "primary_key": [primary_key_column]})

    if configuration.get("VECTOR_TABLES_DATA"):
        vector_tables_data = configuration["VECTOR_TABLES_DATA"]
        for table_name, table_data in vector_tables_data.items():
            schema_list.append({"table": table_name, "primary_key": [table_data["primary_key_column"]], "columns": {table_data["vector_column"]:"JSON"}})

    
    return schema_list


def parse_embedding_string_to_list(s):
    if s is None:
        return None
    # fast try: JSON parse
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
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
                logging.warning(f"Failed to parse embedding element '{p}'")
                return None
        return out
    return None

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
        # Handle possible 'Z'
        timestamp_str = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if timestamp_str.tzinfo is None:
            timestamp_str = timestamp_str.replace(tzinfo=timezone.utc)
        return timestamp_str
    except ValueError:
        return datetime(1990, 1, 1, tzinfo=timezone.utc)

def process_row(row_data, table_name, configuration, is_vector_table):

    if row_data.get("created_at") and row_data["created_at"].tzinfo is None:
        row_data["created_at"] = row_data["created_at"].replace(tzinfo=timezone.utc)

    if row_data.get("updated_at") and row_data["updated_at"].tzinfo is None:
        row_data["updated_at"] = row_data["updated_at"].replace(tzinfo=timezone.utc)

    
    if is_vector_table:
        embedding_column = configuration[table_name]["vector_column"]
        raw_embeddings = row_data.get(embedding_column)
        emb_list = parse_embedding_string_to_list(raw_embeddings)
        if emb_list is not None:
            # Put the parsed list into a JSON field for Fivetran
            # Fivetran will write this as JSON to BigQuery destination
            row_data[embedding_column] = emb_list

    return row_data


def fetch_and_upsert_data(cursor: TiDBClient, table_name: str, state: dict, configuration:dict, is_vector_table: bool = False):
    last_created = state.get(f"{table_name}_last_created", "1990-01-01T00:00:00Z")
    last_created_timestamp = parse_state_timestamp(timestamp_str=last_created)

    tidb_timestamp = last_created.replace("T", " ").replace("Z", "")

    tidb_query = f"SELECT * FROM {table_name} WHERE created_at > '{tidb_timestamp}' ORDER BY created_at"
    
    query_result = cursor.query(tidb_query).to_list()

    for row in query_result:
        row_data = process_row(row, table_name, configuration, is_vector_table)
        op.upsert(table=table_name, data=row_data)

        if row_data.get("created_at") and row_data["created_at"] > last_created_timestamp:
            last_created_timestamp = row_data["created_at"]

    state[f"{table_name}_last_created"] = last_created_timestamp.isoformat()

    op.checkpoint(state)


def create_tidb_connection(configuration:dict):
    TIDB_DATABASE_URL=f"mysql+pymysql://{configuration['TIDB_USER']}:{configuration['TIDB_PASS']}@{configuration['TIDB_HOST']}:{configuration['TIDB_PORT']}/{configuration['TIDB_DATABASE']}?ssl_ca={certifi.where()}"

    connection = TiDBClient.connect(TIDB_DATABASE_URL)

    return connection


def update(configuration: dict, state: dict):
    connection = create_tidb_connection(configuration=configuration)

    tables = configuration["TABLES_PRIMARY_KEY_COLUMNS"].keys()

    for table_name in tables:
        fetch_and_upsert_data(cursor=connection, table_name=table_name, state=state, configuration=configuration)
    
    if configuration.get("VECTOR_TABLES_DATA"):

        vector_tables = configuration["VECTOR_TABLES_DATA"].keys()

        for table_name in vector_tables:
            fetch_and_upsert_data(cursor=connection, table_name=table_name, state=state, configuration=configuration, is_vector_table=True)



# Initialize the Connector with our update (and schema) functions
connector = Connector(update=update, schema=schema)

# Allow running this script directly for local debugging
if __name__ == "__main__":
    # Load configuration from file when running locally
    with open("configuration.json", "r") as f:
        configuration = json.load(f)
    # Run the connector in debug mode with the provided configuration    
    connector.debug(configuration=configuration)