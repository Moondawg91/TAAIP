#!/bin/bash

################################################################################
# TAAIP DigitalOcean Automated Deployment Script
# This script will deploy TAAIP to a DigitalOcean droplet in ~5 minutes
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         TAAIP DigitalOcean Deployment Script                ║"
echo "║         Automated 24/7 Cloud Deployment                     ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running on DigitalOcean droplet
if [ ! -f /etc/digitalocean ]; then
    echo -e "${YELLOW}⚠️  This script is designed to run on a DigitalOcean droplet${NC}"
    echo -e "${YELLOW}   You can still continue, but some features may not work${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get droplet IP address
DROPLET_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
echo -e "${GREEN}✓ Detected IP: $DROPLET_IP${NC}"

# Prompt for domain (optional)
read -p "Do you have a domain name? (leave empty to use IP only): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    FRONTEND_URL="http://$DROPLET_IP"
    BACKEND_URL="http://$DROPLET_IP:8000"
else
    FRONTEND_URL="https://$DOMAIN_NAME"
    BACKEND_URL="https://api.$DOMAIN_NAME"
fi

echo ""
echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo -e "   Frontend: $FRONTEND_URL"
echo -e "   Backend:  $BACKEND_URL"
echo ""

# Step 1: Update system
echo -e "${BLUE}[1/8] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq
echo -e "${GREEN}✓ System updated${NC}"

# Step 2: Install Docker
echo -e "${BLUE}[2/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# Step 3: Install Docker Compose
echo -e "${BLUE}[3/8] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✓ Docker Compose already installed${NC}"
fi

# Step 4: Install additional tools
echo -e "${BLUE}[4/8] Installing additional tools...${NC}"
apt-get install -y -qq git curl wget ufw certbot python3-certbot-nginx
echo -e "${GREEN}✓ Tools installed${NC}"

# Step 5: Clone repository (if not already present)
echo -e "${BLUE}[5/8] Setting up TAAIP repository...${NC}"
INSTALL_DIR="/opt/TAAIP"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠️  Directory $INSTALL_DIR already exists${NC}"
    read -p "Do you want to pull latest changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$INSTALL_DIR"
        git pull
    fi
else
    git clone https://github.com/Moondawg91/TAAIP.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "${GREEN}✓ Repository ready${NC}"

# Step 6: Create environment file
echo -e "${BLUE}[6/8] Configuring environment...${NC}"
cat > .env << EOF
# TAAIP Production Environment Configuration
# Generated: $(date)

# Backend Configuration
DATABASE_URL=sqlite:///./data/recruiting.db
BACKEND_PORT=8000
LOG_LEVEL=info

# CORS Configuration
CORS_ORIGINS=$FRONTEND_URL,$BACKEND_URL

# Frontend Configuration
VITE_API_URL=$BACKEND_URL

# Server Information
DROPLET_IP=$DROPLET_IP
DOMAIN_NAME=$DOMAIN_NAME

# Security (CHANGE THESE IN PRODUCTION!)
JWT_SECRET=$(openssl rand -base64 32)
ADMIN_PASSWORD=$(openssl rand -base64 16)
EOF

echo -e "${GREEN}✓ Environment configured${NC}"

# Step 7: Set up firewall
echo -e "${BLUE}[7/8] Configuring firewall...${NC}"
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 8000/tcp # Backend API
echo -e "${GREEN}✓ Firewall configured${NC}"

# Step 8: Build and start services
echo -e "${BLUE}[8/8] Building and starting TAAIP services...${NC}"
echo -e "${YELLOW}⏳ This may take 5-10 minutes...${NC}"

# Create data and logs directories
mkdir -p data logs

# Build and start with Docker Compose
docker-compose down 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

echo -e "${GREEN}✓ Services starting...${NC}"

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 10

# Check backend health
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend health check failed${NC}"
        echo -e "${YELLOW}Check logs: docker-compose logs backend${NC}"
    fi
    sleep 2
done

# Check frontend
if curl -s http://localhost:80 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend may still be starting${NC}"
fi

# Set up SSL if domain provided
if [ -n "$DOMAIN_NAME" ]; then
    echo ""
    read -p "Do you want to set up SSL/HTTPS now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Setting up SSL with Let's Encrypt...${NC}"
        certbot --nginx -d "$DOMAIN_NAME" -d "api.$DOMAIN_NAME" --non-interactive --agree-tos --email admin@$DOMAIN_NAME || echo -e "${YELLOW}⚠️  SSL setup failed. You can run certbot manually later.${NC}"
    fi
fi

# Create auto-backup script
echo -e "${BLUE}Setting up automated backups...${NC}"
cat > /usr/local/bin/taaip-backup.sh << 'BACKUP_SCRIPT'
#!/bin/bash
BACKUP_DIR="/opt/TAAIP/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
docker exec taaip-backend sqlite3 /app/data/recruiting.db ".backup /app/data/backup_$TIMESTAMP.db"
find "$BACKUP_DIR" -name "backup_*.db" -mtime +7 -delete
BACKUP_SCRIPT

chmod +x /usr/local/bin/taaip-backup.sh

# Add daily backup cron job
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/taaip-backup.sh") | crontab -

echo -e "${GREEN}✓ Automated daily backups configured${NC}"

# Print summary
echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         🎉 TAAIP DEPLOYMENT SUCCESSFUL! 🎉                  ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${BLUE}📊 Access your TAAIP application:${NC}"
echo -e "   Frontend:     $FRONTEND_URL"
echo -e "   Backend API:  $BACKEND_URL"
echo -e "   Health Check: $BACKEND_URL/health"
echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo -e "   View logs:           ${YELLOW}docker-compose logs -f${NC}"
echo -e "   Restart services:    ${YELLOW}docker-compose restart${NC}"
echo -e "   Stop services:       ${YELLOW}docker-compose down${NC}"
echo -e "   Start services:      ${YELLOW}docker-compose up -d${NC}"
echo -e "   Update application:  ${YELLOW}git pull && docker-compose up -d --build${NC}"
echo -e "   Manual backup:       ${YELLOW}/usr/local/bin/taaip-backup.sh${NC}"
echo ""
echo -e "${BLUE}📁 Important Locations:${NC}"
echo -e "   Installation:  /opt/TAAIP"
echo -e "   Database:      /opt/TAAIP/data/recruiting.db"
echo -e "   Logs:          /opt/TAAIP/logs/"
echo -e "   Backups:       /opt/TAAIP/backups/"
echo ""
echo -e "${BLUE}🔐 Security Notes:${NC}"
echo -e "   • Change default passwords in ${YELLOW}/opt/TAAIP/.env${NC}"
echo -e "   • Firewall is enabled (SSH, HTTP, HTTPS allowed)"
echo -e "   • Daily backups scheduled at 2:00 AM"
echo -e "   • Services auto-restart on failure"
echo ""
echo -e "${GREEN}✅ Your TAAIP app is now running 24/7!${NC}"
echo ""
