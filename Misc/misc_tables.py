#!/usr/bin/env python3
"""
insert_dummy_data_global.py

- Inserts 10 global patients + 10 caretakers + metadata + usual spots + memories into TiDB.
- Uses pytidb.TiDBClient.insert for batched inserts.
- Configure connection via environment variables: TIDB_HOST, TIDB_PORT, TIDB_USER, TIDB_PASS, TIDB_DATABASE
"""

import os
import json
import random
import datetime
import numpy as np
from pytidb import TiDBClient
from dotenv import load_dotenv
from pytidb.schema import TableModel, Field, VectorField, DistanceMetric

load_dotenv()

# ---- CONFIG (from env) ----
TIDB_HOST = os.getenv("TIDB_HOST")
TIDB_USER = os.getenv("TIDB_USER")
TIDB_PASS = os.getenv("TIDB_PASS")
TIDB_PORT = os.getenv("TIDB_PORT")
TIDB_DATABASE = os.getenv("TIDB_DATABASE")

TIDB_DATABASE_URL=f"mysql+pymysql://{TIDB_USER}:{TIDB_PASS}@{TIDB_HOST}:{TIDB_PORT}/{TIDB_DATABASE}?ssl_ca=/etc/ssl/cert.pem"

SEED = 12345
random.seed(SEED)
np.random.seed(SEED)


class Caretakers(TableModel, table=True):
    __tablename__ = "caretakers"

    caretaker_id: int = Field(primary_key=True)
    full_name: str = Field()
    email: str = Field(unique=True)
    patient_ids: str | None = Field(default=None)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)


class Patients(TableModel, table=True):
    __tablename__ = "patients"

    patient_id: int = Field(primary_key=True)
    first_name: str = Field()
    last_name: str | None = Field(default=None)
    safe_center_lat: float | None = Field(default=None)
    safe_center_long: float | None = Field(default=None)
    safe_radius_meters: int | None = Field(default=100)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)


class Memories(TableModel, table=True):
    __tablename__ = "memories"

    memory_id: int = Field(primary_key=True)
    patient_id: int = Field()
    text_embedding: list[float] | None = VectorField(dimensions=512, distance_metric=DistanceMetric.L2)
    image_embedding: list[float] | None = VectorField(dimensions=512, distance_metric=DistanceMetric.L2)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)


class PatientMetadata(TableModel, table=True):
    __tablename__ = "patient_metadata"

    metadata_id: int = Field(primary_key=True)
    patient_id: int = Field()
    metadata_content: str | None = Field(default=None)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)


class UsualSpots(TableModel, table=True):
    __tablename__ = "usual_spots"

    spot_id: int = Field(primary_key=True)
    patient_id: int = Field()
    item_name: str = Field()
    location_description: str | None = Field(default=None)
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)

# ---- HELPERS ----
def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def random_vector(dim=512):
    return np.random.rand(dim).astype(float).tolist()

# ---- GLOBAL (non-Indian) NAMES / LOCATIONS ----
# 10 global patient names and 10 global caretaker names
patient_names = [
    ("Oliver", "Smith"),    # London-like
    ("Emma", "Johnson"),    # US-like
    ("Lucas", "Martin"),    # France/Europe-like
    ("Sophia", "Brown"),    # English-speaking
    ("Mateo", "Garcia"),    # Spain/Latin America
    ("Hana", "Kobayashi"),  # Japan-like
    ("Liam", "O'Connor"),   # Ireland-like
    ("Isabella", "Rossi"),  # Italy-like
    ("Noah", "Silva"),      # Brazil/Portugal-like
    ("Maya", "Nguyen"),     # Vietnam/SE Asia-like
]

caretaker_names = [
    "Ava Müller", "Ethan Williams", "Mia Anderson", "Oliver Jensen",
    "Chloe Dubois", "Luca Romano", "Amelia Wilson", "Ethan Carter",
    "Zoe Park", "Benjamin Lee"
]

# pick 10 diverse home centers (lat, lon) across world cities for safe zones
home_centers = [
    (51.5074, -0.1278),   # London
    (40.7128, -74.0060),  # New York
    (48.8566, 2.3522),    # Paris
    (-33.8688, 151.2093), # Sydney
    (35.6762, 139.6503),  # Tokyo
    (52.5200, 13.4050),   # Berlin
    (-23.5505, -46.6333), # São Paulo
    (43.6532, -79.3832),  # Toronto
    (-33.9249, 18.4241),  # Cape Town
    (25.2048, 55.2708),   # Dubai
]

# example usual spots to vary per patient
usual_spots_examples = [
    ("Glasses", "On the nightstand"),
    ("Wallet", "Second drawer of living room cabinet"),
    ("Keys", "Hook near the front door"),
    ("Phone", "Charging dock on the kitchen counter"),
    ("Medication", "Top shelf of bathroom cabinet"),
    ("Watch", "Left bedside table"),
    ("Remote", "Couch cushion pocket"),
    ("Hat", "Coat rack in the hallway"),
    ("Umbrella", "Stand near the entrance"),
    ("Reading glasses", "Bookshelf near the armchair")
]

# ---- MAIN DATA CREATION ----
def build_patients():
    patients = []
    for i, (fn, ln) in enumerate(patient_names):
        lat, lon = home_centers[i]
        # small jitter to avoid identical exact coordinates
        lat_j = lat + np.random.normal(scale=0.002)
        lon_j = lon + np.random.normal(scale=0.002)
        age = random.randint(65, 85)
        p = {
            "first_name": fn,
            "last_name": ln,
            "safe_center_lat": float(lat_j),
            "safe_center_long": float(lon_j),
            "safe_radius_meters": random.choice([150, 200, 300]),
            "created_at": now(),
            "updated_at": now(),
            "age": age
        }
        patients.append(p)
    return patients

