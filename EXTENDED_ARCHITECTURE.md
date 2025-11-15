# TAAIP Extended Architecture: ROI, Funnel, Project Management & Forecasting

## Overview
Enhanced TAAIP system for comprehensive recruiting analytics, event ROI tracking, funnel pipeline visibility, and predictive forecasting aligned with USAREC/USARD targeting principles (D3AE, F3A, M-IPOE).

---

## Core Domains

### 1. ROI & Event Tracking
**Purpose**: Measure effectiveness of recruiting events and capture real-time data.

**Entities**:
- `Event` — recruiting event (job fair, campus visit, social media campaign)
  - `event_id`, `name`, `type` (In-Person-Meeting, Digital-Campaign, etc.)
  - `location`, `start_date`, `end_date`
  - `budget`, `team_size`
  - `targeting_principles` (D3AE/F3A rules applied)
  - `status` (planned, active, completed)

- `EventMetrics` — daily/live KPIs
  - `event_id`, `date`, `leads_generated`, `leads_qualified`, `conversion_count`, `cost_per_lead`
  - `roi`, `engagement_rate`

- `CaptureSurvey` — real-time survey from TA technicians
  - `survey_id`, `event_id`, `lead_id`
  - `timestamp`, `technician_id`
  - `effectiveness_rating`, `feedback`, `data_quality_flag`

### 2. Recruiting Funnel (Lead-to-Contract Pipeline)
**Purpose**: Track lead progression through stages.

**Stages**:
1. Lead (unqualified, raw prospect)
2. Qualified Lead (passed initial screening)
3. Engaged (communication initiated)
4. Interested (expressed interest)
5. Applicant (submitted application)
6. Interview (interview scheduled/completed)
7. Offer (offer extended)
8. Contract (signed contract)

**Entities**:
- `FunnelStage` — stage definitions (idempotent)
- `FunnelTransition` — lead movement + timestamp, reason, technician
- `StageMetrics` — aggregates per stage (count, avg time in stage, drop-off rate)

### 3. Project Management (Event Planning & Tasking)
**Purpose**: Coordinate event planning, task allocation, and timeline.

**Entities**:
- `Project` — event planning project
  - `project_id`, `name`, `event_id`, `start_date`, `target_date`
  - `owner_id`, `status` (planning, active, closed)
  - `objectives`, `success_criteria`

- `Task` — individual action item
  - `task_id`, `project_id`, `title`, `description`
  - `assigned_to`, `due_date`, `status` (open, in-progress, complete)
  - `priority`, `completion_date`

- `Timeline` — milestone tracking
  - `milestone_id`, `project_id`, `name`, `target_date`, `actual_date`

### 4. M-IPOE Analysis
**Purpose**: Structured military decision-making framework.

**Phases**:
- **Intent**: Strategic objectives, targeting guidance (D3AE/F3A principles)
- **Plan**: Event strategy, budget, target demographics, messaging
- **Order**: Resource allocation, task assignment, timeline
- **Execute**: Live event execution, real-time feedback
- **Evaluate**: ROI analysis, feedback aggregation, lessons learned

**Entities**:
- `MIPOE` — linked to event/project
  - `mipoe_id`, `event_id`, `phase` (intent, plan, order, execute, evaluate)
  - `content` (JSON), `created_at`, `updated_at`, `owner_id`

### 5. D3AE & F3A Targeting Principles
**Purpose**: Apply Army Recruiting targeting doctrine.

**D3AE** (Data-Driven, Demographic, Age-Gender, Education):
- Identify high-propensity demographics (age, education, location, ASVAB-ready)
- Focus messaging on life outcomes (career, education, personal growth)

**F3A** (Focus, Frequency, Fidelity, Affinity):
- **Focus**: Concentrate on high-value markets
- **Frequency**: Optimal contact cadence
- **Fidelity**: Message consistency
- **Affinity**: Alignment with prospect values

**Entities**:
- `TargetingProfile` — d3ae/F3A configuration per event
  - `profile_id`, `event_id`
  - `target_age_min`, `target_age_max`
  - `target_education_level` (HS, Some College, Bachelors+)
  - `target_locations` (CBSA codes)
  - `message_themes` (career, education, fitness, service)
  - `contact_frequency` (contacts per week)
  - `success_metrics` (conversion rate target, cost per lead target)

### 6. Predictive Forecasting & Analytics
**Purpose**: Quarter-by-quarter planning and predictions.

**Entities**:
- `Forecast` — quarterly projections
  - `forecast_id`, `quarter`, `year`
  - `projected_leads`, `projected_conversions`
  - `projected_roi`, `confidence_level`
  - `methodology` (time-series, ML model, historical average)

