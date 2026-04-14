#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Starting the TAAIP operational stack..."
zsh "$PROJECT_ROOT/scripts/taaip_preflight.sh"

if ! command -v pm2 >/dev/null 2>&1; then
  echo "❌ PM2 is not installed. Use ./start-taaip-local.sh for the local process launcher."
  exit 1
fi

echo "🧹 Cleaning up the runtime ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

pm2 delete taaip-backend taaip-frontend 2>/dev/null || true
pm2 start ecosystem.config.cjs --update-env

pm2 list

echo "✅ TAAIP startup submitted to PM2"
echo "   Backend: http://127.0.0.1:8000/docs"
echo "   Frontend: http://127.0.0.1:5173"

