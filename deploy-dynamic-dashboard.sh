#!/bin/bash

# Dynamic Dashboard Deployment Script
# Run this on your DigitalOcean droplet to deploy the Smart Visualizations feature

echo "=========================================="
echo "Dynamic Dashboard Deployment"
echo "=========================================="
echo ""

# Navigate to TAAIP directory
cd /opt/TAAIP || exit 1

echo "📥 Pulling latest code from GitHub..."
git pull origin feat/optimize-app

echo ""
echo "🛑 Stopping containers..."
/usr/bin/docker-compose down

echo ""
echo "🔨 Rebuilding containers with new features..."
echo "   (This may take 2-3 minutes)"
/usr/bin/docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "✅ Checking container status..."
/usr/bin/docker-compose ps

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "🎉 Smart Visualizations feature is now live!"
echo ""
echo "Access it at:"
echo "  http://129.212.185.3"
echo "  → Click menu dropdown"
echo "  → Select 'Smart Visualizations' under Operations"
echo ""
echo "Features included:"
echo "  ✅ KPI Cards - Key metrics at a glance"
echo "  ✅ Bar Charts - Category breakdowns"
echo "  ✅ Pie Charts - Distribution analysis"
echo "  ✅ Timeline Charts - Temporal trends"
echo "  ✅ Status Boards - Progress indicators"
echo "  ✅ Location Rankings - Geographic insights"
echo "  ✅ Heatmaps - Pattern analysis"
echo "  ✅ Data Tables - Raw data browser"
echo ""
echo "📖 Documentation: /opt/TAAIP/DYNAMIC_DASHBOARD_GUIDE.md"
echo ""
