# TAAIP Deployment Quick Reference Guide

## 🚀 Three Deployment Options

### **Option 1: Local Mac Auto-Start** ✅ READY NOW
**Purpose**: Development and local team testing  
**Cost**: Free  
**Setup Time**: 5 minutes  

#### Start Services
```bash
cd /Users/ambermooney/Desktop/TAAIP
chmod +x start-taaip-local.sh stop-taaip-local.sh
./start-taaip-local.sh
```

#### Access
- Frontend: http://localhost:5174
- Backend: http://localhost:8000

#### Stop Services
```bash
./stop-taaip-local.sh
```

#### Auto-Start on Mac Boot (Optional)
```bash
# Copy launch agent
cp com.taaip.startup.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.taaip.startup.plist

# Disable auto-start
launchctl unload ~/Library/LaunchAgents/com.taaip.startup.plist
```

---

### **Option 2: DigitalOcean (Pilot/Testing)** 📦 15-30 MIN SETUP
**Purpose**: Remote testing with your unit  
**Cost**: $24/month  
**Setup Time**: 15-30 minutes  
**Guide**: See `DEPLOYMENT_DIGITALOCEAN.md`

#### Quick Deploy
1. Create DigitalOcean account
2. Create Ubuntu 22.04 droplet with Docker
3. SSH to droplet:
```bash
ssh root@YOUR_DROPLET_IP

# Clone and deploy
git clone https://github.com/Moondawg91/TAAIP.git /opt/TAAIP
cd /opt/TAAIP
docker-compose up -d
```
4. Access at http://YOUR_DROPLET_IP

---

### **Option 3: Azure Government (Production Army)** 🛡️ 3-6 MONTHS
**Purpose**: Official Army deployment with RMF/ATO  
**Cost**: $200-500/month  
**Setup Time**: 3-6 months (includes ATO)  
**Guide**: See `DEPLOYMENT_AZURE_GOV.md`

#### Prerequisites
- Azure Gov subscription (contact G6)
- RMF/ATO approval
- CAC/PIV integration setup

#### Deploy
```bash
# Login to Azure Gov
az cloud set --name AzureUSGovernment
az login

# Run deployment script
./deploy-azure-gov.sh
```

---

## 📊 Comparison Matrix

| Feature | Local Mac | DigitalOcean | Azure Gov |
|---------|-----------|--------------|-----------|
| **Accessibility** | Only your Mac | Internet | Internet |
| **Army Compliant** | ❌ No | ❌ No | ✅ Yes |
| **CAC Auth** | ❌ No | ❌ No | ✅ Yes |
| **24/7 Uptime** | ❌ No | ✅ Yes | ✅ Yes |
| **Auto Scaling** | ❌ No | ⚠️ Manual | ✅ Yes |
| **Cost** | Free | $24/mo | $200-500/mo |
| **Setup Time** | 5 min | 30 min | 3-6 months |
| **Use Case** | Dev/Test | Pilot | Production |
| **SSL/HTTPS** | ❌ No | ✅ Yes | ✅ Yes |
| **Backup** | Manual | ✅ Yes | ✅ Yes |
| **Monitoring** | Manual | Basic | Enterprise |

---

## 🎯 Recommended Deployment Path

### **Phase 1: NOW - Local Development** (Week 1)
- ✅ Use your Mac for development
- ✅ Test all features
- ✅ Train yourself and close team members

### **Phase 2: SOON - Pilot Testing** (Weeks 2-4)
- 📦 Deploy to DigitalOcean
- Get feedback from battalion
- Document issues and improvements
- Test with 10-20 users

### **Phase 3: LATER - Army Production** (Months 3-6)
- 🛡️ Start Azure Gov approval process
- Complete RMF/ATO paperwork
- Deploy to Azure Gov
- Roll out to brigade/USAREC

---

## 🆘 Quick Troubleshooting

### Local Mac Issues

**Services won't start:**
```bash
# Check what's using ports
lsof -i :8000
lsof -i :5174

# Kill existing processes
./stop-taaip-local.sh

# Try again
./start-taaip-local.sh
```

**Backend error:**
```bash
# Check logs
tail -f /Users/ambermooney/Desktop/TAAIP/logs/backend.log

# Verify Python dependencies
cd /Users/ambermooney/Desktop/TAAIP
pip3 install -r requirements.txt
```

**Frontend error:**
```bash
# Check logs
tail -f /Users/ambermooney/Desktop/TAAIP/logs/frontend.log

# Reinstall dependencies
cd /Users/ambermooney/Desktop/TAAIP/taaip-dashboard
npm install
```

### DigitalOcean Issues

**Can't access droplet:**
```bash
# Check if services are running
ssh root@YOUR_DROPLET_IP "docker ps"

# View logs
ssh root@YOUR_DROPLET_IP "docker-compose logs"
```

**Update code:**
```bash
ssh root@YOUR_DROPLET_IP
cd /opt/TAAIP
git pull
docker-compose up -d --build
```

### Azure Gov Issues

**Contact your G6 or see DEPLOYMENT_AZURE_GOV.md**

---

## 📞 Support

### Technical Issues
- GitHub Issues: https://github.com/Moondawg91/TAAIP/issues
- Local logs: `/Users/ambermooney/Desktop/TAAIP/logs/`

### Deployment Help
- DigitalOcean Docs: https://docs.digitalocean.com
- Azure Gov Docs: https://docs.microsoft.com/azure/azure-government/

### Army-Specific
- Contact your G6/IM office
- ISSO for RMF/ATO questions
- Identity Management for CAC/PIV

---

## Quick import-check (CI-friendly)

You can validate the backend imports (useful in CI) with:

```bash
# run in the project root virtualenv
python -c "from services.api.app.main import app; print('api import ok')"
```


## ✅ Current Status

Your TAAIP installation is ready for:
- ✅ **Local testing** on your Mac
- ✅ **DigitalOcean deployment** (follow guide)
- ✅ **Azure Gov preparation** (start paperwork)

### Next Action Items

1. **Today**: Test locally with `./start-taaip-local.sh`
2. **This Week**: Deploy to DigitalOcean for team testing
3. **This Month**: Contact G6 about Azure Gov access
4. **Next Month**: Start RMF/ATO documentation

---

## 📁 Key Files

```
TAAIP/
├── start-taaip-local.sh          # Start local servers
├── stop-taaip-local.sh           # Stop local servers
├── com.taaip.startup.plist       # Mac auto-start config
├── DEPLOYMENT_DIGITALOCEAN.md    # DigitalOcean guide
├── DEPLOYMENT_AZURE_GOV.md       # Azure Gov guide
├── docker-compose.yml            # Docker configuration
├── Dockerfile.backend            # Backend container
└── Dockerfile.gateway            # Frontend container
```

---

**Ready to start?** Run: `./start-taaip-local.sh`
