# TAAIP Extended API Reference

## Overview
Complete REST API reference for the enhanced TAAIP system including ROI tracking, recruiting funnel management, project management, M-IPOE documentation, D3AE/F3A targeting, and forecasting.

---

## Base URL
```
http://localhost:8000/api/v2
```

## Authentication
All endpoints support optional Bearer token authentication (if `TAAIP_API_TOKEN` is set):
```
Authorization: Bearer <token>
```

---

## Events & ROI Tracking

### Create Event
**POST** `/events`

Create a new recruiting event (job fair, campus visit, social media campaign).

**Request Body**:
```json
{
  "name": "Fort Jackson Job Fair 2025",
  "type": "In-Person-Meeting",
  "location": "Fort Jackson, SC",
  "start_date": "2025-02-15",
  "end_date": "2025-02-15",
  "budget": 50000,
  "team_size": 12,
  "targeting_principles": "D3AE_Primary, F3A_Focus"
}
```

**Response**:
```json
{
  "status": "ok",
  "event_id": "evt_a1b2c3d4e5f6"
}
```

---

### Get Event ROI Metrics
**GET** `/events/{event_id}/metrics`

Retrieve real-time ROI and performance metrics for an event.

**Response**:
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "metrics": [
    {
      "date": "2025-02-15",
      "leads_generated": 150,
      "leads_qualified": 95,
      "conversion_count": 12,
      "cost_per_lead": 333.33,
      "roi": 1.45,
      "engagement_rate": 0.63
    }
  ]
}
```

---

### Record Event Metrics
**POST** `/events/{event_id}/metrics`

Live update of event performance (called by TA technician during/after event).

**Request Body**:
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "date": "2025-02-15",
  "leads_generated": 150,
  "leads_qualified": 95,
  "conversion_count": 12,
  "cost_per_lead": 333.33,
  "roi": 1.45,
  "engagement_rate": 0.63
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "Metrics recorded"
}
```

---

### Capture Survey Feedback
**POST** `/events/{event_id}/survey`

Capture real-time survey feedback from TA technician about event effectiveness.

**Request Body**:
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "lead_id": "lead_xyz",
  "technician_id": "tech_001",
  "effectiveness_rating": 4,
  "feedback": "Strong turnout, high-quality interactions, messaging resonated well with HS graduates."
}
```

**Response**:
```json
{
  "status": "ok",
  "survey_id": "sur_abc123def456"
}
```

---

### Get Event Feedback
**GET** `/events/{event_id}/feedback`

Retrieve aggregated survey feedback for an event.

**Response**:
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "feedback": [
    {
      "technician_id": "tech_001",
      "effectiveness_rating": 4,
      "feedback": "Strong turnout, high-quality interactions..."
    }
  ]
}
```

---

## Recruiting Funnel

### Get Funnel Stages
**GET** `/funnel/stages`

List all recruiting funnel stages.

**Response**:
```json
{
  "stages": [
    {
      "stage_id": "lead",
      "stage_name": "Lead",
      "sequence_order": 1,
      "description": "Unqualified, raw prospect"
    },
    {
      "stage_id": "qualified",
      "stage_name": "Qualified Lead",
      "sequence_order": 2,
      "description": "Passed initial screening"
    },
    {
      "stage_id": "contract",
      "stage_name": "Contract",
      "sequence_order": 8,
      "description": "Signed contract"
    }
  ]
}
```

---

### Record Funnel Transition
**POST** `/funnel/transition`

Move a lead from one funnel stage to the next (tracks progression toward contract).

**Request Body**:
```json
{
  "lead_id": "lead_xyz",
  "from_stage": "lead",
  "to_stage": "qualified",
  "transition_reason": "Passed ASVAB screening with 67 GT score",
  "technician_id": "tech_001"
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "Lead lead_xyz transitioned to qualified"
}
```

---

### Get Funnel Metrics
**GET** `/funnel/metrics`

Get conversion rates and lead distribution across all funnel stages.

**Response**:
```json
{
  "stage_distribution": {
    "lead": 1250,
    "qualified": 850,
    "engaged": 620,
    "interested": 480,
    "applicant": 320,
    "interview": 180,
    "offer": 95,
    "contract": 42
  }
}
```

---

## Project Management

### Create Project
**POST** `/projects`

Create an event planning project with tasks and milestones.

**Request Body**:
```json
{
  "name": "Fort Jackson Job Fair 2025 Planning",
  "event_id": "evt_a1b2c3d4e5f6",
  "start_date": "2025-01-15",
  "target_date": "2025-02-15",
  "owner_id": "mgr_001",
  "objectives": "Generate 150+ leads, 95+ qualified leads, close event ROI at 1.4x+",
  "success_criteria": "Convert 12+ leads to applicants, maintain cost per lead under $350"
}
```

