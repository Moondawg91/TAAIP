#!/bin/bash

################################################################################
# TAAIP Droplet Deployment Script
# Run this from your local machine to deploy updates to your droplet
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Droplet configuration
DROPLET_IP="129.212.185.3"
DROPLET_USER="root"
APP_DIR="/root/TAAIP"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         TAAIP Droplet Deployment Script                     ║"
echo "║         Deploying to: ${DROPLET_IP}                    ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if we can reach the droplet
echo -e "${YELLOW}→ Testing connection to droplet...${NC}"
if ! ssh -o ConnectTimeout=5 ${DROPLET_USER}@${DROPLET_IP} "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${RED}✗ Cannot connect to droplet at ${DROPLET_IP}${NC}"
    echo -e "${YELLOW}  Please ensure:${NC}"
    echo -e "  1. Your droplet is running"
    echo -e "  2. You have SSH access configured"
    echo -e "  3. Your SSH key is added to the droplet"
    echo ""
    echo -e "${YELLOW}  To test manually: ssh ${DROPLET_USER}@${DROPLET_IP}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connected to droplet${NC}"

# Deploy the application
echo -e "${YELLOW}→ Deploying application to droplet...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} << 'ENDSSH'
set -e

echo "→ Navigating to app directory..."
cd /root/TAAIP

echo "→ Checking current branch..."
git branch

echo "→ Fetching latest changes..."
git fetch origin

echo "→ Pulling latest code from feat/optimize-app..."
git pull origin feat/optimize-app

echo "→ Installing dependencies..."
cd taaip-dashboard
npm install

echo "→ Building production bundle..."
npm run build

echo "→ Checking if Docker is running..."
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "→ Restarting Docker containers..."
    cd /root/TAAIP
    docker-compose down
    docker-compose up -d
    echo "✓ Docker containers restarted"
else
    echo "⚠ Docker not detected - skipping container restart"
    echo "  You may need to manually restart your web server"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "✓ Deployment Complete!"
echo "═══════════════════════════════════════════════════"

ENDSSH

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         ✓ Deployment Successful!                            ║"
echo "║                                                              ║"
echo "║         Your app is live at:                                ║"
echo "║         http://${DROPLET_IP}                         ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
