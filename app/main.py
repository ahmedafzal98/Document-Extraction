# main.py
from fastapi import FastAPI
from app.routes import pdf_routes, upload_routes
from app.routes.extract_router import router as extract_router
from app.routes.dataset_routes import router as dataset_router
import uvicorn
import os

app = FastAPI(title="PDF Processing API")

# PDF routes
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["PDF Processing"])

# Upload routes
app.include_router(upload_routes.router, prefix="/api", tags=["File Upload"])
app.include_router(extract_router, prefix="/api")
app.include_router(dataset_router, prefix="/api")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Use Cloud Run's PORT or default 8080 locally
    uvicorn.run("main:app", host="0.0.0.0", port=port)