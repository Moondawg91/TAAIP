# TAAIP 2.0 Complete Setup & Run Guide

## 🎯 Overview
TAAIP 2.0 is a multifunctional recruiting intelligence platform built on USAREC market segmentation, fusion team structure, and AI predictive capabilities. It integrates:
- **React Dashboard** (frontend, charts, real-time KPIs)
- **FastAPI Backend** (recruiting funnel, marketing tracking, KPI calculation)
- **AI Pipeline** (lead propensity scoring, batch predictions)
- **Minimal LMS** (courses, enrollments, progress tracking)
- **Power BI Integration** (embedded dashboards)

---

## 📋 Prerequisites

### System Requirements
- macOS 12+ / Ubuntu 20+ / Windows 10+
- Node.js 18+ (for React dashboard)
- Python 3.9+
- npm / yarn (Node package manager)
- Homebrew (macOS) or apt/brew equivalent

### Install Dependencies

#### 1. Backend (Python)
```bash
cd /Users/ambermooney/Desktop/TAAIP

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or on Windows: .venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Optional: Install ML dependencies (for real model training)
pip install scikit-learn==1.3.2 pandas==2.1.3
```

#### 2. Frontend (React + Vite)
```bash
cd /Users/ambermooney/Desktop/TAAIP/taaip-dashboard

# Install Node dependencies
npm install

# (Optional) If using yarn
# yarn install
```

---

## 🚀 Running the Full System

### Option A: Run Everything (Recommended for Testing)

#### Terminal 1: Start Backend
```bash
cd /Users/ambermooney/Desktop/TAAIP
source .venv/bin/activate
python -m uvicorn taaip_service:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Terminal 2: Start Frontend
```bash
cd /Users/ambermooney/Desktop/TAAIP/taaip-dashboard
npm run dev
```

Expected output:
```
  VITE v5.0.8  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

#### Access the App
- **Dashboard**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **API (OpenAPI)**: http://localhost:8000/openapi.json

---

### Option B: Production Build

#### Build Frontend
```bash
cd /Users/ambermooney/Desktop/TAAIP/taaip-dashboard
npm run build
```

This generates `dist/` folder with optimized files.

#### Serve with Backend
Backend serves static files at `/` by default if configured:
```bash
# (Optional) Update taaip_service.py to serve static files from dist/
```

---

## 🧪 Testing the System

### 1. Run Unit Tests (Backend)
```bash
cd /Users/ambermooney/Desktop/TAAIP
source .venv/bin/activate
pytest -v
```

Expected output:
```
test_taaip_marketing.py::test_record_marketing_activity PASSED
test_taaip_kpis.py::test_calculate_kpis PASSED
test_taaip_exports_v2.py::test_exports_endpoints_v2 PASSED
...
============ 7 passed in 0.54s ============
```

### 2. Verify API Endpoints

#### Check Funnel Stages
```bash
curl -X GET http://localhost:8000/api/v2/funnel/stages | jq '.'
```

Expected response:
```json
{
  "status": "ok",
  "stages": [
    "lead",
    "prospect",
    "appointment_made",
    "appointment_conducted",
    "test",
    "test_pass",
    "physical",
    "enlist"
  ]
}
```

#### Record a Marketing Activity
```bash
curl -X POST http://localhost:8000/api/v2/marketing/activities \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_001",
    "activity_type": "social_media",
    "campaign_name": "test_campaign",
    "channel": "Instagram",
    "data_source": "emm",
    "impressions": 500,
    "engagement_count": 25,
    "awareness_metric": 0.8,
    "activation_conversions": 3
  }' | jq '.'
```

#### Get KPIs
```bash
curl -X GET http://localhost:8000/api/v2/kpis | jq '.'
```

---

## 🤖 AI Pipeline Setup

### 1. Train Model on Historical Data
```bash
# In Python shell or script:
from taaip_ai_pipeline import train_lead_propensity_model
result = train_lead_propensity_model('data/taaip.sqlite3')
print(result)
# Output: {"status": "trained", "accuracy": 0.87, "samples": 1000}
```

### 2. Get Model Status
```bash
curl -X GET http://localhost:8000/api/v2/ai/model-status | jq '.'
```

### 3. Predict Lead Propensity
```bash
# Add endpoint in taaip_service.py to expose predictions
# Example: POST /api/v2/ai/predict
```

### 4. Scheduled Retraining (Optional)
Add to `taaip_service.py`:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from taaip_ai_pipeline import train_lead_propensity_model

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', day_of_week='6', hour=2)  # Weekly on Sunday
def retrain_model():
    result = train_lead_propensity_model(DB_FILE)
    logging.info(f"Model retraining completed: {result}")

