from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

def upload_file_to_gcs(file_obj, filename: str) -> str:
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    blob.upload_from_file(file_obj, content_type="application/pdf")

    return f"gs://{BUCKET_NAME}/{filename}"