import json
from google.cloud import pubsub_v1
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_ID = "pdf-processing-topic"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

def publish_document_message(document_id: int, gcs_path: str):
    message = {
        "documents": [
            {
                "document_id": document_id,
                "gcs_path": gcs_path
            }
        ],
        "dataset_file": "client_dataset.csv"
    }

    publisher.publish(
        topic_path,
        json.dumps(message).encode("utf-8")
    )
