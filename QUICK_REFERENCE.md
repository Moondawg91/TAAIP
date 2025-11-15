# TAAIP Quick Reference Card

## 🚀 Quick Start (Copy & Paste)

```bash
# Start service
cd /Users/ambermooney/Desktop/TAAIP
pip install -r requirements.txt
python taaip_service.py

# In another terminal, test it
python test_taaip_api.py
```

---

## 🔗 Core API Calls (curl)

### Event Management
```bash
# Create event
curl -X POST http://localhost:8000/api/v2/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Job Fair 2025",
    "type": "In-Person-Meeting",
    "location": "Fort Jackson, SC",
    "budget": 50000,
    "team_size": 12
  }'

# Record metrics
curl -X POST http://localhost:8000/api/v2/events/evt_ID/metrics \
  -d '{
    "date": "2025-02-15",
    "leads_generated": 150,
    "conversion_count": 12,
    "roi": 1.45
  }'

# Get ROI
curl http://localhost:8000/api/v2/events/evt_ID/metrics
```

### Recruiting Funnel
```bash
# List funnel stages
curl http://localhost:8000/api/v2/funnel/stages

# Move lead through funnel
curl -X POST http://localhost:8000/api/v2/funnel/transition \
  -d '{
    "lead_id": "lead_001",
    "from_stage": "lead",
    "to_stage": "qualified",
    "transition_reason": "ASVAB passed"
  }'

# Get funnel metrics
curl http://localhost:8000/api/v2/funnel/metrics
```

### Projects & Tasks
```bash
# Create project
curl -X POST http://localhost:8000/api/v2/projects \
  -d '{
    "name": "Event Planning",
    "event_id": "evt_ID",
    "start_date": "2025-01-15",
    "target_date": "2025-02-15"
  }'

# Add task
curl -X POST http://localhost:8000/api/v2/projects/prj_ID/tasks \
  -d '{
    "title": "Finalize messaging",
    "assigned_to": "marketing_team",
    "due_date": "2025-02-01",
    "priority": "high"
  }'
```

### Targeting Profiles (D3AE/F3A)
```bash
# Create profile
curl -X POST http://localhost:8000/api/v2/targeting-profiles \
  -d '{
    "event_id": "evt_ID",
    "target_age_min": 18,
    "target_age_max": 28,
    "target_locations": "37980,41884",
    "message_themes": "career_growth,education",
    "contact_frequency": 3
  }'
```

### Forecasting
```bash
# Generate forecast
curl -X POST http://localhost:8000/api/v2/forecasts/generate \
  -d '{"quarter": 2, "year": 2025}'

# Get forecast
curl http://localhost:8000/api/v2/forecasts/2/2025

# Get dashboard
curl http://localhost:8000/api/v2/analytics/dashboard
```

### M-IPOE Documentation
```bash
# Create intent
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{
    "event_id": "evt_ID",
    "phase": "intent",
    "content": {
      "strategic_objective": "Increase officer recruitment",
      "target_demographic": "HS grads 18-28"
    }
  }'

# Create evaluate
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{
    "event_id": "evt_ID",
    "phase": "evaluate",
    "content": {
      "achievements": ["150 leads", "1.45x ROI"],
      "lessons_learned": ["D3AE targeting effective"]
    }
  }'
```

---

## 🐍 Python Client

```python
import requests

class TAAIPClient:
    def __init__(self, base_url="http://localhost:8000/api/v2", token=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def post(self, endpoint, data):
        return requests.post(f"{self.base_url}{endpoint}", 
                           json=data, headers=self.headers).json()
    
    def get(self, endpoint):
        return requests.get(f"{self.base_url}{endpoint}", 
                          headers=self.headers).json()

# Usage
client = TAAIPClient()

# Create event
result = client.post("/events", {
    "name": "Job Fair",
    "type": "In-Person-Meeting",
    "location": "Fort Jackson, SC",
    "budget": 50000,
    "team_size": 12
})
event_id = result["event_id"]

# Record metrics
client.post(f"/events/{event_id}/metrics", {
    "leads_generated": 150,
    "conversion_count": 12,
    "roi": 1.45
})

# Get dashboard
dashboard = client.get("/analytics/dashboard")
print(dashboard)
```

---

## 📊 Response Formats

### Event Response
```json
{
  "status": "ok",
  "event_id": "evt_a1b2c3d4e5f6"
}
```