def build_caretakers():
    caretakers = []
    for name in caretaker_names:
        parts = name.split()
        full_name = name
        # email derive
        email = f"{parts[0].lower()}.{parts[-1].lower()}@example.com"
        caretakers.append({
            "full_name": full_name,
            "email": email,
            "created_at": now(),
            "updated_at": now()
        })
    return caretakers

def build_patient_metadata(patients):
    metadata_rows = []
    for p in patients:
        age = p.get("age", random.randint(66, 82))
        # simple medical history examples
        med_hist = random.choice([
            "Hypertension; Mild cognitive impairment",
            "Type 2 diabetes; Mild cognitive decline",
            "Hyperlipidemia; Early Alzheimer's symptoms",
            "No major chronic conditions; occasional memory lapses",
            "Vascular disease; early-stage dementia"
        ])
        meds = random.choice([
            ["Donepezil"],
            ["Memantine"],
            ["Metformin"],
            ["Lisinopril"],
            ["Atorvastatin"]
        ])
        meta = {
            "medical_history": med_hist,
            "medications": meds,
            "age": age,
            "gender": random.choice(["Male", "Female"]),
            "notes": random.choice([
                "Needs help locating daily items occasionally.",
                "Has a smartwatch for monitoring; caregiver checks daily.",
                "Active socially; shows recent forgetfulness.",
                "Lives with spouse; caregivers listed.",
                "Occasional nighttime wandering observed."
            ])
        }
        metadata_rows.append(meta)
    return metadata_rows

def build_usual_spots_for_patient():
    # pick 3 distinct usual spots per patient
    spots = []
    choices = random.sample(usual_spots_examples, k=3)
    for item_name, location_description in choices:
        spots.append({
            "item_name": item_name,
            "location_description": location_description,
            "created_at": now(),
            "updated_at": now()
        })
    return spots

def build_memories_for_patient(patient_id):
    # create 3 memory entries with random vectors
    mems = []
    for _ in range(3):
        mems.append({
            "patient_id": patient_id,
            "text_embedding": json.dumps(random_vector(512)),
            "image_embedding": json.dumps(random_vector(512)),
            "created_at": now(),
            "updated_at": now()
        })
    return mems

# ---- DB INSERT LOGIC ----
def insert_all():
    client = TiDBClient.connect(TIDB_DATABASE_URL)

    # 1) Patients
    patients = build_patients()
    patient_rows = []
    for p in patients:
        patient_rows.append({
            "first_name": p["first_name"],
            "last_name": p["last_name"],
            "safe_center_lat": p["safe_center_lat"],
            "safe_center_long": p["safe_center_long"],
            "safe_radius_meters": p["safe_radius_meters"],
            "created_at": p["created_at"],
            "updated_at": p["updated_at"]
        })
    table = client.open_table("patients")
    table.bulk_insert(patient_rows)
    print("Inserted patients.")

    # fetch patient_ids (ordered insertion)
    patient_rows_db = client.query("SELECT patient_id, first_name, last_name FROM patients ORDER BY patient_id DESC LIMIT 10").to_rows()
    # query returned descending; reorder by id ascending to map our created ones (safer approach: fetch last N and sort)
    patient_rows_db = sorted(patient_rows_db, key=lambda r: r[0])
    patient_ids = [r[0] for r in patient_rows_db]

    # 2) Caretakers and assign patient_ids (random 1-4 per caretaker)
    caretakers = build_caretakers()
    caretaker_rows = []
    for c in caretakers:
        assigned = random.sample(patient_ids, k=random.randint(1, min(4, len(patient_ids))))
        caretaker_rows.append({
            "full_name": c["full_name"],
            "email": c["email"],
            "patient_ids": json.dumps(assigned),
            "created_at": c["created_at"],
            "updated_at": c["updated_at"]
        })
    table = client.open_table("caretakers")
    table.bulk_insert(caretaker_rows)
    print("Inserted caretakers and assignments.")

    # 3) Patient metadata (one per patient)
    metadata_list = build_patient_metadata(patients)
    meta_rows = []
    for pid, meta in zip(patient_ids, metadata_list):
        meta_rows.append({
            "patient_id": pid,
            "metadata_content": json.dumps(meta),
            "created_at": now(),
            "updated_at": now()
        })
    table = client.open_table("patient_metadata")
    table.bulk_insert(meta_rows)
    print("Inserted patient metadata.")

    # 4) Usual spots (3 per patient)
    spots_rows = []
    for pid in patient_ids:
        spots = build_usual_spots_for_patient()
        for s in spots:
            row = {
                "patient_id": pid,
                "item_name": s["item_name"],
                "location_description": s["location_description"],
                "created_at": s["created_at"],
                "updated_at": s["updated_at"]
            }
            spots_rows.append(row)
    table = client.open_table("usual_spots")
    table.bulk_insert(spots_rows)
    print("Inserted usual spots.")

    # 5) Memories (3 per patient)
    mem_rows = []
    for pid in patient_ids:
        for _ in range(3):
            mem_rows.append({
                "patient_id": pid,
                "text_embedding": random_vector(512),
                "image_embedding": random_vector(512),
                "created_at": now(),
                "updated_at": now()
            })
    table = client.open_table("memories")
    table.bulk_insert(mem_rows)
    print("Inserted memories.")

    print("✅ All dummy data inserted successfully.")

if __name__ == "__main__":
    insert_all()
