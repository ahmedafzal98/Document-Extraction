#!/bin/bash

# Start Cloud SQL Auth Proxy in the background
/cloud_sql_proxy -instances=elliptical-feat-476423-q8:us-central1:documet-extraction=tcp:5432 &

# Wait a few seconds to ensure proxy is ready
sleep 2

# Start FastAPI with Gunicorn + Uvicorn
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8080
