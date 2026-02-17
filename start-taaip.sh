#!/bin/bash

# TAAIP Startup Script
# Starts both backend and frontend servers with PM2 for persistent operation

echo "🚀 Starting TAAIP Application..."

# Navigate to TAAIP directory
cd /Users/ambermooney/Desktop/TAAIP

# Stop any existing PM2 processes
echo "🛑 Stopping existing processes..."
pm2 delete all 2>/dev/null || true

# Kill any processes on ports 8000 and 5173
echo "🧹 Cleaning up ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

sleep 2

# Start servers with PM2
echo "▶️  Starting servers with PM2..."
pm2 start ecosystem.config.cjs

# Wait for servers to initialize
echo "⏳ Waiting for servers to start..."
sleep 5

# Check server status
echo ""
echo "📊 Server Status:"
pm2 list

echo ""
echo "🌐 Testing servers..."

# Test backend
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend API running on http://localhost:8000"
    echo "   📖 API Docs: http://localhost:8000/docs"
else
    echo "❌ Backend API not responding"
fi

# Test frontend
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend running on http://localhost:5173"
else
    echo "❌ Frontend not responding"
fi

echo ""
echo "🎯 TAAIP is ready!"
echo ""
echo "📋 Available Dashboards:"
echo "   • Market & Segment Dashboard"
echo "   • Recruiting Funnel"
echo "   • Data Input Center"
echo "   • Analytics & Insights"
echo "   • Project Management"
echo "   • Market Potential"
echo "   • Mission Analysis"
echo "   • DOD Branch Comparison"
echo "   • Targeting Decision Board (TWG)"
echo "   • Lead Status Report"
echo ""
echo "🔧 Useful Commands:"
echo "   pm2 status          - View server status"
echo "   pm2 logs            - View server logs"
echo "   pm2 restart all     - Restart both servers"
echo "   pm2 stop all        - Stop all servers"
echo "   pm2 delete all      - Remove all servers from PM2"
echo ""
echo "🌐 Open http://localhost:5173 in your browser to access TAAIP"
