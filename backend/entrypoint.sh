#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding bootstrap admin..."
python -m app.scripts.bootstrap

echo "Starting backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
