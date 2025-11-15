# TAAIP — Quick Start Guide

## Overview
The TAAIP system is now a complete 3-tier stack:

1. **FastAPI Backend** (port 8000) — Lead Scoring engine (Python)
2. **Node.js API Gateway** (port 3000) — CORS proxy & orchestration
3. **React Frontend** (Vite, port 5173) — Admin UI for lead scoring

## Files & Structure

```
/Users/ambermooney/Desktop/TAAIP/
├── taaip_service.py           # FastAPI lead scoring service
├── api-gateway.js             # Express.js API Gateway
├── package.json               # Node.js dependencies (gateway)
├── run-dev.sh                 # One-command dev stack launcher
├── requirements.txt           # Python dependencies
├── ARCHITECTURE.md            # System design (AWS/Azure)
├── frontend/
│   ├── App.jsx                # React component (Tailwind + Lucide icons)
│   ├── package.json           # React + Vite + dependencies
│   ├── app.js                 # Simple browser demo (alternate)
│   ├── index.html             # Browser demo entry (alternate)
│   └── style.css              # Demo styles (alternate)
├── k8s/
│   └── sample-deployments.yaml # Kubernetes manifests for AKS
└── diagrams/
    └── architecture.puml       # PlantUML architecture diagram
```

## Quick Start (One Command)

```bash
cd /Users/ambermooney/Desktop/TAAIP
chmod +x run-dev.sh
./run-dev.sh
```

This script will:
1. Create/activate Python venv, install FastAPI & uvicorn
2. Start FastAPI backend on port 8000
3. Install Node dependencies & start API Gateway on port 3000
4. Optionally start Vite dev server on port 5173

**Output:**
```
✓ Stack ready!
- FastAPI backend:    http://127.0.0.1:8000
- API Gateway:        http://127.0.0.1:3000
- Frontend (Vite):    http://127.0.0.1:5173
- FastAPI docs:       http://127.0.0.1:8000/docs
```

## Manual Start (if run-dev.sh doesn't work)

**Terminal 1 — FastAPI Backend:**
```bash
source .venv/bin/activate
python -m uvicorn taaip_service:app --reload --port 8000
```

**Terminal 2 — API Gateway:**
```bash
npm install  # If not already done
node api-gateway.js
```

**Terminal 3 — Frontend (optional, or use browser demo):**
```bash
cd frontend
npm install  # If not already done
npm run dev
```

## How to Use

### Option A: Browser-based Demo (Simplest)
1. Open a browser and go to: **http://127.0.0.1:3000**
2. The static HTML demo (`frontend/app.js` + `index.html`) will load
3. Fill in the form and click "Get Predictive Score"
4. The API Gateway proxies your request to FastAPI

### Option B: React App (Vite Dev Server)
1. Open a browser and go to: **http://127.0.0.1:5173**
2. Hot reload enabled; edit `frontend/App.jsx` and changes appear instantly

### Option C: CLI/cURL
```bash
curl -sS -X POST http://127.0.0.1:3000/api/targeting/scoreLead \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id":"demo-001",
    "age":28,
    "education_level":"Bachelors",
    "cbsa_code":"41884",
    "campaign_source":"High-Impact-Targeting-Campaign"
  }'
```

**Response:**
```json
{
  "lead_id": "demo-001",
  "predicted_probability": 0.64,
  "score": 64,
  "recommendation": "Medium Priority: Add to Nurture Campaign Queue"
}
```

## Testing Full Stack

Run all three services, then:

```bash
# Check backend health
curl http://127.0.0.1:8000/health

# Check gateway health
curl http://127.0.0.1:3000/health

# Test scoring endpoint (proxied through gateway)
curl -X POST http://127.0.0.1:3000/api/targeting/scoreLead \
  -H "Content-Type: application/json" \
  -d '{"lead_id":"test","age":25,"education_level":"Bachelors","cbsa_code":"12345","campaign_source":"Social"}'
```

## API Endpoints

### FastAPI Backend (port 8000)
- `GET /health` — Service health status
- `POST /api/v1/scoreLead` — Lead scoring (requires FastAPI Pydantic schema)
- `GET /docs` — Auto-generated Swagger UI

### API Gateway (port 3000)
- `GET /health` — Proxies to FastAPI backend
- `POST /api/targeting/scoreLead` — Proxies lead scoring requests to FastAPI

## Frontend Features

The React component (`App.jsx`) includes:
- Real-time API status indicator (green=online, red=offline)
- Form validation (age >= 18)
- Exponential backoff retry logic for robust network calls
- Color-coded score display (green ≥85, yellow 60–84, red <60)
- Recruiter action recommendations
- Tailwind CSS styling + Lucide icons

## Architecture Layers

```
┌─────────────────────────────────────┐
│   React Frontend (Vite)             │
│   - Tailwind CSS + Lucide Icons     │
│   - API status polling              │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Node.js API Gateway (Express)     │
│   - CORS proxy                      │
│   - Input validation                │
│   - Error handling                  │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   FastAPI Lead Scoring (Python)     │
│   - Pydantic models                 │
│   - Lead scoring logic              │
│   - Model placeholder               │
└─────────────────────────────────────┘
```

## Next Steps

1. **Replace mock scoring** — Integrate a real ML model (Scikit-learn, TensorFlow)
2. **Add authentication** — Integrate Azure AD or OAuth2 at the API Gateway
3. **Deploy to AKS** — Use Kubernetes manifests in `k8s/sample-deployments.yaml`
4. **Add monitoring** — Integrate Azure Monitor / Prometheus for observability
5. **Implement CI/CD** — GitHub Actions to build/test/deploy services

## Troubleshooting

### "API Gateway: Offline/Unreachable"
- Check FastAPI is running: `curl http://127.0.0.1:8000/health`
- Check Node.js API Gateway is running: `curl http://127.0.0.1:3000/health`

### Port already in use
```bash
lsof -ti:8000 | xargs kill -9  # Kill FastAPI on port 8000
lsof -ti:3000 | xargs kill -9  # Kill API Gateway on port 3000
lsof -ti:5173 | xargs kill -9  # Kill Vite on port 5173
```

### Python venv issues
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Node dependencies issues
```bash
rm -rf node_modules package-lock.json
npm install
```

## Key Files to Edit

- **Scoring logic**: `taaip_service.py` — `score_lead()` function
- **Frontend form**: `frontend/App.jsx` — Add/remove fields
- **Gateway routing**: `api-gateway.js` — Add new endpoints

---

**Status:** ✅ Full stack running and tested (FastAPI + Node.js + React)
