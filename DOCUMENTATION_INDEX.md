# TAAIP Documentation Index

## 📚 Complete Documentation Suite

This index provides a roadmap to all TAAIP documentation and resources.

---

## 🎯 Start Here

### New to TAAIP?
1. **[README_COMPREHENSIVE.md](README_COMPREHENSIVE.md)** — Complete overview, architecture, and quick start
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — One-page reference card with copy-paste commands
3. **[API_REFERENCE_V2.md](API_REFERENCE_V2.md)** — Detailed endpoint documentation

### Want to Run It Locally?
1. **[README_COMPREHENSIVE.md](README_COMPREHENSIVE.md)** — Quick Start section (5 minutes)
2. **[QUICKSTART.md](QUICKSTART.md)** — Original quick start guide
3. **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** — Python examples and workflows

### Deploying to Production?
1. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** — Complete deployment documentation
2. **[EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md)** — System design and scaling

---

## 📖 Documentation by Category

### Getting Started
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md) | Full system overview with quick start | 15 min |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | One-page cheat sheet with curl examples | 5 min |
| [QUICKSTART.md](QUICKSTART.md) | Original quick start guide | 10 min |

### API Documentation
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [API_REFERENCE_V2.md](API_REFERENCE_V2.md) | Complete REST API reference with examples | 30 min |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Python client examples and workflows | 20 min |
| [EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md) | Data model and domain design | 25 min |

### Deployment & Operations
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Local, Docker, production, K8s deployment | 40 min |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Original architecture documentation | 15 min |

### Planning & Strategy
| Document | Purpose | Read Time |
|----------|---------|-----------|
| [PILOT_PLAN.md](PILOT_PLAN.md) | Pilot program and rollout plan | 20 min |
| [WHITEPAPER.md](WHITEPAPER.md) | TAAIP concept and strategic vision | 25 min |
| [next-steps.md](next-steps.md) | Future roadmap and next phases | 10 min |

---

## 🔗 Core Files

### Backend
```
taaip_service.py          # Main FastAPI backend (571 lines)
                          # Features: Events, ROI, funnel, projects, 
                          #          M-IPOE, targeting, forecasting
```

**Key endpoints**:
- `/api/v2/events` — Event management
- `/api/v2/funnel/*` — Recruiting funnel
- `/api/v2/projects/*` — Project management
- `/api/v2/mipoe` — M-IPOE documentation
- `/api/v2/targeting-profiles` — D3AE/F3A targeting
- `/api/v2/forecasts/*` — Forecasting & analytics

### API Gateway
```
api-gateway.js            # Express.js gateway
                          # Routes: /api/targeting/* → backend
                          # Auth: Optional Bearer token
```

### Frontend
```
frontend/
  ├── index.html         # Demo UI
  ├── app.js             # Frontend logic
  ├── style.css          # Styling
  └── App.jsx            # React template (planned)
```

### Database
```
data/
  ├── taaip.sqlite3      # SQLite database (auto-created on startup)
  └── model.joblib       # Optional ML model (place here)
```

### Testing
```
test_taaip_api.py        # Comprehensive API test suite
                         # Tests all endpoints and workflows
```

### Configuration
```
requirements.txt         # Python dependencies
package.json            # Node.js dependencies
docker-compose.yml      # Local Docker development
Dockerfile.backend      # Backend container image
Dockerfile.gateway      # Gateway container image
```

---

## 📊 Database Schema

### Tables (13 total)

**Core Recruiting**:
- `leads` — Lead scoring (legacy support)
- `pilot_state` — Pilot program tracking

**Events & ROI**:
- `events` — Recruiting events
- `event_metrics` — Real-time ROI metrics
- `capture_survey` — TA technician feedback

**Funnel**:
- `funnel_stages` — 8 stages (auto-initialized)
- `funnel_transitions` — Lead progression tracking

**Projects**:
- `projects` — Event planning projects
- `tasks` — Project tasks
- `milestones` — Timeline tracking

