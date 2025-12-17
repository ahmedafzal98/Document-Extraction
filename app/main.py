from fastapi import FastAPI
from app.routes import pdf_routes, upload_routes
from app.routes.extract_router import router as extract_router
from app.routes.dataset_routes import router as dataset_router
import uvicorn
import os

app = FastAPI(title="PDF Processing API")

# Root route for Cloud Run Health Checks (Crucial!)
@app.get("/")
async def root():
    return {"message": "API is active"}

# Include your routers
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["PDF Processing"])
app.include_router(upload_routes.router, prefix="/api", tags=["File Upload"])
app.include_router(extract_router, prefix="/api")
app.include_router(dataset_router, prefix="/api")

# This block is only for LOCAL testing. 
# Cloud Run will ignore this if started via command line.
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)