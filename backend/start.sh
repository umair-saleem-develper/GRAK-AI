#!/bin/bash
set -e

# Only wait for Docker Compose's `db` container when DATABASE_URL targets `@db:`
if [[ "${DATABASE_URL:-}" == *"@db:"* ]]; then
  echo "Docker Postgres detected in DATABASE_URL; checking readiness (max 10s)..."
  for i in $(seq 1 10); do
    if pg_isready -h db -U "${POSTGRES_USER:-admin}" >/dev/null 2>&1; then
      echo "PostgreSQL is up - executing migrations"
      alembic upgrade head || echo "Warning: alembic upgrade failed, continuing startup..."
      break
    fi
    sleep 1
  done
elif [[ "${DATABASE_URL:-}" == postgres* ]]; then
  echo "External PostgreSQL configured - running migrations (non-blocking)..."
  alembic upgrade head || echo "Warning: alembic upgrade skipped/failed, continuing startup..."
else
  echo "No Postgres DATABASE_URL configured - skipping pg_isready and alembic (using SQLite fallback)."
fi

echo "Starting FastAPI server on port ${PORT:-8000}"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