**Response**:
```json
{
  "status": "ok",
  "project_id": "prj_xyz123abc456"
}
```

---

### Create Task
**POST** `/projects/{project_id}/tasks`

Create a task within a project (e.g., "Setup booth", "Train recruiters", "Coordinate logistics").

**Request Body**:
```json
{
  "project_id": "prj_xyz123abc456",
  "title": "Finalize Recruiting Messaging",
  "description": "Develop messaging aligned with D3AE targeting (HS graduates, age 18-35, tech careers)",
  "assigned_to": "tech_marketing",
  "due_date": "2025-02-01",
  "priority": "high"
}
```

**Response**:
```json
{
  "status": "ok",
  "task_id": "tsk_abc001def002"
}
```

---

### Update Task
**PUT** `/projects/{project_id}/tasks/{task_id}`

Update task status, due date, or other fields.

**Request Body**:
```json
{
  "status": "complete",
  "completion_date": "2025-02-01"
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "Task updated"
}
```

---

### Get Project Timeline
**GET** `/projects/{project_id}/timeline`

Retrieve project milestones and timeline.

**Response**:
```json
{
  "project_id": "prj_xyz123abc456",
  "milestones": [
    {
      "milestone_id": "mil_001",
      "name": "Messaging finalized",
      "target_date": "2025-02-01",
      "actual_date": null
    },
    {
      "milestone_id": "mil_002",
      "name": "Team training complete",
      "target_date": "2025-02-10",
      "actual_date": null
    },
    {
      "milestone_id": "mil_003",
      "name": "Event execution",
      "target_date": "2025-02-15",
      "actual_date": null
    }
  ]
}
```

---

## M-IPOE Analysis

### Create M-IPOE Record
**POST** `/mipoe`

Document event planning and execution using the M-IPOE (Intent, Plan, Order, Execute, Evaluate) framework.

**Request Body** (Intent Phase):
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "phase": "intent",
  "content": {
    "strategic_objective": "Increase officer acquisition in underrepresented markets",
    "target_demographic": "HS graduates, 18-28, tech-interested, Southeast region",
    "timeline": "Q1 2025",
    "commander_intent": "Focus recruiting efforts on high-propensity demographics per D3AE principles"
  },
  "owner_id": "commander_001"
}
```

**Response**:
```json
{
  "status": "ok",
  "mipoe_id": "mip_xyz123abc456"
}
```

**Example: Plan Phase**:
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "phase": "plan",
  "content": {
    "event_type": "In-Person Job Fair",
    "venue": "Fort Jackson, SC",
    "budget": 50000,
    "team_size": 12,
    "targeting_profile": "D3AE_Primary (HS grads, tech careers), F3A focus (high-density markets)",
    "expected_leads": 150,
    "conversion_target": 10
  },
  "owner_id": "planner_001"
}
```

---

### Get M-IPOE Record
**GET** `/mipoe/{mipoe_id}`

Retrieve M-IPOE record.

