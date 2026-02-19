#!/bin/bash
# Deploy backend fixes to droplet

echo "=== Deploying Backend API Fixes ==="
echo ""

# Pull latest changes
echo "Step 1: Pulling latest changes from GitHub..."
git pull origin feat/optimize-app

# Rebuild backend container
echo ""
echo "Step 2: Rebuilding backend container..."
docker-compose build backend

# Restart backend service
echo ""
echo "Step 3: Restarting backend service..."
docker-compose up -d backend

# Wait for backend to start
echo ""
echo "Waiting 5 seconds for backend to start..."
sleep 5

# Test the fixed endpoints
echo ""
echo "=== Testing Fixed Endpoints ==="
echo ""

echo "1. Testing recruiting-funnel/metrics:"
curl -s http://localhost:3000/api/v2/recruiting-funnel/metrics | jq '.status' 2>/dev/null || echo "  Error or no jq installed"

echo ""
echo "2. Testing analytics/overview:"
curl -s http://localhost:3000/api/v2/analytics/overview | jq '.status' 2>/dev/null || echo "  Error or no jq installed"

echo ""
echo "3. Testing market/potential:"
curl -s http://localhost:3000/api/v2/market/potential | jq '.status' 2>/dev/null || echo "  Error or no jq installed"

echo ""
echo "4. Testing targeting/recommendations:"
curl -s http://localhost:3000/api/v2/targeting/recommendations | jq '.status' 2>/dev/null || echo "  Error or no jq installed"

echo ""
echo "=== Deployment Complete ==="
echo "All endpoints should now be working. Check the application at http://129.212.185.3"
