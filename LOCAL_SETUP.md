# TAAIP Local Development - Auto-Start Setup

## Quick Start Scripts

I've created scripts to easily start and stop TAAIP on your Mac:

### Start TAAIP
```bash
cd /Users/ambermooney/Desktop/TAAIP
./start-taaip-local.sh
```

This will:
- Start backend on `http://localhost:8000`
- Start frontend on `http://localhost:5174`
- Save logs to `logs/` directory
- Save process IDs for easy shutdown

### Stop TAAIP
```bash
cd /Users/ambermooney/Desktop/TAAIP
./stop-taaip-local.sh
```

This will gracefully stop both services.

---

## Auto-Start on Mac Boot (Optional)

To have TAAIP start automatically when you turn on your Mac:

### Step 1: Enable Auto-Start

```bash
cd /Users/ambermooney/Desktop/TAAIP

# Copy launch agent to system directory
cp com.taaip.autostart.plist ~/Library/LaunchAgents/

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.taaip.autostart.plist

# Enable it
launchctl enable gui/$(id -u)/com.taaip.autostart
```

### Step 2: Verify It Works

```bash
# Check status
launchctl list | grep taaip

# Test by restarting your Mac
# TAAIP should automatically start after login
```

### Step 3: Disable Auto-Start (if needed)

```bash
# Disable auto-start
launchctl disable gui/$(id -u)/com.taaip.autostart

# Unload the agent
launchctl unload ~/Library/LaunchAgents/com.taaip.autostart.plist

# Remove the file
rm ~/Library/LaunchAgents/com.taaip.autostart.plist
```

---

## Keep Mac Awake (Prevent Sleep)

To keep your Mac running 24/7 without sleeping:

### Option 1: Temporary (Current Session Only)
```bash
# Keep awake while plugged in
caffeinate -d -i -m -s &

# To stop
killall caffeinate
```

### Option 2: Permanent (System Settings)
1. **System Settings** → **Energy Saver** (or **Battery**)
2. **Power Adapter** tab:
   - ✅ Prevent computer from sleeping automatically when display is off
   - Set "Turn display off after" to a reasonable time (10-30 minutes)
3. **Disable Sleep Mode Completely**:
```bash
sudo pmset -a sleep 0
sudo pmset -a disablesleep 1
```

### Option 3: Scheduled Wake (Best for office hours)
```bash
# Wake Mac at 6:00 AM on weekdays
sudo pmset repeat wakeorpoweron MTWRF 06:00:00

# Sleep at 10:00 PM
sudo pmset repeat sleep MTWRFSU 22:00:00
```

---

## Monitoring

### Check if TAAIP is Running
```bash
# Check processes
ps aux | grep -E "taaip_service|vite"

# Check ports
lsof -i :8000  # Backend
lsof -i :5174  # Frontend

# Check health
curl http://localhost:8000/health
```

### View Logs
```bash
# Backend logs
tail -f /Users/ambermooney/Desktop/TAAIP/logs/backend.log

# Frontend logs
tail -f /Users/ambermooney/Desktop/TAAIP/logs/frontend.log

# Auto-start logs
tail -f /Users/ambermooney/Desktop/TAAIP/logs/launchd.log
```

### Restart Services
```bash
cd /Users/ambermooney/Desktop/TAAIP
./stop-taaip-local.sh && sleep 2 && ./start-taaip-local.sh
```

---

## Remote Access (Local Network Only)

To access TAAIP from other computers on your network:

### Step 1: Find Your Mac's IP Address
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example output: inet 192.168.1.100
```

### Step 2: Update Frontend Configuration
```bash
cd /Users/ambermooney/Desktop/TAAIP/taaip-dashboard

# Edit vite.config.ts to allow network access
cat >> vite.config.ts << 'EOF'
export default {
  server: {
    host: '0.0.0.0',  // Listen on all network interfaces
    port: 5174,
    strictPort: true
  }
}
EOF
```

### Step 3: Update Backend CORS
```bash
cd /Users/ambermooney/Desktop/TAAIP

