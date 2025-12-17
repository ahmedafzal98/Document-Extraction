import json
import logging
import os
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_ID = os.getenv("PUBSUB_TOPIC_ID", "pdf-processing-topic")

_publisher = None


def get_publisher():
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


def publish_document_message(document_id: int, gcs_path: str):
    if not PROJECT_ID:
        raise RuntimeError("PROJECT_ID is not set")

    publisher = get_publisher()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    message = {
        "documents": [
            {
                "document_id": document_id,
                "gcs_path": gcs_path
            }
        ],
        "dataset_file": "client_dataset.csv"
    }

    try:
        future = publisher.publish(
            topic_path,
            json.dumps(message).encode("utf-8")
        )

        message_id = future.result(timeout=10)
        logger.info(f"📤 Pub/Sub message published: {message_id}")

        return message_id

    except Exception as e:
        logger.error(f"❌ Failed to publish Pub/Sub message: {e}")
        raise
