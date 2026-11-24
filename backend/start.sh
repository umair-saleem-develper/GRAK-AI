#!/bin/bash
set -e

echo "Waiting for postgres..."
# Wait for postgres to be ready
while ! pg_isready -h db -U ${POSTGRES_USER:-admin}; do
  sleep 1
done

echo "PostgreSQL is up - executing migrations"
alembic upgrade head

echo "Starting FastAPI server"
exec uvicorn main:app --host 0.0.0.0 --port 8000
