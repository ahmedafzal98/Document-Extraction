from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
from app.db import get_db
from app.models.tables import DatasetRecord

router = APIRouter(tags=["Dataset"])

def ensure_date(value):
    """Convert value to datetime.date or return None"""
    if pd.isna(value) or value in ("", "N/A"):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except:
            continue
    return None

@router.post("/upload_dataset")
def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload dataset CSV/XLSX and store in DB
    """
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        elif file.filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Use CSV or XLSX.")

        records_added = 0
        for _, row in df.iterrows():
            dataset_name = row.get("Dataset_Name")
            dataset_doa = ensure_date(row.get("Dataset_DOA"))
            dataset_dob = ensure_date(row.get("Dataset_DOB"))
            dataset_referral = row.get("Dataset_Referral")

            if dataset_name:  # Skip empty rows
                record = DatasetRecord(
                    dataset_name=dataset_name,
                    dataset_doa=dataset_doa,
                    dataset_dob=dataset_dob,
                    dataset_referral=dataset_referral
                )
                db.add(record)
                records_added += 1

        db.commit()
        return {"status": "success", "records_added": records_added}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