### Metrics Response
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "metrics": [
    {
      "date": "2025-02-15",
      "leads_generated": 150,
      "conversion_count": 12,
      "roi": 1.45
    }
  ]
}
```

### Funnel Response
```json
{
  "stages": [
    {"stage_id": "lead", "stage_name": "Lead", "sequence_order": 1},
    {"stage_id": "qualified", "stage_name": "Qualified", "sequence_order": 2},
    ...
  ]
}
```

### Dashboard Response
```json
{
  "dashboard": {
    "total_events": 4,
    "total_leads": 650,
    "total_conversions": 52,
    "conversion_rate": 0.08,
    "avg_cost_per_lead": 384.62,
    "avg_roi": 1.38
  }
}
```

---

## 🔑 Funnel Stages

| Order | Stage | Description |
|-------|-------|-------------|
| 1 | lead | Unqualified prospect |
| 2 | qualified | Passed initial screening |
| 3 | engaged | Active communication |
| 4 | interested | Expressed interest |
| 5 | applicant | Submitted application |
| 6 | interview | Completed interview |
| 7 | offer | Received offer |
| 8 | contract | Signed contract |

---

## 📋 M-IPOE Phases

| Phase | Purpose |
|-------|---------|
| **Intent** | Strategic objective & commander's vision |
| **Plan** | Detailed event design & resources |
| **Order** | Task assignment & preparation |
| **Execute** | Event execution & real-time adjustments |
| **Evaluate** | Post-event analysis & lessons learned |

---

## 🎯 D3AE/F3A Targeting

**D3AE (Demographics, Dialect, Attitude, Education)**:
- Demographics: Age, gender, location
- Dialect: Language, communication style
- Attitude: Values, priorities, motivation
- Education: HS, college, military background

**F3A (Frequency, Forums, Format)**:
- Frequency: How often to contact (3-5x recommended)
- Forums: Channels (social, in-person, email, etc.)
- Format: Messaging style and content themes

---

## 🔑 Environment Variables

```bash
# Database
export TAAIP_DB_PATH=data/taaip.sqlite3

# Authentication (optional)
export TAAIP_API_TOKEN=secret_token_12345

# Logging
export TAAIP_LOG_LEVEL=INFO
export TAAIP_DEBUG=0
```

---

## 🧪 Test Commands

```bash
# Full test suite
python test_taaip_api.py

# Health check
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/api/v1/metrics

# List events
curl http://localhost:8000/api/v2/events
```

---

## 📁 File Structure

```
TAAIP/
├── taaip_service.py              # Main FastAPI backend
├── api-gateway.js                # Express API gateway
├── requirements.txt              # Python dependencies
├── test_taaip_api.py            # Test suite
├── data/
│   ├── taaip.sqlite3            # Database (auto-created)
│   └── model.joblib             # Optional ML model
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── README_COMPREHENSIVE.md       # Full documentation
├── API_REFERENCE_V2.md          # API reference
├── INTEGRATION_GUIDE.md          # Code examples
├── DEPLOYMENT_GUIDE.md          # Deployment instructions
├── EXTENDED_ARCHITECTURE.md     # System design
└── docker-compose.yml           # Docker Compose
```

---

## 🚨 Common Errors & Fixes

| Error | Solution |
|-------|----------|
| `Port 8000 in use` | `lsof -i :8000 && kill -9 <PID>` |
| `ModuleNotFoundError: fastapi` | `pip install -r requirements.txt` |
| `Database locked` | Use PostgreSQL for production |
| `401 Unauthorized` | Check `TAAIP_API_TOKEN` env var |
| `event_id not found` | Create event first with POST /events |

---

## 📞 Quick Support Links

| Topic | Link |
|-------|------|
| **Full Docs** | [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md) |
| **API Reference** | [API_REFERENCE_V2.md](API_REFERENCE_V2.md) |
| **Code Examples** | [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) |
| **Deployment** | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| **Architecture** | [EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md) |

---

## 🎓 Example: One Event Lifecycle

```bash
# 1. CREATE EVENT
curl -X POST http://localhost:8000/api/v2/events \
  -d '{"name":"Fort Jackson Fair","type":"In-Person-Meeting","location":"SC","budget":50000,"team_size":12}'
# Returns: evt_abc123

# 2. CREATE TARGETING
curl -X POST http://localhost:8000/api/v2/targeting-profiles \
  -d '{"event_id":"evt_abc123","target_age_min":18,"target_age_max":28}'

# 3. DOCUMENT INTENT
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{"event_id":"evt_abc123","phase":"intent","content":{"strategic_objective":"..."}}'

# 4. EXECUTE: RECORD METRICS
curl -X POST http://localhost:8000/api/v2/events/evt_abc123/metrics \
  -d '{"leads_generated":150,"conversion_count":12,"roi":1.45}'

# 5. TRACK: MOVE LEADS
curl -X POST http://localhost:8000/api/v2/funnel/transition \
  -d '{"lead_id":"lead_001","from_stage":"lead","to_stage":"qualified"}'

# 6. EVALUATE
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{"event_id":"evt_abc123","phase":"evaluate","content":{"achievements":[...]}}'

# 7. FORECAST
curl -X POST http://localhost:8000/api/v2/forecasts/generate \
  -d '{"quarter":2,"year":2025}'

# 8. VIEW RESULTS
curl http://localhost:8000/api/v2/analytics/dashboard
```

---

## 📈 Performance Tips

- ✅ Use PostgreSQL for >10K events/leads
- ✅ Enable Redis caching for dashboard queries
- ✅ Batch event metrics updates
- ✅ Use indexes on frequently queried fields
- ✅ Deploy with Docker for consistency

---

**Last Updated**: January 2025  
**Version**: 2.0.0
