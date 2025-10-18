import os
from pytidb import TiDBClient
from pytidb.schema import TableModel, Field, VectorField, DistanceMetric
from dotenv import load_dotenv
import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
import time
from random import randint

load_dotenv()


# ── CONFIG ────────────────────────────────────────────────────────────────
TIDB_HOST = os.getenv("TIDB_HOST")
TIDB_USER = os.getenv("TIDB_USER")
TIDB_PASS = os.getenv("TIDB_PASS")
TIDB_PORT = os.getenv("TIDB_PORT")
TIDB_DATABASE = os.getenv("TIDB_DATABASE")

TIDB_DATABASE_URL=f"mysql+pymysql://{TIDB_USER}:{TIDB_PASS}@{TIDB_HOST}:{TIDB_PORT}/{TIDB_DATABASE}?ssl_ca=/etc/ssl/cert.pem"

db = TiDBClient.connect(TIDB_DATABASE_URL)

model = ""
embedding_dimension = 512

def initialize_model():
    global model
    PROJECT_ID = "alzora-474820"
    vertexai.init(project=PROJECT_ID, location="us-central1")
    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
    print("Initialising Model ...")
    

def get_embeddings(image_list, mri_scan_type):
    count = 1542 + randint(234,99932)
    object_list = []
    for image_path in image_list:
        image = Image.load_from_file(
            image_path
        )

        try:
            embeddings = model.get_embeddings(
                image=image,
                dimension=embedding_dimension,
            )
        except Exception as e:
            print("Entered exception waiting for a min...")
            time.sleep(60)
            initialize_model()

            embeddings = model.get_embeddings(
                image=image,
                dimension=embedding_dimension,
            )

        object_list.append(MriImageEmbeddings(
            id = count,
            mri_scan_type = mri_scan_type,
            embedding = embeddings.image_embedding
        ))

        count = count + randint(234,99932)

    return object_list


class MriImageEmbeddings(TableModel, table=True):
    __tablename__ = "mri_image_embeddings"

    id: int = Field(primary_key=True)
    mri_scan_type: str = Field()
    embedding: list[float] = VectorField(dimensions=512, distance_metric=DistanceMetric.L2)

table = db.create_table(schema=MriImageEmbeddings, if_exists="skip")

print("Connected to TiDB database and created table!")

initialize_model()

dataset_dir = "../Datasets/MRI_Dataset"

curr_image_list = []

for class_name in sorted(os.listdir(dataset_dir)):
    for fname in sorted(os.listdir(os.path.join(dataset_dir,class_name)))[:100]:
        image_path = os.path.abspath(os.path.join(dataset_dir, class_name, fname))
        curr_image_list.append(image_path)

        if len(curr_image_list) == 10:
            curr_object_list = get_embeddings(curr_image_list, class_name)
            print("Got the embeddings for 10 images!")
            curr_image_list = []
            db = TiDBClient.connect(TIDB_DATABASE_URL)
            table = db.open_table("mri_image_embeddings")
            table.bulk_insert(curr_object_list)
            print("10 batch objects inserted to TiDB!")
            time.sleep(60)

print("Done with all objects")