# Edit taaip_service.py - find CORS settings and add your network
# Look for: allowed_origins = [...]
# Add: "http://192.168.1.*", "http://10.0.0.*"
```

### Step 4: Allow Firewall Access (macOS)
```bash
# Allow incoming connections
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/python3

# Or disable firewall for local network (easier but less secure)
# System Settings → Network → Firewall → Turn Off
```

### Step 5: Access from Other Computers
```
Frontend: http://YOUR_MAC_IP:5174
Backend:  http://YOUR_MAC_IP:8000
```

---

## Backup Configuration

### Automatic Daily Backups
```bash
# Create backup script
cat > /Users/ambermooney/Desktop/TAAIP/backup-taaip.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/Users/ambermooney/Desktop/TAAIP/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
cp /Users/ambermooney/Desktop/TAAIP/recruiting.db "$BACKUP_DIR/recruiting_$DATE.db"

# Keep only last 7 days
find "$BACKUP_DIR" -name "recruiting_*.db" -mtime +7 -delete

echo "Backup completed: recruiting_$DATE.db"
EOF

chmod +x /Users/ambermooney/Desktop/TAAIP/backup-taaip.sh

# Schedule daily backup at 2 AM
cat > ~/Library/LaunchAgents/com.taaip.backup.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.taaip.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/ambermooney/Desktop/TAAIP/backup-taaip.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.taaip.backup.plist
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check for port conflicts
lsof -i :8000
lsof -i :5174

# Kill conflicting processes
lsof -ti:8000 | xargs kill -9
lsof -ti:5174 | xargs kill -9

# Try starting again
./start-taaip-local.sh
```

### Auto-Start Not Working
```bash
# Check launch agent status
launchctl list | grep taaip

# View launch agent logs
cat /Users/ambermooney/Desktop/TAAIP/logs/launchd.log

# Reload launch agent
launchctl unload ~/Library/LaunchAgents/com.taaip.autostart.plist
launchctl load ~/Library/LaunchAgents/com.taaip.autostart.plist
```

### Database Issues
```bash
# Restore from backup
cp /Users/ambermooney/Desktop/TAAIP/backups/recruiting_20251119_*.db /Users/ambermooney/Desktop/TAAIP/recruiting.db

# Restart services
./stop-taaip-local.sh && ./start-taaip-local.sh
```

---

## Performance Optimization

### Increase Node.js Memory
```bash
# Edit start script to add Node options
export NODE_OPTIONS="--max-old-space-size=4096"
```

### Monitor Resource Usage
```bash
# Install htop for better monitoring
brew install htop

# Monitor TAAIP processes
htop -p $(pgrep -f taaip_service),$(pgrep -f vite)
```

---

## Limitations of Local Hosting

⚠️ **Local Mac hosting is NOT suitable for:**
- ❌ Official Army operations (no ATO/RMF compliance)
- ❌ Multi-battalion deployment (limited to your network)
- ❌ CAC authentication (requires Azure AD)
- ❌ High availability (Mac restart = downtime)
- ❌ Disaster recovery (no redundancy)

✅ **Local Mac hosting IS good for:**
- ✅ Development and testing
- ✅ Single battalion pilot (small team)
- ✅ Demonstrations to leadership
- ✅ Feature validation before cloud deployment

---

## Next Steps

1. **✅ Test locally** - Use for development (you're here)
2. **📦 Deploy to DigitalOcean** - 15-minute pilot deployment (~$15/month)
3. **🏛️ Deploy to Azure Gov** - Production Army deployment (3-6 months, ~$300/month)

See:
- `DEPLOYMENT_DIGITALOCEAN.md` - Quick pilot deployment guide
- `DEPLOYMENT_AZURE_GOV.md` - Production DoD deployment guide