**Military Planning**:
- `mipoe` — M-IPOE phase documentation

**Targeting**:
- `targeting_profiles` — D3AE/F3A parameters

**Analytics**:
- `forecasts` — Quarterly projections
- `analytics_snapshots` — Aggregated metrics

---

## 🚀 Quick Commands

### Start Service
```bash
cd /Users/ambermooney/Desktop/TAAIP
python taaip_service.py
# Backend: http://localhost:8000
# Database: data/taaip.sqlite3 (auto-created)
```

### Run Tests
```bash
python test_taaip_api.py
# Output: Summary of all tests (events, funnel, projects, M-IPOE, etc.)
```

### Docker Development
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Gateway: http://localhost:3001
# Frontend: http://localhost:3000
```

### Test Individual Endpoint
```bash
# Create event
curl -X POST http://localhost:8000/api/v2/events \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","type":"In-Person-Meeting","location":"SC","budget":50000,"team_size":12}'

# Get dashboard
curl http://localhost:8000/api/v2/analytics/dashboard

# List funnel stages
curl http://localhost:8000/api/v2/funnel/stages
```

---

## 🎓 Learning Paths

### Path 1: Quick Integration (30 minutes)
1. Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (5 min)
2. Start service: `python taaip_service.py` (1 min)
3. Run tests: `python test_taaip_api.py` (2 min)
4. Try curl examples from [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (10 min)
5. Read [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) — Python section (10 min)

### Path 2: Full Implementation (2 hours)
1. Read [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md) (15 min)
2. Read [EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md) (25 min)
3. Read [API_REFERENCE_V2.md](API_REFERENCE_V2.md) (30 min)
4. Read [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) (30 min)
5. Build complete workflow using examples (20 min)

### Path 3: Production Deployment (4 hours)
1. Read [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md) — architecture (15 min)
2. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) (60 min)
3. Setup local Docker: `docker-compose up -d` (5 min)
4. Test with: `python test_taaip_api.py` (5 min)
5. Migrate database to PostgreSQL (30 min)
6. Configure HTTPS/TLS (30 min)
7. Setup monitoring & logging (30 min)

### Path 4: Military Integration (3 hours)
1. Read [WHITEPAPER.md](WHITEPAPER.md) (25 min)
2. Read [EXTENDED_ARCHITECTURE.md](EXTENDED_ARCHITECTURE.md) — M-IPOE section (20 min)
3. Read [API_REFERENCE_V2.md](API_REFERENCE_V2.md) — M-IPOE section (15 min)
4. Study D3AE/F3A targeting in [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md) (20 min)
5. Build M-IPOE workflow from [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) (30 min)
6. Test with: `python test_taaip_api.py` (5 min)

---

## 🔑 Key Concepts

### D3AE (Demographics, Dialect, Attitude, Education)
- **Demographics**: Age, gender, location, income
- **Dialect**: Language, communication style, values
- **Attitude**: Motivations, priorities, career interests
- **Education**: HS, college, military background

Example targeting:
```json
{
  "target_age_min": 18,
  "target_age_max": 28,
  "target_locations": ["37980", "41884"],
  "message_themes": ["career_growth", "education_benefits"]
}
```

### F3A (Frequency, Forums, Format)
- **Frequency**: Contact rate (3-5x recommended)
- **Forums**: Channels (in-person, social, email, SMS)
- **Format**: Content style, messaging tone

### M-IPOE (Military Decision Process)
1. **Intent** — Strategic objective and vision
2. **Plan** — Detailed event design
3. **Order** — Task assignment and preparation
4. **Execute** — Live event execution
5. **Evaluate** — Post-event analysis and lessons

### Recruiting Funnel (8 Stages)
1. Lead → 2. Qualified → 3. Engaged → 4. Interested → 
5. Applicant → 6. Interview → 7. Offer → 8. Contract

---

## 📈 API Statistics

### Endpoint Coverage
- **Events**: 6 endpoints (create, get, metrics, survey, feedback)
- **Funnel**: 3 endpoints (stages, transition, metrics)
- **Projects**: 4 endpoints (create, tasks, update task, timeline)
- **M-IPOE**: 2 endpoints (create, get)
- **Targeting**: 2 endpoints (create, get)
- **Forecasting**: 3 endpoints (generate, get, dashboard)
- **Total**: 20+ endpoints

### Database Tables
- **13 tables** with automatic schema initialization
- **Relationships**: Events → Metrics, Events → Projects, Events → MIPOE, etc.
- **Auto-initialized**: 8 funnel stages on startup
- **Scalable**: SQLite (dev) to PostgreSQL (prod)

---

## 🧪 Testing & Validation

### Automated Test Suite
```bash
python test_taaip_api.py
```

**Coverage**:
- ✅ Event creation and metrics
- ✅ Funnel transitions and metrics
- ✅ Project and task management
- ✅ M-IPOE documentation
- ✅ Targeting profile creation
- ✅ Forecasting and analytics

### Manual Testing
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for curl examples
- See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for Python examples

---

## 🔒 Security

### Authentication
- Optional Bearer token via `TAAIP_API_TOKEN` env var
- All endpoints support token validation
- Gateway enforces auth on `/api/targeting/*`

### Data Protection
- SQLite (local), PostgreSQL (production)
- HTTPS/TLS for production
- OAuth/OIDC recommended for enterprise

---

## 🚀 Deployment Options

| Option | Best For | Setup Time |
|--------|----------|-----------|
| **Direct Python** | Development | 2 min |
| **Docker Compose** | Local testing | 5 min |
| **Kubernetes** | Production | 30 min |
| **AWS/GCP/Azure** | Enterprise | 1-2 hours |

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for details.

---

## 📞 Support Resources

### Documentation
- Full docs: [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md)
- API ref: [API_REFERENCE_V2.md](API_REFERENCE_V2.md)
- Code examples: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- Deployment: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Getting Help
1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands
2. See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for code examples
3. Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for ops questions
4. Run `python test_taaip_api.py` to verify service health

### Common Issues
- **Port in use**: `lsof -i :8000 && kill -9 <PID>`
- **Module not found**: `pip install -r requirements.txt`
- **DB locked**: Use PostgreSQL for multi-process
- **Auth failed**: Check `TAAIP_API_TOKEN` env var

---

## 📋 Roadmap

### ✅ Completed (Phase 1)
- Database schema with 13 tables
- 20+ API endpoints
- Real-time metrics capture
- TA feedback system
- Basic forecasting

### 🔄 In Progress (Phase 2)
- React dashboard
- D3.js visualization
- Advanced charting

### 📅 Planned (Phases 3-4)
- Advanced forecasting (ARIMA)
- OAuth/OIDC auth
- PostgreSQL migration
- Kubernetes deployment
- Multi-tenancy

---

## 📄 Version Information

- **Version**: 2.0.0
- **Status**: Production Ready
- **Last Updated**: January 2025
- **Python**: 3.8+
- **Node**: 14+
- **Database**: SQLite (dev) / PostgreSQL (prod)

---

## 🙏 Acknowledgments

TAAIP integrates principles from:
- **Army Recruiting Command (USAREC)**
- **Army Reserve Recruiting (USARD)**
- **D3AE Targeting Doctrine**
- **F3A Strategy**
- **M-IPOE Military Planning**

---

## 📞 Contact & More Info

- **USAREC**: www.usarec.army.mil
- **USARD**: www.usar.army.mil
- **Documentation**: See links above
- **Support**: Check troubleshooting sections in relevant docs

---

**This index provides navigation to all TAAIP documentation and resources.**  
**Start with [README_COMPREHENSIVE.md](README_COMPREHENSIVE.md) or [QUICK_REFERENCE.md](QUICK_REFERENCE.md).**
