#!/usr/bin/env bash
set -euo pipefail

echo "Running TAAIP verify_app.sh"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="http://127.0.0.1:8000"

echo "Initializing DB schema (init_db)"
python - <<PY
from services.api.app.db import init_db
print('init_db ->', init_db())
PY

echo "Checking health endpoint"
curl -sS ${API_URL}/health | jq || true

echo "Running system self-check"
curl -sS ${API_URL}/api/system/self-check | jq || true

echo "Verify script completed. Review outputs above."
