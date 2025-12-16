from sqlalchemy import text
from fastapi import APIRouter, HTTPException
from app.db import SessionLocal

router = APIRouter()

@router.get("/extract_fields")
def get_extract_fields(limit: int = 100):
    """Fetch records from extracted_fields table"""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM extracted_fields LIMIT :limit"), {"limit": limit}).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/matches")
def get_matches(limit: int = 100):
    """Fetch records from matches table"""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM matches LIMIT :limit"), {"limit": limit}).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