scheduler.start()
```

---

## 📚 LMS Usage

### 1. Initialize LMS
```bash
# Automatically initialized on app startup
from taaip_lms import get_lms_manager
lms = get_lms_manager('data/taaip.sqlite3')
```

### 2. Enroll User in Course
```bash
result = lms.enroll_user('user_001', 'usarec-101')
# Output: {"status": "ok", "enrollment_id": "enr_user_001_usarec-101_..."}
```

### 3. Update Progress
```bash
lms.update_progress('enr_user_001_usarec-101_...', 45)  # 45% progress
```

### 4. Get User Courses
```bash
enrollments = lms.get_user_enrollments('user_001')
for e in enrollments:
    print(f"{e['title']}: {e['progress_percent']}%")
```

### 5. Get LMS Stats
```bash
stats = lms.get_course_stats()
print(f"Total courses: {stats['total_courses']}")
print(f"Completion rate: {stats['completion_rate']}%")
```

---

## 📊 Power BI Integration

### Setup Instructions
1. **Get Service Principal Credentials**:
   - Go to Azure Portal → App registrations → Create new
   - Note: `client_id`, `client_secret`, `tenant_id`
   - Grant Power BI admin consent

2. **Configure in TAAIP**:
   - Set environment variables:
     ```bash
     export POWER_BI_CLIENT_ID="your-client-id"
     export POWER_BI_CLIENT_SECRET="your-client-secret"
     export POWER_BI_TENANT_ID="your-tenant-id"
     ```

3. **Embed Dashboard**:
   - Update `taaip-dashboard/src/App.tsx` PowerBIView component
   - Replace iframe URL with your Power BI dashboard embed URL

---

## 📡 GitHub Actions CI/CD

### Check Workflow Status
```bash
# View latest workflow runs
gh workflow list

# View job logs
gh run view <run-id>
```

### Add Secrets to GitHub
```bash
# Add export token
gh secret set EXPORT_API_TOKEN --body "your-secure-token"

# Add Codecov token (optional)
gh secret set CODECOV_TOKEN --body "your-codecov-token"
```

---

## 🔧 Configuration & Environment Variables

### Backend (.env or export)
```bash
export EXPORT_API_TOKEN="devtoken123"
export DATABASE_URL="sqlite:///data/taaip.sqlite3"
export LOG_LEVEL="INFO"
```

### Frontend (.env.local in taaip-dashboard/)
```
VITE_API_URL=http://localhost:8000/api/v2
VITE_API_KEY=devtoken123
```

---

## 📖 API Reference

### Key Endpoints
- `GET /api/v2/funnel/stages` - Recruiting funnel stages
- `POST /api/v2/marketing/activities` - Record marketing activity
- `GET /api/v2/kpis` - Compute KPIs
- `GET /api/v2/exports/activities.csv` - Export activities
- `POST /api/v2/ingest/survey` - Ingest survey data
- `GET /api/v2/segments/{lead_id}` - Get lead segments

Full docs at: http://localhost:8000/docs

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process on port 8000
kill -9 <PID>

# Try different port
python -m uvicorn taaip_service:app --port 8001
```

### Frontend Won't Build
```bash
cd taaip-dashboard
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Database Errors
```bash
# Reset database
rm data/taaip.sqlite3
python -c "from taaip_service import init_db; init_db()"
```

### Tests Failing
```bash
# Run tests in verbose mode
pytest -vv

# Run specific test
pytest test_taaip_marketing.py::test_record_marketing_activity -vv
```

---

## 📚 Documentation

- **Architecture**: `EXTENDED_ARCHITECTURE.md`
- **USAREC Funnel**: `USAREC_RECRUITING_FUNNEL.md`
- **API Reference**: `API_REFERENCE_V2.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **Integration**: `INTEGRATION_GUIDE.md`

---

## 🎓 Next Steps

1. ✅ Start backend & frontend
2. ✅ Test API endpoints
3. ✅ Train AI model on sample data
4. ✅ Enroll users in LMS courses
5. ⏳ Configure Power BI integration
6. ⏳ Deploy to production (Docker, Kubernetes, AWS, etc.)

---

## 📞 Support

- **GitHub Issues**: https://github.com/Moondawg91/TAAIP/issues
- **Documentation**: See docs/ folder
- **API Docs**: http://localhost:8000/docs

---

**TAAIP 2.0 - Multifunctional Recruiting Intelligence Platform**
Last Updated: November 15, 2025
