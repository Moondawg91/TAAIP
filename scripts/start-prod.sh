#!/bin/bash
# Minimal startup script for running TAAIP on the droplet.
# Usage: copy /opt/TAAIP/deploy/.env.prod.example -> /opt/TAAIP/.env and edit values
# Then run as the app user: `bash scripts/start-prod.sh` or use systemd unit.

set -euo pipefail
cd /opt/TAAIP
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
elif [ -f ".env.prod" ]; then
  export $(grep -v '^#' .env.prod | xargs)
fi

# Ensure data directories exist
mkdir -p "${EXPORT_STORAGE_DIR:-/opt/TAAIP/data/exports}"
mkdir -p "${UPLOADS_DIR:-/opt/TAAIP/data/uploads}"
mkdir -p "${TAAIP_DB_PATH%/*}"

# Start uvicorn in background (for simple droplet usage). Prefer systemd in production.
echo "Starting TAAIP (uvicorn) on ${HOST:-127.0.0.1}:${PORT:-8001}"
nohup uvicorn services.api.app.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8001} --workers ${WORKERS:-2} > /var/log/taaip_uvicorn.log 2>&1 &

sleep 1
ps aux | grep uvicorn | grep -v grep || true

echo "Started. Check /var/log/taaip_uvicorn.log for logs."
