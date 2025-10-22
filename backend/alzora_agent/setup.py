from google.cloud import bigquery
from pytidb import TiDBClient
from pytidb.schema import TableModel, Field, VectorField, DistanceMetric
import os
from typing import List, Optional
from google.adk.agents import Agent
from google.adk.tools import google_search
import certifi
import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel, Image
from vertexai.language_models import TextEmbeddingModel
import io



# ── CONFIG ────────────────────────────────────────────────────────────────
TIDB_HOST = os.getenv("TIDB_HOST")
TIDB_USER = os.getenv("TIDB_USER")
TIDB_PASS = os.getenv("TIDB_PASS")
TIDB_PORT = os.getenv("TIDB_PORT")
TIDB_DATABASE = os.getenv("TIDB_DATABASE")
JINA_AI_API_KEY = os.getenv("JINA_AI_API_KEY")
# ── END CONFIG ────────────────────────────────────────────────────────────


TIDB_DATABASE_URL=f"mysql+pymysql://{TIDB_USER}:{TIDB_PASS}@{TIDB_HOST}:{TIDB_PORT}/{TIDB_DATABASE}?ssl_ca={certifi.where()}"

db = TiDBClient.connect(TIDB_DATABASE_URL)

bigquery_client = bigquery.Client()

embedding_dimension = 512
image_embedding_model = None
text_embedding_model = None

search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    description="Specialist agent for web search",
    instruction="Use Google Search to fetch information for the given query.",
    tools=[google_search],
    output_key="search_results",
)

class Memories(TableModel, table=True):
    __tablename__ = "memories"

    memory_id: int = Field(primary_key=True)
    patient_id: int = Field()
    text_content: str = Field()
    text_embedding: list[float] = VectorField(dimensions=512, distance_metric=DistanceMetric.L2)
    image_embedding: list[float] = VectorField(dimensions=512, distance_metric=DistanceMetric.L2)
    created_at: str =  Field()
    updated_at: str = Field()


def get_bigquery_data(query):
    query_job = bigquery_client.query(query)
    rows = query_job.result()
    return rows

def reconnect_db():
    global db
    print("Refreshing database connection..")
    db = TiDBClient.connect(TIDB_DATABASE_URL)
    return db

def query_tidb(query):
    try:
        res = db.query(query)
    except Exception as e:
        db = reconnect_db()
        res = db.query(query)
    return res

def get_tidb_table(table_name):
    try:
        current_table = db.open_table(table_name)
    except Exception as e:
        reconnect_db()
        current_table = db.open_table(table_name)
    return current_table


def initialize_image_embedding_model():
    global image_embedding_model
    PROJECT_ID = "alzora-474820"
    vertexai.init(project=PROJECT_ID, location="us-central1")
    image_embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
    print("Initialising Image Embedding Model ...")


def initialize_text_embedding_model():
    global text_embedding_model
    PROJECT_ID = "alzora-474820"
    vertexai.init(project=PROJECT_ID, location="us-central1")
    text_embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
    print("Initialising Text Embedding Model ...")


def get_image_embeddings(image_blob, text_content):
    global image_embedding_model

    if image_embedding_model is None:
        initialize_image_embedding_model()

    try:
        img_bytes = io.BytesIO()
        image_blob.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()
        vertex_image = Image(image_bytes=img_bytes)

        embeddings = image_embedding_model.get_embeddings(
            image=vertex_image,
            contextual_text=text_content,
            dimension=embedding_dimension,
        )

        print("Got the embeddings")

        return {"Image Embedding": embeddings.image_embedding, "Text Embedding": embeddings.text_embedding}

    except Exception as e:
        print("Encountered Exception while embedding image!!")
        print(e)

    return None

def get_text_embeddings(text_content):
    global text_embedding_model
    
    if text_embedding_model is None:
        initialize_text_embedding_model()

    try:
        text_embeddings = text_embedding_model.get_embeddings(texts=list(text_content), output_dimensionality=512)
        print("Got the text Embeddings!")
        return text_embeddings[0].values
    except Exception as e:
        print("Encountered Exception while embedding text!!")
        print(e)
    return None