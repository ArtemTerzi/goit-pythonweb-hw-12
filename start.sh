#!/usr/bin/env sh
# Container entrypoint used in production (Render).
# 1) apply migrations (creates the DB if missing),
# 2) seed pre-confirmed users (idempotent, non-fatal),
# 3) start the API on the port the platform provides via $PORT.
set -e

poetry run alembic upgrade head
poetry run python seed.py || echo "[start] seeding failed (non-fatal), continuing"
poetry run uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"