# app/routes/upload_routes.py
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from uuid import uuid4

from app.db import get_db
from app.models.tables import Document
from app.services.gcs_service import upload_file_to_gcs
from app.services.pubsub_service import publish_document_message

router = APIRouter(tags=["Upload"])

@router.post("/upload")
def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload one or more PDFs to GCS, save in DB, and queue for processing via Pub/Sub.
    """
    uploaded_docs = []

    for file in files:
        try:
            # 1️⃣ Generate unique filename
            unique_name = f"{uuid4()}_{file.filename}"

            # 2️⃣ Upload file to GCS
            gcs_path = upload_file_to_gcs(file.file, unique_name)

            # 3️⃣ Save record in DB
            document = Document(
                file_name=file.filename,
                gcs_path=gcs_path,
                status="uploaded"
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            # 4️⃣ Publish to Pub/Sub for worker
            publish_document_message(
                document_id=document.id,
                gcs_path=gcs_path
            )

            uploaded_docs.append({
                "document_id": document.id,
                "file_name": document.file_name,
                "status": "queued"
            })

        except Exception as e:
            db.rollback()
            uploaded_docs.append({
                "file_name": file.filename,
                "status": "failed",
                "error": str(e)
            })

    return {"uploaded": uploaded_docs}



