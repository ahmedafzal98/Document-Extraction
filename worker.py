import logging
from datetime import datetime, date
import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from google.cloud import pubsub_v1
import json
import os
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

# ------------------- Load .env -------------------
load_dotenv()

# ------------------- Configure logging -------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------- Database setup -------------------
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# Validate database variables
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    logging.error("Database environment variables are missing! Please check your .env file.")
    exit(1)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ------------------- Pub/Sub setup -------------------
PROJECT_ID = os.getenv("PROJECT_ID")
SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION_ID")

if not all([PROJECT_ID, SUBSCRIPTION_ID]):
    logging.error("Pub/Sub environment variables are missing! Please check your .env file.")
    exit(1)

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

# ------------------- Helper Functions -------------------
def ensure_date(value):
    """Convert value to datetime.date or return None for invalid/unparseable dates."""
    if isinstance(value, date):
        return value
    if value in (None, "", "NaT") or (isinstance(value, str) and "N/A" in value):
        return None
    for fmt in ("%m-%d-%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    logging.warning(f"Failed to parse date: {value}")
    return None

def fuzzy_similarity(a, b):
    """Return fuzzy match score between 0 and 100 using fuzzywuzzy"""
    if not a or not b:
        return 0
    return fuzz.ratio(a.lower(), b.lower())

def process_document(document, dataset_file, db_session):
    document_id = document.get("document_id")
    try:
        dataset_rows = db_session.execute("SELECT * FROM dataset_records").fetchall()
        for idx, row in dataset_rows.iterrows():
            # Dataset fields
            dataset_name = row.get("Dataset_Name")
            dataset_doa = ensure_date(row.get("Dataset_DOA"))
            dataset_dob = ensure_date(row.get("Dataset_DOB"))
            dataset_referral = row.get("Dataset_Referral", "")

            # Extracted fields (replace with your extraction logic)
            extracted_name = row.get("Extracted_Name", "")
            extracted_doa = ensure_date(row.get("Extracted_DOA"))
            extracted_dob = ensure_date(row.get("Extracted_DOB"))
            extracted_referral = row.get("Extracted_Referral", "")

       # Compute fuzzy scores and matches
            name_score = fuzzy_similarity(dataset_name, extracted_name)
            doa_match = dataset_doa == extracted_doa
            dob_match = dataset_dob == extracted_dob
            referral_score = fuzzy_similarity(dataset_referral, extracted_referral)
            referral_match = referral_score > 80  # 80% match for referral

            if name_score > 80 and doa_match and dob_match:
                match_status = "Exact Match"
            elif name_score > 70 or doa_match or dob_match:
                match_status = "Partial Match"
            else:
                match_status = "Mismatch"

            # Insert into database

            db_session.execute(
                text("""
                    INSERT INTO matches 
                    (document_id, dataset_index, dataset_name, dataset_doa, dataset_dob, dataset_referral,
                    extracted_name, extracted_doa, extracted_dob, extracted_referral,
                    name_score, doa_match, dob_match, referral_score, referral_match, match_status)
                    VALUES 
                    (:document_id, :dataset_index, :dataset_name, :dataset_doa, :dataset_dob, :dataset_referral,
                    :extracted_name, :extracted_doa, :extracted_dob, :extracted_referral,
                    :name_score, :doa_match, :dob_match, :referral_score, :referral_match, :match_status)
                """),
                {
                    "document_id": document_id,
                    "dataset_index": idx,
                    "dataset_name": dataset_name,
                    "dataset_doa": dataset_doa,
                    "dataset_dob": dataset_dob,
                    "dataset_referral": dataset_referral,
                    "extracted_name": extracted_name,
                    "extracted_doa": extracted_doa,
                    "extracted_dob": extracted_dob,
                    "extracted_referral": extracted_referral,
                    "name_score": name_score,
                    "doa_match": doa_match,
                    "dob_match": dob_match,
                    "referral_score": referral_score,
                    "referral_match": referral_match,
                    "match_status": match_status,
                }
            )

        db_session.commit()
        logging.info(f"Document {document_id} processed successfully.")
    except SQLAlchemyError as e:
        db_session.rollback()
        logging.error(f"Document {document_id} failed (DB error): {e}")
    except Exception as e:
        logging.error(f"Document {document_id} failed (Unexpected error): {e}")

# ------------------- Pub/Sub Callback -------------------
def callback(message):
    logging.info(f"📩 Received message: {message.data}")
    try:
        batch = json.loads(message.data)
        db_session = SessionLocal()
        for document in batch.get("documents", []):
            dataset_file = batch.get("dataset_file")
            if not dataset_file or not os.path.exists(dataset_file):
                logging.warning(f"Dataset file missing or not found: {dataset_file}")
                continue
            process_document(document, dataset_file, db_session)
    finally:
        db_session.close()
    message.ack()

# ------------------- Main Listener -------------------
def main():
    logging.info("👂 Worker listening for batch messages...")
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        logging.info("Worker stopped.")

if __name__ == "__main__":
    main()
