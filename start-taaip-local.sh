#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/scripts/taaip_preflight.sh"

echo "🚀 Starting TAAIP local services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
nohup "$PYTHON_BIN" -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

cd "$PROJECT_ROOT/taaip-dashboard"
nohup npm run dev -- --host 127.0.0.1 --port 5173 > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

cd "$PROJECT_ROOT"
echo $BACKEND_PID > "$LOG_DIR/backend.pid"
echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"

echo "✅ TAAIP local stack started"
echo "   Backend:  http://127.0.0.1:8000/docs"
echo "   Frontend: http://127.0.0.1:5173"
echo "   Logs:     $LOG_DIR"

