#!/bin/bash
set -e

# Start Cloud SQL Proxy in background
/cloud_sql_proxy \
  -instances=elliptical-feat-476423-q8:us-central1:documet-extraction=tcp:5432 \
  -credential_file=$GOOGLE_APPLICATION_CREDENTIALS &

# Wait for proxy to start
echo "Waiting for Cloud SQL Proxy..."
while ! nc -z 127.0.0.1 5432; do
  sleep 1
done

echo "Cloud SQL Proxy ready. Starting FastAPI..."
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8080