**Response**:
```json
{
  "mipoe_id": "mip_xyz123abc456",
  "event_id": "evt_a1b2c3d4e5f6",
  "phase": "intent",
  "content": {
    "strategic_objective": "...",
    "target_demographic": "..."
  },
  "owner_id": "commander_001",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

---

## D3AE/F3A Targeting Profiles

### Create Targeting Profile
**POST** `/targeting-profiles`

Define D3AE and F3A targeting parameters for an event.

**Request Body**:
```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "target_age_min": 18,
  "target_age_max": 28,
  "target_education_level": "High School, Some College",
  "target_locations": "37980,41884,35980",
  "message_themes": "career_growth,education_benefits,technology,personal_development",
  "contact_frequency": 3,
  "conversion_target": 0.12,
  "cost_per_lead_target": 333.33
}
```

**Response**:
```json
{
  "status": "ok",
  "profile_id": "tgt_abc123def456"
}
```

---

### Get Targeting Profile
**GET** `/targeting-profiles/{profile_id}`

Retrieve targeting profile.

**Response**:
```json
{
  "profile_id": "tgt_abc123def456",
  "event_id": "evt_a1b2c3d4e5f6",
  "target_age_min": 18,
  "target_age_max": 28,
  "target_education_level": "High School, Some College",
  "target_locations": "37980,41884,35980",
  "message_themes": "career_growth,education_benefits,technology,personal_development",
  "contact_frequency": 3,
  "conversion_target": 0.12,
  "cost_per_lead_target": 333.33,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

---

## Forecasting & Analytics

### Get Quarterly Forecast
**GET** `/forecasts/{quarter}/{year}`

Retrieve quarterly projections.

**Response**:
```json
{
  "forecast_id": "fct_xyz123abc456",
  "quarter": 1,
  "year": 2025,
  "projected_leads": 1200,
  "projected_conversions": 95,
  "projected_roi": 1.45,
  "confidence_level": 0.75,
  "methodology": "historical_average",
  "created_at": "2025-01-10T09:00:00"
}
```

---

### Generate Forecast
**POST** `/forecasts/generate`

Trigger forecast generation using historical data or ML model.

**Request Body**:
```json
{
  "quarter": 2,
  "year": 2025
}
```

**Response**:
```json
{
  "status": "ok",
  "forecast_id": "fct_xyz123abc456",
  "quarter": 2,
  "year": 2025,
  "projected_leads": 1400,
  "projected_conversions": 115,
  "projected_roi": 1.52,
  "confidence_level": 0.75
}
```

---

### Get Dashboard Snapshot
**GET** `/analytics/dashboard`

Get comprehensive dashboard snapshot (all metrics, current quarter).

**Response**:
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

## Error Responses

All endpoints return standard HTTP error codes:

- `400 Bad Request` — Invalid request body or parameters
- `401 Unauthorized` — Invalid or missing bearer token
- `404 Not Found` — Resource not found
- `500 Internal Server Error` — Server error

**Error Response Format**:
```json
{
  "detail": "Error message describing the issue"
}
```

---

## Integration Example: Complete Event Workflow

### 1. Plan Event (Week 1)
```bash
# Create event
curl -X POST http://localhost:8000/api/v2/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fort Jackson Job Fair 2025",
    "type": "In-Person-Meeting",
    "location": "Fort Jackson, SC",
    "budget": 50000,
    "team_size": 12
  }'
# Response: event_id = evt_a1b2c3d4e5f6

# Create targeting profile
curl -X POST http://localhost:8000/api/v2/targeting-profiles \
  -d '{
    "event_id": "evt_a1b2c3d4e5f6",
    "target_age_min": 18,
    "target_age_max": 28,
    "target_education_level": "High School, Some College"
  }'

# Create project
curl -X POST http://localhost:8000/api/v2/projects \
  -d '{
    "name": "Fort Jackson Planning",
    "event_id": "evt_a1b2c3d4e5f6",
    "start_date": "2025-01-15",
    "target_date": "2025-02-15"
  }'

# Document M-IPOE intent
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{
    "event_id": "evt_a1b2c3d4e5f6",
    "phase": "intent",
    "content": { "strategic_objective": "..." }
  }'
```

### 2. Execute Event (Day of Event)
```bash
# Record live metrics
curl -X POST http://localhost:8000/api/v2/events/evt_a1b2c3d4e5f6/metrics \
  -d '{
    "date": "2025-02-15",
    "leads_generated": 150,
    "leads_qualified": 95
  }'

# Capture TA technician survey
curl -X POST http://localhost:8000/api/v2/events/evt_a1b2c3d4e5f6/survey \
  -d '{
    "technician_id": "tech_001",
    "effectiveness_rating": 4,
    "feedback": "Strong turnout, excellent engagement"
  }'

# Record funnel transitions
curl -X POST http://localhost:8000/api/v2/funnel/transition \
  -d '{
    "lead_id": "lead_xyz",
    "from_stage": "lead",
    "to_stage": "qualified",
    "technician_id": "tech_001"
  }'
```

### 3. Evaluate & Plan Next Event
```bash
# Get event ROI metrics
curl http://localhost:8000/api/v2/events/evt_a1b2c3d4e5f6/metrics

# Get funnel metrics
curl http://localhost:8000/api/v2/funnel/metrics

# Generate forecast for Q2
curl -X POST http://localhost:8000/api/v2/forecasts/generate \
  -d '{"quarter": 2, "year": 2025}'

# Get dashboard snapshot
curl http://localhost:8000/api/v2/analytics/dashboard

# Document M-IPOE evaluate
curl -X POST http://localhost:8000/api/v2/mipoe \
  -d '{
    "event_id": "evt_a1b2c3d4e5f6",
    "phase": "evaluate",
    "content": {
      "actual_leads": 150,
      "actual_conversions": 12,
      "actual_roi": 1.45,
      "lessons_learned": "..."
    }
  }'
```

---

## Notes

- All endpoints support Bearer token authentication via `Authorization` header.
- Timestamps are ISO 8601 format (`YYYY-MM-DDTHH:MM:SS`).
- UUIDs are shortened hex strings for readability (e.g., `evt_a1b2c3d4e5f6`).
- M-IPOE phases: `intent`, `plan`, `order`, `execute`, `evaluate`.
- D3AE/F3A targeting is flexible and can be extended per USAREC/USARD guidance.
