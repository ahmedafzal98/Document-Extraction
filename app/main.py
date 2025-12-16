# main.py
from fastapi import FastAPI
from app.routes import pdf_routes, upload_routes
from app.routes.extract_router import router as extract_router
from app.routes.dataset_routes import router as dataset_router

app = FastAPI(title="PDF Processing API")

# PDF routes
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["PDF Processing"])

# Upload routes
app.include_router(upload_routes.router, prefix="/api", tags=["File Upload"])
app.include_router(extract_router, prefix="/api")
app.include_router(dataset_router, prefix="/api")
