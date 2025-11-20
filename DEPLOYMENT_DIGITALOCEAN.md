# TAAIP Deployment Guide - DigitalOcean

## Quick Pilot Deployment ($5-20/month)

This guide will get TAAIP running on DigitalOcean in ~15 minutes for testing and pilot operations.

### Prerequisites
- DigitalOcean account (https://digitalocean.com)
- Credit card for billing
- Domain name (optional, but recommended)

---

## Step 1: Create a Droplet

1. **Sign up** at https://digitalocean.com
2. **Create Droplet** → Choose:
   - **Image**: Docker on Ubuntu 22.04
   - **Plan**: Basic - $8/month (1GB RAM) or $16/month (2GB RAM - Recommended)
   - **Region**: Choose closest to your users (e.g., New York 3)
   - **Authentication**: SSH Key (generate if needed)
   - **Hostname**: `taaip-production`

3. **Click "Create Droplet"** - takes 1-2 minutes

---

## Step 2: Connect to Your Server

```bash
# Replace YOUR_DROPLET_IP with the IP from DigitalOcean dashboard
ssh root@YOUR_DROPLET_IP
```

---

## Step 3: Clone Your Repository

```bash
# Install git if not present
apt update && apt install -y git

# Clone your TAAIP repo
cd /opt
git clone https://github.com/Moondawg91/TAAIP.git
cd TAAIP
```

---

## Step 4: Configure Environment

```bash
# Create production environment file
cat > .env.production << 'EOF'
# Backend Configuration
DATABASE_URL=sqlite:///./recruiting.db
BACKEND_PORT=8000
CORS_ORIGINS=http://YOUR_DROPLET_IP,https://YOUR_DOMAIN.com

# Frontend Configuration
VITE_API_URL=http://YOUR_DROPLET_IP:8000

# Security (generate random strings)
JWT_SECRET=CHANGE_THIS_TO_RANDOM_STRING
ADMIN_PASSWORD=CHANGE_THIS_PASSWORD
EOF

# Replace YOUR_DROPLET_IP with actual IP
sed -i "s/YOUR_DROPLET_IP/$(curl -s ifconfig.me)/g" .env.production
```

---

## Step 5: Build with Docker

```bash
# Build backend
docker build -f Dockerfile.backend -t taaip-backend .

# Build frontend (production)
cd taaip-dashboard
docker build -t taaip-frontend --build-arg VITE_API_URL=http://$(curl -s ifconfig.me):8000 .
cd ..
```

---

## Step 6: Start Services

```bash
# Create Docker network
docker network create taaip-network

# Start backend
docker run -d \
  --name taaip-backend \
  --network taaip-network \
  -p 8000:8000 \
  -v /opt/TAAIP/recruiting.db:/app/recruiting.db \
  --restart unless-stopped \
  taaip-backend

# Start frontend
docker run -d \
  --name taaip-frontend \
  --network taaip-network \
  -p 80:80 \
  --restart unless-stopped \
  taaip-frontend
```

---

## Step 7: Configure Firewall

```bash
# Allow HTTP, HTTPS, and SSH
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw enable
```

---

## Step 8: Access Your Application

```bash
# Get your droplet IP
curl ifconfig.me
```

**Your TAAIP app is now live at:**
- Frontend: `http://YOUR_DROPLET_IP`
- Backend API: `http://YOUR_DROPLET_IP:8000`

---

## Step 9: Add Domain Name (Optional)

1. **In DigitalOcean:**
   - Networking → Domains → Add Domain
   - Create A record: `@` → `YOUR_DROPLET_IP`
   - Create A record: `api` → `YOUR_DROPLET_IP`

2. **Update your domain registrar:**
   - Point nameservers to DigitalOcean:
     - ns1.digitalocean.com
     - ns2.digitalocean.com
     - ns3.digitalocean.com

3. **Enable HTTPS (Let's Encrypt):**

```bash
# Install Nginx and Certbot
apt install -y nginx certbot python3-certbot-nginx

# Configure Nginx
cat > /etc/nginx/sites-available/taaip << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN.com;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/taaip /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Get SSL certificate
certbot --nginx -d YOUR_DOMAIN.com
```

**Now accessible at:** `https://YOUR_DOMAIN.com`

---

## Monitoring & Maintenance

### Check Service Status
```bash
docker ps
docker logs taaip-backend
docker logs taaip-frontend
```

### Restart Services
```bash
docker restart taaip-backend
docker restart taaip-frontend
```

### Update Application
```bash
cd /opt/TAAIP
git pull
docker-compose down
docker-compose up -d --build
```

### Backup Database
```bash
# Backup
docker exec taaip-backend sqlite3 /app/recruiting.db ".backup /app/backup.db"
docker cp taaip-backend:/app/backup.db ./backup-$(date +%Y%m%d).db

# Restore
docker cp ./backup-20251119.db taaip-backend:/app/recruiting.db
docker restart taaip-backend
```

---

## Cost Breakdown

| Resource | Cost/Month |
|----------|------------|
| Basic Droplet (1GB RAM) | $8 |
| Recommended (2GB RAM) | $16 |
| Domain Name (optional) | $12/year |
| Backups (optional) | $2.40 |
| **Total** | **~$10-18/month** |

---

## Scaling Options

### Upgrade Droplet Size
- **4GB RAM**: $24/month (recommended for 100+ users)
- **8GB RAM**: $48/month (recommended for 500+ users)

### Add Database Server
```bash
# Create managed PostgreSQL database
# $15/month for 1GB RAM

# Update backend .env
DATABASE_URL=postgresql://user:pass@db-host:25060/taaip
```

---

## Limitations

⚠️ **This deployment is NOT suitable for official Army use because:**
- Not FedRAMP/ATO compliant
- No CAC authentication
- No Azure Gov hosting
- Basic security (good for pilot, not production)

✅ **Perfect for:**
- Testing with your battalion
- Demonstrating to leadership
- Pilot program (30-90 days)
- Feature validation

---

## Troubleshooting

### Backend won't start
```bash
docker logs taaip-backend
# Check for Python errors or missing dependencies
```

### Frontend shows API errors
```bash
# Check CORS settings in .env.production
# Verify backend is running: curl http://localhost:8000/health
```

### Can't connect from outside
```bash
# Check firewall
ufw status
# Verify services are listening
netstat -tlnp | grep -E "80|8000"
```

---

## Next Steps

1. **Test with your unit** (1-2 weeks)
2. **Collect feedback** 
3. **Start Azure Gov approval process** for production
4. **Migrate to Azure Gov** (see DEPLOYMENT_AZURE_GOV.md)

---

## Support

- DigitalOcean Docs: https://docs.digitalocean.com
- TAAIP Issues: https://github.com/Moondawg91/TAAIP/issues
- Contact your G6 for Army production deployment
