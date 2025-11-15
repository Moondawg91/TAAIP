# TAAIP Getting Started Guide

**Welcome to TAAIP!** This guide gets you up and running in 5-30 minutes depending on your use case.

---

## ⚡ 5-Minute Quick Start

### 1. Verify Prerequisites
```bash
python --version        # Should be 3.8+
pip --version          # Should be present
```

### 2. Install & Start
```bash
cd /Users/ambermooney/Desktop/TAAIP
pip install -r requirements.txt
python taaip_service.py
```

### 3. Verify It's Running
```bash
# In another terminal
curl http://localhost:8000/health

# Response:
# {"status": "ok", "service": "TAAIP Targeting & AI Service", ...}
```

### 4. Test the API
```bash
python test_taaip_api.py
# Output: Tests Passed: 18/18 ✓
```

**That's it! You're running TAAIP.** ✅

---

## 📖 Next Steps by Role

### 👨‍💻 Developer: Build an Integration

**Goal**: Create a Python app that uses TAAIP API

1. **Read**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
2. **Copy Python client** example:
   ```python
   from integration_examples import TAAIPClient
   client = TAAIPClient()
   event = client.create_event(...)
   ```
3. **Run examples** from the integration guide
4. **Build your feature** using the same patterns

### 🎯 Project Manager: Track Events & ROI

**Goal**: Monitor recruiting events and ROI in real-time

1. **Start the service**: `python taaip_service.py`
2. **Bookmark**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
3. **Use curl commands** to:
   - Create events
   - Record metrics
   - View dashboard
   - Track funnel progress
4. **Example workflow**:
   ```bash
   # Create event
   curl -X POST http://localhost:8000/api/v2/events \
     -d '{"name":"Job Fair","location":"Fort Jackson","budget":50000}'
   
   # Record metrics (during event)
   curl -X POST http://localhost:8000/api/v2/events/evt_ID/metrics \
     -d '{"leads_generated":150,"roi":1.45}'
   
   # View results
   curl http://localhost:8000/api/v2/analytics/dashboard
   ```

### 🏗️ DevOps: Deploy to Production

**Goal**: Deploy TAAIP to AWS/GCP/Azure/K8s

1. **Read**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. **Follow the steps**:
   - Set up PostgreSQL database
   - Configure HTTPS/TLS
   - Setup monitoring
   - Deploy with Docker/K8s
3. **Test deployment** with `python test_taaip_api.py`

### 🎓 Architect: Understand the System

**Goal**: Learn the full architecture and design

1. **Read**: [EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md)
2. **Understand the 6 domains**:
   - ROI & Event Tracking
   - Recruiting Funnel
   - Project Management
   - M-IPOE Analysis
   - D3AE/F3A Targeting
   - Predictive Forecasting
3. **Review data model** with 13 tables
4. **Study API endpoints** in [API_REFERENCE_V2.md](API_REFERENCE_V2.md)

### 🎖️ Military Commander: Apply M-IPOE Framework

**Goal**: Use TAAIP for military decision-making

1. **Read**: [WHITEPAPER.md](WHITEPAPER.md) — strategic vision
2. **Understand M-IPOE phases**:
   - Document **Intent** (strategic objective)
   - Define **Plan** (event design)
   - Issue **Order** (task assignment)
   - Execute **Execute** (live event)
   - Document **Evaluate** (lessons learned)
3. **Use API**:
   ```bash
   # Document intent
   curl -X POST http://localhost:8000/api/v2/mipoe \
     -d '{"event_id":"evt_ID","phase":"intent","content":{...}}'
   ```
4. **Apply D3AE/F3A targeting** principles
5. **Review quarterly forecasts** for planning

---

## 📚 Complete Documentation

### Quick References
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — One-page cheat sheet (5 min)
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** — Navigation guide (5 min)

