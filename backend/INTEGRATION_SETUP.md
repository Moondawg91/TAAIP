# Army System Integration Setup Guide

## Overview
TAAIP is now connected to 6 Army data systems:
1. **iKrome** - Recruiting leads, enlistments, mission tracking
2. **EMM Portal** - Event management and performance
3. **Vantage** - Market analytics and performance metrics
4. **BIZone** - Business intelligence and reporting
5. **SharePoint G2** - Reports, SITREPs, weekly/monthly metrics
6. **iKrome Recruiter Zone** - Recruiter-specific updates

## Prerequisites

### 1. CAC Certificate
You need a Common Access Card (CAC) certificate to authenticate with Army systems.

**Obtain your CAC certificate:**
- Your CAC certificate is usually located at: `/Users/ambermooney/.cac/cert.pem`
- Or export from Keychain Access on macOS
- Must be in PEM format

### 2. Python Dependencies
```bash
pip install requests certifi urllib3
```

## Configuration

### Set CAC Certificate Path
Create a `.env` file in `/Users/ambermooney/Desktop/TAAIP/backend/`:

```bash
# Army System Integration
CAC_CERT_PATH=/Users/ambermooney/.cac/cert.pem

# Optional: Custom timeout (default 30 seconds)
REQUEST_TIMEOUT=30

# Optional: Max retries (default 3)
MAX_RETRIES=3
```

Or set as environment variable:
```bash
export CAC_CERT_PATH=/path/to/your/cac/cert.pem
```

## Testing Integration

### 1. Start the Backend
```bash
cd /Users/ambermooney/Desktop/TAAIP/backend
python3 taaip_service.py
```

### 2. Check Integration Status
```bash
curl http://localhost:8000/api/v2/integrations/status
```

**Expected Response:**
```json
{
  "timestamp": "2025-01-23T10:00:00",
  "systems": {
    "ikrome": {"connected": true, "last_check": "2025-01-23T10:00:00"},
    "emm_portal": {"connected": true, "last_check": "2025-01-23T10:00:00"},
    "vantage": {"connected": true, "last_check": "2025-01-23T10:00:00"},
    "bizone": {"connected": true, "last_check": "2025-01-23T10:00:00"},
    "sharepoint": {"connected": true, "last_check": "2025-01-23T10:00:00"}
  },
  "overall_status": "operational"
}
```

### 3. Test Individual Systems
```bash
# Test iKrome
curl http://localhost:8000/api/v2/integrations/test/ikrome

# Test EMM Portal
curl http://localhost:8000/api/v2/integrations/test/emm_portal

# Test Vantage
curl http://localhost:8000/api/v2/integrations/test/vantage

# Test BIZone
curl http://localhost:8000/api/v2/integrations/test/bizone

# Test SharePoint G2
curl http://localhost:8000/api/v2/integrations/test/sharepoint
```

## Available API Endpoints

### Integration Management
- `GET /api/v2/integrations/status` - Check all system connections
- `GET /api/v2/integrations/test/{system}` - Test specific system

### iKrome Data
- `GET /api/v2/integrations/ikrome/enlistments?start_date=2025-01-01&end_date=2025-01-23`
- `GET /api/v2/integrations/ikrome/mission?period=monthly`

### Vantage Analytics
- `GET /api/v2/integrations/vantage/market?region=5th_brigade`

### SharePoint G2 Reports
- `GET /api/v2/integrations/sharepoint/reports?report_type=sitrep&days=7`

### Dashboard Data (Multi-Source)
- `GET /api/v2/integrations/dashboard/overview` - Aggregates all sources
- `GET /api/v2/integrations/dashboard/recruiting` - Recruiting-specific data
- `GET /api/v2/integrations/dashboard/events` - Event-specific data

## Configuration Details

### System Refresh Intervals
Located in `/Users/ambermooney/Desktop/TAAIP/backend/integrations/config.py`:

```python
SYSTEM_CONFIGS = {
    "ikrome": {
        "refresh_interval": 300,  # 5 minutes
        "api_base": "/api/v1",
        "timeout": 30
    },
    "emm_portal": {
        "refresh_interval": 600,  # 10 minutes
        ...
    },
    ...
}
```

Adjust these based on your needs.

### Cache Settings
```python
CACHE_CONFIG = {
    "enabled": True,
    "ttl": 300,  # 5 minutes
    "max_size": 1000
}
```

## Troubleshooting

### Certificate Issues
**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution:**
1. Verify CAC certificate path is correct
2. Ensure certificate is in PEM format
3. Check certificate hasn't expired
4. Try: `export CAC_CERT_PATH=/path/to/cert.pem`

### Connection Timeouts
**Error:** `RequestTimeout`

**Solution:**
1. Increase timeout in config.py
2. Check VPN connection to Army network
3. Verify you're on CAC-enabled network
4. Check firewall rules

### Authentication Failures
**Error:** `401 Unauthorized`

**Solution:**
1. Verify CAC certificate is valid
2. Check if certificate is registered in Army systems
3. Ensure you have access permissions
4. Contact system administrators

### Network Issues
**Error:** `ConnectionError`

**Solution:**
1. Verify VPN connection
2. Check if you're on approved network
3. Ping the system URLs directly
4. Check proxy settings if applicable

## Next Steps

### 1. Update API Endpoints
Once connected, update actual endpoint paths in `config.py`:
```python
API_ENDPOINTS = {
    "ikrome": {
        "enlistments": "/actual/endpoint/path",
        ...
    }
}
```

### 2. Schedule Data Refresh
Create a background task to refresh data periodically:
```python
# In taaip_service.py
from apscheduler.schedulers.background import BackgroundScheduler
from backend.integrations.manager import IntegrationManager

scheduler = BackgroundScheduler()
manager = IntegrationManager()

def refresh_data():
    data = manager.get_dashboard_data('overview')
    # Store in database

scheduler.add_job(refresh_data, 'interval', minutes=5)
scheduler.start()
```

### 3. Add Data Caching
Implement Redis or in-memory caching for better performance.

### 4. Set Up Monitoring
Add logging and alerting for integration failures:
```python
import logging

logging.basicConfig(
    filename='integrations.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Security Notes

⚠️ **IMPORTANT:**
- Never commit CAC certificates to git
- Keep `.env` file in `.gitignore`
- Rotate credentials regularly
- Use least-privilege access
- Monitor for unauthorized access attempts
- Follow Army cybersecurity policies

## Support

For system-specific access issues:
- **iKrome:** Contact USAREC G3
- **EMM Portal:** Contact event management team
- **Vantage:** Contact analytics support
- **BIZone:** Contact BI team
- **SharePoint G2:** Contact G2 Report Zone administrators

## System URLs (For Reference)
- iKrome: https://ikrome.usaas.army.mil
- EMM Portal: https://emm.usaac.army.mil/EMMPortal
- iKrome Recruiter Zone: https://ikrome.ussaac.army.mil/group.recruiterzone
- SharePoint G2: https://army.sharepoint-mil.us/teams/TR-USREC-G2-ReportZone/SitePages/G2-Report-Zone-Main.aspx
- Vantage: https://vantage.army.mil
- BIZone: https://bizone-prod.usarec.army.mil
