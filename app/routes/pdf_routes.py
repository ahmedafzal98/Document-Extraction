# app/routes/pdf_routes.py
from fastapi import APIRouter, HTTPException
from app.models.pdf_models import PDFProcessRequest, PDFProcessResponse
from pdf_processing import process_pdf
from dotenv import load_dotenv
import os


load_dotenv()

router = APIRouter()

# Environment variables for Document AI
PROJECT_ID = os.getenv("PROJECT_ID", "267816589183")
LOCATION = os.getenv("LOCATION", "us")
PROCESSOR_ID = os.getenv("PROCESSOR_ID", "3bd2a3a3becdadcb")

@router.post("/process_pdf", response_model=PDFProcessResponse)
def process_single_pdf(request: PDFProcessRequest):
    all_results = []
    for pdf_path in request.pdf_paths:
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail=f"{pdf_path} not found")
        result = process_pdf(pdf_path, request.dataset_file, PROJECT_ID, LOCATION, PROCESSOR_ID)
        all_results.extend(result)
    return PDFProcessResponse(results=all_results)
