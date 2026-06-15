#!/usr/bin/env sh
# Container entrypoint used in production (Render).
# Runs database migrations, then starts the API on the port the platform
# provides via $PORT (falling back to 8000 for local use).
set -e

poetry run alembic upgrade head
poetry run uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"