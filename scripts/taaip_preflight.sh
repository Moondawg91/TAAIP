#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.env" ]]; then
  set -a
  source "$PROJECT_ROOT/.env"
  set +a
fi

export TAAIP_DB_PATH="${TAAIP_DB_PATH:-$PROJECT_ROOT/data/taaip.sqlite3}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$TAAIP_DB_PATH}"
export TAAIP_UPLOAD_DIR="${TAAIP_UPLOAD_DIR:-$PROJECT_ROOT/services/api/.data/imports}"
export TAAIP_REFRESH_UPLOAD_DIR="${TAAIP_REFRESH_UPLOAD_DIR:-$PROJECT_ROOT/data/refresh_uploads}"
export EXPORT_STORAGE_DIR="${EXPORT_STORAGE_DIR:-$PROJECT_ROOT/data/exports}"
export TAAIP_DOCUMENTS_PATH="${TAAIP_DOCUMENTS_PATH:-$PROJECT_ROOT/data/documents}"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8000}"

mkdir -p "$(dirname "$TAAIP_DB_PATH")" "$TAAIP_UPLOAD_DIR" "$TAAIP_REFRESH_UPLOAD_DIR" "$EXPORT_STORAGE_DIR" "$TAAIP_DOCUMENTS_PATH" "$PROJECT_ROOT/logs"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

"$PYTHON_BIN" "$PROJECT_ROOT/services/api/scripts/runtime_preflight.py" --ensure-schema