### Comprehensive Guides
- **[README_COMPREHENSIVE.md](README_COMPREHENSIVE.md)** — Full overview (15 min)
- **[API_REFERENCE_V2.md](API_REFERENCE_V2.md)** — All endpoints (30 min)
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** — Code examples (20 min)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** — Production setup (40 min)

### Design Documents
- **[EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md)** — System design (25 min)
- **[WHITEPAPER.md](WHITEPAPER.md)** — Strategic vision (25 min)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Original architecture (15 min)

---

## 🚀 Common Tasks

### Task 1: Create & Track a Recruiting Event

```bash
# 1. Create event
EVENT=$(curl -X POST http://localhost:8000/api/v2/events \
  -d '{
    "name":"Spring Job Fair 2025",
    "type":"In-Person-Meeting",
    "location":"Fort Jackson, SC",
    "budget":50000,
    "team_size":12
  }')

EVENT_ID=$(echo $EVENT | grep -o '"event_id":"[^"]*"' | cut -d'"' -f4)
echo "Created event: $EVENT_ID"

# 2. Create targeting profile (who to recruit)
curl -X POST http://localhost:8000/api/v2/targeting-profiles \
  -d '{
    "event_id":"'$EVENT_ID'",
    "target_age_min":18,
    "target_age_max":28,
    "target_education_level":"High School, Some College",
    "target_locations":"37980,41884",
    "message_themes":"career_growth,technology",
    "contact_frequency":3
  }'

# 3. Record metrics during event
curl -X POST http://localhost:8000/api/v2/events/$EVENT_ID/metrics \
  -d '{
    "date":"2025-02-15",
    "leads_generated":150,
    "leads_qualified":95,
    "conversion_count":12,
    "roi":1.45
  }'

# 4. Track lead progression
curl -X POST http://localhost:8000/api/v2/funnel/transition \
  -d '{
    "lead_id":"lead_001",
    "from_stage":"lead",
    "to_stage":"qualified"
  }'

# 5. View results
curl http://localhost:8000/api/v2/events/$EVENT_ID/metrics
curl http://localhost:8000/api/v2/analytics/dashboard
```

### Task 2: Plan Event with Project Management

```bash
# 1. Create project
PROJECT=$(curl -X POST http://localhost:8000/api/v2/projects \
  -d '{
    "name":"Spring Fair Planning",
    "event_id":"'$EVENT_ID'",
    "start_date":"2025-01-15",
    "target_date":"2025-02-15"
  }')

PROJECT_ID=$(echo $PROJECT | grep -o '"project_id":"[^"]*"' | cut -d'"' -f4)

# 2. Add tasks
curl -X POST http://localhost:8000/api/v2/projects/$PROJECT_ID/tasks \
  -d '{
    "title":"Finalize messaging",
    "assigned_to":"marketing_team",
    "due_date":"2025-02-01",
    "priority":"high"
  }'

# 3. Get timeline
curl http://localhost:8000/api/v2/projects/$PROJECT_ID/timeline
```

### Task 3: Forecast Next Quarter

```bash
# Generate forecast for Q2
curl -X POST http://localhost:8000/api/v2/forecasts/generate \
  -d '{"quarter":2,"year":2025}'

# Get specific forecast
curl http://localhost:8000/api/v2/forecasts/2/2025

# Expected output:
# {
#   "quarter": 2,
#   "projected_leads": 1400,
#   "projected_conversions": 115,
#   "projected_roi": 1.52,
#   "confidence_level": 0.75
# }
```

### Task 4: Document Military Decision with M-IPOE

```bash
# Document Intent phase
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{
    "event_id":"'$EVENT_ID'",
    "phase":"intent",
    "content":{
      "strategic_objective":"Increase officer acquisition",
      "target_demographic":"HS grads 18-28",
      "commander_intent":"Focus on high-propensity markets"
    }
  }'

# Post-event: Document Evaluate phase
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{
    "event_id":"'$EVENT_ID'",
    "phase":"evaluate",
    "content":{
      "achievements":["150 leads","1.45x ROI"],
      "lessons_learned":["D3AE targeting very effective"],
      "recommendations":["Replicate for Q2"]
    }
  }'
```

