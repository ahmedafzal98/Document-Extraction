# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install system dependencies needed for some Python packages and wget for Cloud SQL Proxy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    wget \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc wget \
    && apt-get clean

# Copy project files
COPY . .

# Download Cloud SQL Auth Proxy
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /cloud_sql_proxy \
    && chmod +x /cloud_sql_proxy

# Expose the port Render expects
EXPOSE 8080

# Start Cloud SQL Proxy in background and then run FastAPI with Gunicorn + Uvicorn
CMD ["/bin/bash", "-c", "/cloud_sql_proxy -instances=elliptical-feat-476423-q8:us-central1:documet-extraction=tcp:5432 & gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8080"]
