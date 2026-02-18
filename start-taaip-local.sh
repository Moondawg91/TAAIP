#!/bin/bash

# TAAIP Local Auto-Start Script
# This script starts both backend and frontend servers automatically

TAAIP_DIR="/Users/ambermooney/Desktop/TAAIP"
LOG_DIR="$TAAIP_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "🚀 Starting TAAIP Local Services..."

# Kill any existing processes
echo "Stopping existing services..."
pkill -f "taaip_service.py" 2>/dev/null
pkill -f "vite.*taaip-dashboard" 2>/dev/null
sleep 2

# Start Backend (Python FastAPI)
echo "Starting Backend on port 8000..."
cd "$TAAIP_DIR"
nohup python3 taaip_service.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to initialize
sleep 3

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️ Backend may still be starting..."
fi

# Start Frontend (React + Vite)
echo "Starting Frontend on port 5174..."
cd "$TAAIP_DIR/taaip-dashboard"
nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Wait for frontend to initialize
sleep 5

# Save PIDs for easy management
echo $BACKEND_PID > "$LOG_DIR/backend.pid"
echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"

echo ""
echo "✅ TAAIP Services Started Successfully!"
echo ""
echo "📊 Access your application:"
echo "   Frontend: http://localhost:5174"
echo "   Backend:  http://localhost:8000"
echo ""
echo "📝 Logs located at:"
echo "   Backend:  $LOG_DIR/backend.log"
echo "   Frontend: $LOG_DIR/frontend.log"
echo ""
echo "🛑 To stop services, run: ./stop-taaip-local.sh"
echo ""
