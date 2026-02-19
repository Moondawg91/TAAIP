#!/bin/bash

# HomeScreen Layout Update Deployment Script
# Deploys sidebar layout and expandable leaderboard to production

set -e  # Exit on error

echo "========================================="
echo "TAAIP HomeScreen Layout Update Deployment"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on droplet
if [ ! -d "/opt/TAAIP" ]; then
    echo -e "${RED}Error: /opt/TAAIP directory not found${NC}"
    echo "This script should be run on the DigitalOcean droplet"
    exit 1
fi

cd /opt/TAAIP

echo -e "${YELLOW}Step 1: Fetching latest code from GitHub...${NC}"
git fetch origin feat/optimize-app
git checkout feat/optimize-app
git pull origin feat/optimize-app

echo ""
echo -e "${YELLOW}Step 2: Checking Docker status...${NC}"
docker-compose ps

echo ""
echo -e "${YELLOW}Step 3: Rebuilding frontend container...${NC}"
docker-compose build frontend

echo ""
echo -e "${YELLOW}Step 4: Restarting services...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}Step 5: Waiting for services to start...${NC}"
sleep 5

echo ""
echo -e "${YELLOW}Step 6: Checking container health...${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "HomeScreen layout updated with:"
echo "  ✓ Vertical sidebar with Resources/Dashboards/Help Desk panels"
echo "  ✓ Expandable top 10 leaderboard with 'Show More/Less' button"
echo "  ✓ Improved dropdown mutual exclusion"
echo ""
echo "Access the application at: http://129.212.185.3"
echo ""
echo "To view frontend logs:"
echo "  docker-compose logs -f frontend"
echo ""
echo "To view backend logs:"
echo "  docker-compose logs -f backend"
echo ""