---

## 🧪 Verification Checklist

After starting TAAIP, verify everything works:

- [ ] Service starts: `python taaip_service.py` (no errors)
- [ ] Health check: `curl http://localhost:8000/health` (returns ok)
- [ ] Database exists: `ls data/taaip.sqlite3`
- [ ] Tests pass: `python test_taaip_api.py` (18/18 passing)
- [ ] Can create event: `curl -X POST .../api/v2/events` (returns event_id)
- [ ] Can get funnel: `curl .../api/v2/funnel/stages` (returns 8 stages)
- [ ] Dashboard works: `curl .../api/v2/analytics/dashboard` (returns metrics)

---

## 📊 Key URLs

| Resource | URL |
|----------|-----|
| **Backend API** | http://localhost:8000 |
| **Health Check** | http://localhost:8000/health |
| **API Gateway** | http://localhost:3001 (if running) |
| **Frontend** | http://localhost:3000 (if running) |
| **Database** | `data/taaip.sqlite3` |

---

## 🔑 Important Environment Variables

```bash
# Set before running
export TAAIP_DB_PATH=data/taaip.sqlite3
export TAAIP_LOG_LEVEL=INFO

# Optional: Enable authentication
export TAAIP_API_TOKEN=your_secret_token

# Then run
python taaip_service.py
```

---

## 🆘 Troubleshooting

### Service won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check if port 8000 is in use
lsof -i :8000
# If in use: kill -9 <PID>
```

### Test fails
```bash
# Make sure service is running
curl http://localhost:8000/health

# Check database was created
ls data/taaip.sqlite3

# Check logs
python taaip_service.py  # Look for errors
```

### Curl commands not working
```bash
# Make sure you're using correct event_id
curl http://localhost:8000/api/v2/events  # List events first

# If authentication enabled, include token
curl -H "Authorization: Bearer $TAAIP_API_TOKEN" \
  http://localhost:8000/api/v2/events
```

---

## 📈 What You Can Do Right Now

✅ **Immediately**:
- Start the service
- Run tests
- Call API endpoints
- Create events and track metrics
- View dashboard

✅ **Today** (with a bit more work):
- Build Python integration
- Create complete event workflow
- Generate forecasts
- Document M-IPOE phases
- Apply D3AE/F3A targeting

✅ **This Week**:
- Deploy with Docker
- Setup production database (PostgreSQL)
- Enable authentication
- Configure monitoring
- Build custom dashboard

---

## 🎯 Recommended Next Steps

### For Quick Wins (Next 1 Hour)
1. ✅ Start service
2. ✅ Run test suite
3. ✅ Create your first event
4. ✅ Record metrics
5. ✅ View dashboard

### For Integration (Next 1 Day)
1. ✅ Read [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
2. ✅ Build Python client
3. ✅ Create complete workflow
4. ✅ Test all endpoints

### For Production (Next 1 Week)
1. ✅ Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. ✅ Setup PostgreSQL
3. ✅ Configure HTTPS
4. ✅ Enable monitoring
5. ✅ Deploy to infrastructure

---

## 💡 Pro Tips

- **Bookmark** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command reference
- **Use** Python client for building integrations (see examples)
- **Test** with `python test_taaip_api.py` regularly
- **Monitor** logs: `python taaip_service.py 2>&1 | tee debug.log`
- **Backup** database: `cp data/taaip.sqlite3 data/taaip.backup.sqlite3`

---

## 📞 Need Help?

1. **Quick answers**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. **API questions**: [API_REFERENCE_V2.md](API_REFERENCE_V2.md)
3. **Code examples**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
4. **Deployment help**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
5. **System design**: [EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md)
6. **Strategic vision**: [WHITEPAPER.md](WHITEPAPER.md)

---

**You're all set! Start with `python taaip_service.py` and explore.** 🚀

For detailed information, see [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md).
