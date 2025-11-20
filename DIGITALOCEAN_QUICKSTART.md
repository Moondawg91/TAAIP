# 🚀 TAAIP DigitalOcean Quick Deployment (5 Minutes)

Get TAAIP running 24/7 in the cloud in just 5 minutes!

---

## Step 1: Create DigitalOcean Account (2 minutes)

1. Go to https://digitalocean.com
2. Sign up (get $200 free credit with this link: https://m.do.co/c/taaip)
3. Add payment method (credit card)

---

## Step 2: Create Droplet (1 minute)

1. Click **"Create"** → **"Droplets"**
2. Choose:
   - **Image**: Docker on Ubuntu 22.04
   - **Plan**: Basic - $8/month (1GB RAM, 1 vCPU) or $16/month (2GB RAM, 2 vCPU - Recommended)
   - **Region**: New York 3 (or closest to you)
   - **Authentication**: Password (create strong password)
   - **Hostname**: `taaip-production`
3. Click **"Create Droplet"** (takes 30 seconds)

---

## Step 3: Run Automated Deployment (2 minutes)

1. **Copy your Droplet IP** from DigitalOcean dashboard

2. **SSH into your droplet:**
```bash
ssh root@YOUR_DROPLET_IP
# Enter the password you created
```

3. **Run the automated deployment script:**
```bash
curl -fsSL https://raw.githubusercontent.com/Moondawg91/TAAIP/feat/optimize-app/deploy-digitalocean.sh | bash
```

That's it! The script will:
- ✅ Install Docker and dependencies
- ✅ Clone your TAAIP repository
- ✅ Configure environment
- ✅ Set up firewall
- ✅ Build and start services
- ✅ Configure auto-restart
- ✅ Set up daily backups

---

## Step 4: Access Your App

Once deployment completes (2-5 minutes), access your app:

**Frontend**: `http://YOUR_DROPLET_IP`  
**Backend**: `http://YOUR_DROPLET_IP:8000`

---

## Optional: Add Custom Domain

### A. Point Domain to Droplet

1. In DigitalOcean: **Networking** → **Domains** → **Add Domain**
2. Enter your domain (e.g., `taaip.army`)
3. Create DNS records:
   - **A record**: `@` → `YOUR_DROPLET_IP`
   - **A record**: `api` → `YOUR_DROPLET_IP`

### B. Enable HTTPS/SSL

SSH into your droplet and run:
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d taaip.army -d api.taaip.army
```

Now accessible at: `https://taaip.army` 🔒

---

## Management Commands

All commands run from droplet (`ssh root@YOUR_DROPLET_IP`):

### View Status
```bash
cd /opt/TAAIP
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f          # All services
docker-compose logs -f backend  # Backend only
docker-compose logs -f frontend # Frontend only
```

### Restart Services
```bash
docker-compose restart
```

### Update TAAIP
```bash
cd /opt/TAAIP
git pull
docker-compose up -d --build
```

### Manual Backup
```bash
/usr/local/bin/taaip-backup.sh
```

### Check Health
```bash
curl http://localhost:8000/health
```

---

## Monitoring & Alerts

### Set Up DigitalOcean Monitoring (Free)

1. In DigitalOcean dashboard: **Droplets** → Your droplet → **Monitoring**
2. Enable alerts for:
   - CPU usage > 80%
   - Memory usage > 90%
   - Disk usage > 80%

### Check Service Status
```bash
docker ps  # Should show 2 running containers
```

---

## Troubleshooting

### Services won't start
```bash
cd /opt/TAAIP
docker-compose logs
```

### Port not accessible
```bash
# Check firewall
ufw status
# Open port if needed
ufw allow 8000/tcp
```

### Out of memory
```bash
# Upgrade droplet to $24/month (4GB RAM)
# In DigitalOcean: Droplet → Resize
```

### Update not working
```bash
cd /opt/TAAIP
docker-compose down
docker system prune -a
git pull
docker-compose up -d --build
```

---

## Cost Breakdown

| Item | Cost |
|------|------|
| Basic Droplet (1GB RAM) | $8/month |
| Recommended Droplet (2GB RAM) | $16/month |
| Domain name (optional) | $12/year |
| **Total** | **$8-17/month** |

### Upgrade Options
- **4GB RAM** ($24/month) - Recommended for 100+ users
- **8GB RAM** ($32/month) - For brigade-level deployment
- **Managed PostgreSQL** (+$15/month) - For production database

---

## Next Steps After Deployment

1. ✅ **Test the app** - Open `http://YOUR_DROPLET_IP` in browser
2. ✅ **Change default passwords** - Edit `/opt/TAAIP/.env`
3. ✅ **Share with battalion** - Give them the URL
4. ✅ **Monitor usage** - Check DigitalOcean dashboard
5. ✅ **Collect feedback** - Plan improvements
6. ✅ **Start Azure Gov process** - For production Army deployment

---

## Security Checklist

- [x] Firewall enabled (SSH, HTTP, HTTPS only)
- [x] Services auto-restart on failure
- [x] Daily automated backups
- [ ] Change admin password in `.env`
- [ ] Change JWT secret in `.env`
- [ ] Set up SSH key authentication (disable password)
- [ ] Enable SSL/HTTPS with Let's Encrypt
- [ ] Configure DigitalOcean monitoring alerts

---

## Support

- **Deployment Issues**: Check `/opt/TAAIP/logs/`
- **Docker Issues**: Run `docker-compose logs`
- **DigitalOcean Help**: https://docs.digitalocean.com
- **TAAIP GitHub**: https://github.com/Moondawg91/TAAIP/issues

---

## ⚠️ Important Reminders

- This is **NOT Army-compliant** (no CAC, not FedRAMP)
- Use for **pilot testing only** (30-90 days)
- For production Army use, see `DEPLOYMENT_AZURE_GOV.md`
- Services run **24/7** - your Mac is not needed
- Auto-restarts on crashes/reboots
- Daily backups at 2:00 AM

---

**Your TAAIP app is now running continuously in the cloud!** 🎉

Access it anytime at: `http://YOUR_DROPLET_IP`
