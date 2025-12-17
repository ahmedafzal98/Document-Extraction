# app/routes/match_routes.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db import SessionLocal
from concurrent.futures import ThreadPoolExecutor
import logging
logger = logging.getLogger(__name__)

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=5)  # Adjust based on your load

def fetch_from_db(query, params=None):
    db = SessionLocal()
    try:
        result = db.execute(text(query), params or {}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

@router.get("/extract_fields")
def get_extract_fields(limit: int = 100):
    try:
        future = executor.submit(
            fetch_from_db,
            "SELECT * FROM extracted_fields LIMIT :limit",
            {"limit": limit}
        )
        return future.result(timeout=10)  # wait max 10 sec
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches")
def get_matches(limit: int = 100):
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM matches LIMIT :limit"), {"limit": limit}).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error("DB Error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
