#!/usr/bin/env bash
set -euo pipefail

# Apply any pending database migrations before starting the app.
# Safe to run on every boot: Alembic skips migrations already recorded
# in the alembic_version table.
echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting API..."
exec "$@"
