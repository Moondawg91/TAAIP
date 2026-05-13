#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Source preflight so exported env vars (e.g., DATABASE_URL) persist
# for the backend/frontend processes launched below.
source "$PROJECT_ROOT/scripts/taaip_preflight.sh"

cleanup() {
  kill $(lsof -t -i:8000) 2>/dev/null || true
  kill $(lsof -t -i:5173) 2>/dev/null || true
}
trap cleanup EXIT

echo "========================================="
echo "TAAIP commander workflow dev stack"
echo "========================================="

"$PROJECT_ROOT/.venv/bin/python" -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

cd "$PROJECT_ROOT/taaip-dashboard"
npm run dev -- --host 127.0.0.1 --port 5173 > "$PROJECT_ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

echo "Frontend PID: $FRONTEND_PID"
echo "Backend docs:  http://127.0.0.1:8000/docs"
echo "Frontend:      http://127.0.0.1:5173"

wait

