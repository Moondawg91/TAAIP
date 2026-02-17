#!/bin/bash

# TAAIP Local Stop Script
# Gracefully stops both backend and frontend servers

TAAIP_DIR="/Users/ambermooney/Desktop/TAAIP"
LOG_DIR="$TAAIP_DIR/logs"

echo "🛑 Stopping TAAIP Local Services..."

# Try to read PIDs from file first
if [ -f "$LOG_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOG_DIR/backend.pid")
    kill $BACKEND_PID 2>/dev/null && echo "Stopped backend (PID: $BACKEND_PID)"
    rm "$LOG_DIR/backend.pid"
fi

if [ -f "$LOG_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid")
    kill $FRONTEND_PID 2>/dev/null && echo "Stopped frontend (PID: $FRONTEND_PID)"
    rm "$LOG_DIR/frontend.pid"
fi

# Fallback: kill by process name
pkill -f "taaip_service.py" 2>/dev/null
pkill -f "vite.*taaip-dashboard" 2>/dev/null

# Force kill if needed
sleep 2
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5174 | xargs kill -9 2>/dev/null

echo "✅ All TAAIP services stopped"
