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

echo "→ Ensuring we are on the deployment branch..."
# fetch remote and force-reset local working tree to match remote branch
git fetch origin
if git show-ref --verify --quiet refs/heads/feat/optimize-app; then
    git checkout feat/optimize-app || true
else
    git checkout -b feat/optimize-app origin/feat/optimize-app || true
fi

echo "→ Resetting local tree to origin/feat/optimize-app (will overwrite local changes)"
git reset --hard origin/feat/optimize-app

echo "→ Installing dependencies..."
cd taaip-dashboard
npm install

echo "→ Building production bundle..."
npm run build

echo "→ Checking if Docker is running..."
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "→ Restarting Docker containers..."
    cd /root/TAAIP || true
    # Validate docker-compose config first; if invalid, skip restart instead of failing the deploy
    if docker-compose config &> /dev/null; then
        if docker-compose down && docker-compose up -d; then
            echo "✓ Docker containers restarted"
        else
            echo "⚠ Docker restart failed (non-fatal). Please investigate on the droplet."
        fi
    else
        echo "⚠ docker-compose config invalid — skipping docker-compose restart"
        echo "  You may need to fix /root/TAAIP/docker-compose.yml on the droplet and restart manually."
    fi
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
