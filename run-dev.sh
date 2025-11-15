#!/bin/bash

# TAAIP Dev Stack Launcher
# Starts FastAPI backend, Node.js API Gateway, and optionally the frontend dev server

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "========================================="
echo "TAAIP Development Stack Launcher"
echo "========================================="

# Kill any existing processes on ports 8000, 3000 when script exits
trap cleanup EXIT
cleanup() {
  echo "Cleaning up..."
  kill $(lsof -t -i:8000) 2>/dev/null || true
  kill $(lsof -t -i:3000) 2>/dev/null || true
}

# Step 1: Start FastAPI backend
echo ""
echo "Step 1: Starting FastAPI backend (port 8000)..."
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

.venv/bin/python -m uvicorn taaip_service:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 2

# Step 2: Start Node.js API Gateway
echo ""
echo "Step 2: Starting Node.js API Gateway (port 3000)..."
if [ ! -d "node_modules" ]; then
  echo "Installing Node dependencies..."
  npm install -q
fi
node api-gateway.js > api-gateway.log 2>&1 &
GATEWAY_PID=$!
echo "API Gateway PID: $GATEWAY_PID"
sleep 1

# Step 3 (Optional): Start frontend dev server
echo ""
echo "Step 3: Starting frontend dev server (port 5173)..."
echo "Note: You can skip this and open http://127.0.0.1:3000 directly from your browser"
echo "Press Enter to continue, or Ctrl+C to stop here and use static files..."
read -p "Start Vite dev server? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  cd frontend
  if [ ! -d "node_modules" ]; then
    npm install -q
  fi
  npm run dev > ../frontend.log 2>&1 &
  FRONTEND_PID=$!
  echo "Frontend PID: $FRONTEND_PID"
  cd ..
fi

echo ""
echo "========================================="
echo "✓ Stack ready!"
echo "========================================="
echo "- FastAPI backend:    http://127.0.0.1:8000"
echo "- API Gateway:        http://127.0.0.1:3000"
echo "- Frontend (Vite):    http://127.0.0.1:5173"
echo "- FastAPI docs:       http://127.0.0.1:8000/docs"
echo ""
echo "Logs:"
echo "- Backend:      tail -f backend.log"
echo "- API Gateway:  tail -f api-gateway.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "========================================="

# Keep script running
wait