- `AnalyticsSnapshot` — aggregated metrics for dashboard
  - `snapshot_id`, `quarter`, `year`
  - `total_events`, `total_leads`, `conversion_rate`
  - `avg_cost_per_lead`, `total_roi`, `by_event` (JSON)

---

## Data Flow

```
TA Technician @ Event
  ↓
[Live Survey Capture] → EventMetrics + FunnelTransition
  ↓
[ROI Dashboard] calculates: cost_per_lead, ROI, effectiveness
  ↓
[Project Management] tracks tasks, milestones, event progress
  ↓
[M-IPOE Analysis] documents intent, plan, order, execute, evaluate
  ↓
[Targeting Profile] (D3AE/F3A) guides next event planning
  ↓
[Forecasting Engine] projects Q2/Q3/Q4 outcomes
```

---

## Key Endpoints (REST/GraphQL)

### ROI & Event Tracking
- `POST /api/v2/events` — Create event
- `GET /api/v2/events/{event_id}/metrics` — Real-time event KPIs
- `POST /api/v2/events/{event_id}/survey` — Capture TA survey
- `GET /api/v2/events/{event_id}/feedback` — Aggregated survey feedback

### Funnel
- `GET /api/v2/funnel/stages` — List funnel stages
- `POST /api/v2/funnel/transition` — Move lead between stages
- `GET /api/v2/funnel/metrics` — Stage conversion rates, drop-off

### Project Management
- `POST /api/v2/projects` — Create event planning project
- `POST /api/v2/projects/{project_id}/tasks` — Create task
- `GET /api/v2/projects/{project_id}/timeline` — Timeline view
- `PUT /api/v2/projects/{project_id}/tasks/{task_id}` — Update task

### M-IPOE
- `POST /api/v2/mipoe` — Create M-IPOE record (phase: intent/plan/order/execute/evaluate)
- `GET /api/v2/mipoe/{mipoe_id}` — Retrieve

### Targeting Profiles (D3AE/F3A)
- `POST /api/v2/targeting-profiles` — Create profile
- `GET /api/v2/targeting-profiles/{profile_id}` — Retrieve
- `PUT /api/v2/targeting-profiles/{profile_id}` — Update

### Forecasting & Analytics
- `GET /api/v2/forecasts/{quarter}/{year}` — Get quarterly forecast
- `POST /api/v2/forecasts/generate` — Trigger forecast generation
- `GET /api/v2/analytics/dashboard` — Dashboard snapshot (all metrics)

---

## Technology Stack

### Backend
- **FastAPI** (Python): Async REST API
- **SQLite** (migration → PostgreSQL for production): Data persistence
- **Pydantic**: Data validation
- **SQLAlchemy**: ORM (optional, for complex queries)

### Analytics & Forecasting
- **NumPy/Pandas**: Time-series analysis
- **Scikit-learn**: Predictive models (regression, classification)
- **Statsmodels**: ARIMA, seasonal decomposition

### Frontend
- **React.js** or **Vue.js**: Dashboard UI
- **D3.js** or **Recharts**: Funnel visualization, ROI charts
- **Plotly**: Quarterly forecasting charts

### DevOps
- **Docker**: Containerization
- **docker-compose**: Local orchestration
- **PostgreSQL**: Production DB (future)

---

## Implementation Roadmap

### Phase 1 (Immediate)
- [x] Extend `taaip_service.py` with new tables (Event, EventMetrics, FunnelStage, etc.)
- [ ] Create API endpoints for event and funnel management
- [ ] Implement survey capture endpoint

### Phase 2 (Week 2)
- [ ] Project management endpoints (projects, tasks, timeline)
- [ ] M-IPOE documentation endpoints
- [ ] Targeting profile (D3AE/F3A) management

### Phase 3 (Week 3)
- [ ] Predictive forecasting logic (time-series, regression)
- [ ] Analytics aggregation endpoints
- [ ] Dashboard data endpoints

### Phase 4 (Week 4+)
- [ ] Frontend dashboard (React/D3.js)
- [ ] Real-time event metrics display
- [ ] Quarterly forecasting charts
- [ ] Production deployment (PostgreSQL, AWS/Azure)

---

## Notes
- All entities include timestamps (`created_at`, `updated_at`) for audit trails.
- Bearer token auth continues across all new endpoints.
- Survey data is JSON-flexible to accommodate TA technician input.
- M-IPOE phases link events → strategy → execution → evaluation.
- D3AE/F3A targeting profiles guide future event planning.
- Forecasting uses historical data + ML for confidence intervals.
