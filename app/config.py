import os

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us")
PROCESSOR_ID = os.getenv("PROCESSOR_ID")

PUBSUB_SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATASET_FILE = os.getenv("DATASET_FILE", "client_dataset.csv")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "matching_results.xlsx")
