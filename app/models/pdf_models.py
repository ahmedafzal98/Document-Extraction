# app/models/pdf_models.py
from typing import List
from pydantic import BaseModel

class PDFProcessRequest(BaseModel):
    pdf_paths: List[str]
    dataset_file: str

class PDFProcessResponse(BaseModel):
    results: list
