#!/bin/bash
set -e

echo "Starting RiskIntel Entrypoint..."

# We don't need a custom configuration validation loop here
# because core.config (pydantic-settings) will fail-fast 
# when uvicorn imports the application if vars are missing.

echo "Running Alembic Migrations..."
alembic upgrade head

echo "Starting FastAPI Application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
