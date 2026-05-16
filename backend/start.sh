#!/bin/bash
set -e

echo "Running database migrations..."
cd backend
alembic upgrade head

echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2}
