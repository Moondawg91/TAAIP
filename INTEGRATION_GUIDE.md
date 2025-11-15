# TAAIP Integration Guide

## Python Client Examples

This guide shows how to integrate with the TAAIP v2 API using Python.

---

## Setup

### Install Requirements
```bash
pip install requests
```

### Initialize Client
```python
import requests
import json
from datetime import datetime, timedelta

class TAAIPClient:
    def __init__(self, base_url="http://localhost:8000/api/v2", token=None):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def _make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self.headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

# Initialize client
client = TAAIPClient()
```

---

## Event Management

### Create a Recruiting Event

```python
def create_event():
    """Create a new recruiting event."""
    event_data = {
        "name": "Fort Jackson Job Fair 2025",
        "type": "In-Person-Meeting",
        "location": "Fort Jackson, SC",
        "start_date": "2025-02-15",
        "end_date": "2025-02-15",
        "budget": 50000,
        "team_size": 12,
        "targeting_principles": "D3AE_Primary, F3A_Focus"
    }
    
    result = client._make_request("POST", "/events", event_data)
    print(f"Created event: {result}")
    return result.get("event_id") if result else None

event_id = create_event()
# Output: Created event: {'status': 'ok', 'event_id': 'evt_a1b2c3d4e5f6'}
```

### Record Live Event Metrics

```python
def record_event_metrics(event_id, leads_generated=0, leads_qualified=0, 
                         conversions=0, roi=0, engagement_rate=0):
    """Record real-time metrics during event execution."""
    metrics_data = {
        "event_id": event_id,
        "date": datetime.now().date().isoformat(),
        "leads_generated": leads_generated,
        "leads_qualified": leads_qualified,
        "conversion_count": conversions,
        "cost_per_lead": 50000 / max(leads_generated, 1),
        "roi": roi,
        "engagement_rate": engagement_rate
    }
    
    result = client._make_request("POST", f"/events/{event_id}/metrics", metrics_data)
    print(f"Recorded metrics: {result}")
    return result

# Example: Event starts with initial metrics
record_event_metrics(event_id, leads_generated=50, leads_qualified=30, 
                     conversions=2, roi=0.8, engagement_rate=0.45)

# Later in day: Update with cumulative metrics
record_event_metrics(event_id, leads_generated=150, leads_qualified=95, 
                     conversions=12, roi=1.45, engagement_rate=0.63)
```

### Capture TA Technician Feedback

```python
def capture_survey_feedback(event_id, lead_id, technician_id, 
                           effectiveness_rating, feedback):
    """Capture survey feedback from TA technician."""
    survey_data = {
        "event_id": event_id,
        "lead_id": lead_id,
        "technician_id": technician_id,
        "effectiveness_rating": effectiveness_rating,
        "feedback": feedback
    }
    
    result = client._make_request("POST", f"/events/{event_id}/survey", survey_data)
    print(f"Survey recorded: {result}")
    return result

# Example surveys throughout the day
capture_survey_feedback(
    event_id=event_id,
    lead_id="lead_001",
    technician_id="tech_001",
    effectiveness_rating=4,
    feedback="Strong turnout. HS graduates responsive to tech career messaging."
)

capture_survey_feedback(
    event_id=event_id,
    lead_id="lead_002",
    technician_id="tech_002",
    effectiveness_rating=5,
    feedback="Excellent engagement. D3AE targeting approach working perfectly."
)
```

### Get Event Metrics

```python
def get_event_metrics(event_id):
    """Retrieve event metrics."""
    result = client._make_request("GET", f"/events/{event_id}/metrics")
    if result:
        print(f"Event metrics for {event_id}:")
        for metric in result.get("metrics", []):
            print(f"  Date: {metric['date']}")
            print(f"    Leads: {metric['leads_generated']}")
            print(f"    Conversions: {metric['conversion_count']}")
            print(f"    ROI: {metric['roi']}")
    return result

get_event_metrics(event_id)
```

### Get Event Feedback Summary

```python
def get_event_feedback(event_id):
    """Get aggregated technician feedback."""
    result = client._make_request("GET", f"/events/{event_id}/feedback")
    if result:
        print(f"Feedback summary for {event_id}:")
        for fb in result.get("feedback", []):
            print(f"  Technician: {fb['technician_id']}")
            print(f"    Rating: {fb['effectiveness_rating']}/5")
            print(f"    Feedback: {fb['feedback']}")
    return result

get_event_feedback(event_id)
```

---

## Recruiting Funnel Management

### Get Funnel Stages

```python
def get_funnel_stages():
    """Get all recruiting funnel stages."""
    result = client._make_request("GET", "/funnel/stages")
    if result:
        print("Recruiting Funnel Stages:")
        for stage in result.get("stages", []):
            print(f"  {stage['sequence_order']}. {stage['stage_name']} " 
                  f"(ID: {stage['stage_id']})")
            print(f"     {stage['description']}")
    return result

get_funnel_stages()
```

### Record Lead Progression

```python
def move_lead_through_funnel(lead_id, from_stage, to_stage, 
                            reason="", technician_id=""):
    """Move a lead between funnel stages."""
    transition_data = {
        "lead_id": lead_id,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "transition_reason": reason,
        "technician_id": technician_id
    }
    
    result = client._make_request("POST", "/funnel/transition", transition_data)
    print(f"Lead {lead_id} transitioned: {from_stage} → {to_stage}")
    return result

# Example: Process leads through funnel
leads = [
    {"id": "lead_001", "asvab_score": 67},
    {"id": "lead_002", "asvab_score": 72},
    {"id": "lead_003", "asvab_score": 45},
]

for lead in leads:
    if lead["asvab_score"] >= 50:
        move_lead_through_funnel(
            lead_id=lead["id"],
            from_stage="lead",
            to_stage="qualified",
            reason=f"ASVAB score: {lead['asvab_score']}",
            technician_id="tech_001"
        )
        
        if lead["asvab_score"] >= 70:
            move_lead_through_funnel(
                lead_id=lead["id"],
                from_stage="qualified",
                to_stage="engaged",
                reason="High-quality prospect for officer track",
                technician_id="tech_001"
            )
```

### Get Funnel Metrics

```python
def get_funnel_metrics():
    """Get funnel conversion rates and stage distribution."""
    result = client._make_request("GET", "/funnel/metrics")
    if result:
        distribution = result.get("stage_distribution", {})
        print("Funnel Metrics:")
        print("Stage Distribution:")
        for stage, count in distribution.items():
            print(f"  {stage}: {count} leads")
    return result

get_funnel_metrics()
```

---

## Project Management

### Create Event Planning Project

```python
def create_project(event_id, name, start_date, target_date, owner_id):
    """Create event planning project."""
    project_data = {
        "name": name,
        "event_id": event_id,
        "start_date": start_date,
        "target_date": target_date,
        "owner_id": owner_id,
        "objectives": "Generate qualified leads and convert per targeting profile",
        "success_criteria": "Achieve 80%+ of ROI target"
    }
    
    result = client._make_request("POST", "/projects", project_data)
    print(f"Created project: {result}")
    return result.get("project_id") if result else None

project_id = create_project(
    event_id=event_id,
    name="Fort Jackson Job Fair Planning",
    start_date="2025-01-15",
    target_date="2025-02-15",
    owner_id="commander_001"
)
```

### Create Project Tasks

```python
def create_task(project_id, title, description, assigned_to, due_date, priority):
    """Create a project task."""
    task_data = {
        "project_id": project_id,
        "title": title,
        "description": description,
        "assigned_to": assigned_to,
        "due_date": due_date,
        "priority": priority
    }
    
    result = client._make_request("POST", f"/projects/{project_id}/tasks", task_data)
    print(f"Created task: {title}")
    return result

# Create timeline of tasks
tasks_timeline = [
    {
        "title": "Finalize Targeting Profile",
        "description": "Define D3AE/F3A parameters",
        "assigned_to": "targeting_team",
        "due_date": "2025-01-20",
        "priority": "high"
    },
    {
        "title": "Prepare Marketing Materials",
        "description": "Print collateral, digital assets",
        "assigned_to": "marketing_team",
        "due_date": "2025-02-01",
        "priority": "high"
    },
    {
        "title": "Train Recruiting Team",
        "description": "Conduct messaging training",
        "assigned_to": "training_lead",
        "due_date": "2025-02-10",
        "priority": "high"
    },
    {
        "title": "Event Setup",
        "description": "Install booths, test systems",
        "assigned_to": "logistics_team",
        "due_date": "2025-02-14",
        "priority": "high"
    }
]

for task in tasks_timeline:
    create_task(
        project_id=project_id,
        title=task["title"],
        description=task["description"],
        assigned_to=task["assigned_to"],
        due_date=task["due_date"],
        priority=task["priority"]
    )
```

### Get Project Timeline

```python
def get_project_timeline(project_id):
    """Get project milestones and timeline."""
    result = client._make_request("GET", f"/projects/{project_id}/timeline")
    if result:
        print(f"Project Timeline for {project_id}:")
        for milestone in result.get("milestones", []):
            status = "✓ COMPLETE" if milestone["actual_date"] else "⏳ PENDING"
            print(f"  {milestone['name']} - Target: {milestone['target_date']} [{status}]")
    return result

get_project_timeline(project_id)
```

---

## M-IPOE Framework

### Document Intent Phase

```python
def create_mipoe_intent(event_id, strategic_objective, target_demographic, 
                       commander_intent, owner_id):
    """Document M-IPOE Intent phase."""
    mipoe_data = {
        "event_id": event_id,
        "phase": "intent",
        "content": {
            "strategic_objective": strategic_objective,
            "target_demographic": target_demographic,
            "commander_intent": commander_intent,
            "timeline": "Q1 2025"
        },
        "owner_id": owner_id
    }
    
    result = client._make_request("POST", "/mipoe", mipoe_data)
    print(f"Created M-IPOE Intent: {result}")
    return result.get("mipoe_id") if result else None

mipoe_intent_id = create_mipoe_intent(
    event_id=event_id,
    strategic_objective="Increase officer acquisition in underrepresented markets",
    target_demographic="HS graduates 18-28, tech-interested, SE region",
    commander_intent="Apply D3AE principles to focus on high-propensity demographics",
    owner_id="commander_001"
)
```

### Document Plan Phase

```python
def create_mipoe_plan(event_id, event_type, venue, budget, team_size, 
                     targeting_profile, expected_leads, owner_id):
    """Document M-IPOE Plan phase."""
    mipoe_data = {
        "event_id": event_id,
        "phase": "plan",
        "content": {
            "event_type": event_type,
            "venue": venue,
            "budget": budget,
            "team_size": team_size,
            "targeting_profile": targeting_profile,
            "expected_leads": expected_leads,
            "conversion_target": 0.08
        },
        "owner_id": owner_id
    }
    
    result = client._make_request("POST", "/mipoe", mipoe_data)
    print(f"Created M-IPOE Plan: {result}")
    return result

create_mipoe_plan(
    event_id=event_id,
    event_type="In-Person Job Fair",
    venue="Fort Jackson, SC",
    budget=50000,
    team_size=12,
    targeting_profile="D3AE_Primary (HS grads, tech careers), F3A focus",
    expected_leads=150,
    owner_id="planner_001"
)
```

### Document Execute Phase

```python
def create_mipoe_execute(event_id, actual_leads, actual_conversions, 
                        actual_roi, notes, owner_id):
    """Document M-IPOE Execute phase (during event)."""
    mipoe_data = {
        "event_id": event_id,
        "phase": "execute",
        "content": {
            "actual_leads": actual_leads,
            "actual_conversions": actual_conversions,
            "actual_roi": actual_roi,
            "real_time_adjustments": notes
        },
        "owner_id": owner_id
    }
    
    result = client._make_request("POST", "/mipoe", mipoe_data)
    print(f"Recorded M-IPOE Execute: {result}")
    return result

create_mipoe_execute(
    event_id=event_id,
    actual_leads=150,
    actual_conversions=12,
    actual_roi=1.45,
    notes="Targeting messaging performed better than expected. Consider F3A increase.",
    owner_id="event_lead"
)
```

### Document Evaluate Phase

```python
def create_mipoe_evaluate(event_id, achievements, challenges, lessons_learned, 
                         recommendations, owner_id):
    """Document M-IPOE Evaluate phase (post-event analysis)."""
    mipoe_data = {
        "event_id": event_id,
        "phase": "evaluate",
        "content": {
            "achievements": achievements,
            "challenges": challenges,
            "lessons_learned": lessons_learned,
            "recommendations": recommendations
        },
        "owner_id": owner_id
    }
    
    result = client._make_request("POST", "/mipoe", mipoe_data)
    print(f"Recorded M-IPOE Evaluate: {result}")
    return result

create_mipoe_evaluate(
    event_id=event_id,
    achievements=[
        "Generated 150 leads (100% of target)",
        "Achieved 1.45x ROI (target was 1.4x)",
        "95 qualified leads (63% qualification rate)"
    ],
    challenges=[
        "Logistical delays in morning setup",
        "Weather affected outdoor activities"
    ],
    lessons_learned=[
        "D3AE targeting was highly effective",
        "HS grad messaging resonated 4.5x better than general messaging",
        "Tech career focus attracted better-quality leads"
    ],
    recommendations=[
        "Expand D3AE targeting to 5 additional CBSA markets",
        "Increase budget for tech career messaging 30%",
        "Replicate this format for Q2 events"
    ],
    owner_id="commander_001"
)
```

---

## D3AE/F3A Targeting Profiles

### Create Targeting Profile

```python
def create_targeting_profile(event_id, age_min, age_max, education_level,
                            locations, message_themes, contact_frequency,
                            conversion_target, cost_per_lead_target):
    """Create D3AE/F3A targeting profile."""
    profile_data = {
        "event_id": event_id,
        "target_age_min": age_min,
        "target_age_max": age_max,
        "target_education_level": education_level,
        "target_locations": locations,
        "message_themes": message_themes,
        "contact_frequency": contact_frequency,
        "conversion_target": conversion_target,
        "cost_per_lead_target": cost_per_lead_target
    }
    
    result = client._make_request("POST", "/targeting-profiles", profile_data)
    print(f"Created targeting profile: {result}")
    return result.get("profile_id") if result else None

# D3AE (Demographics, Dialect, Attitude, Education)
# F3A (Frequency, Forums, Format/Formats)
profile_id = create_targeting_profile(
    event_id=event_id,
    age_min=18,
    age_max=28,
    education_level="High School, Some College",
    locations="37980,41884,35980",  # CBSA codes for high-density markets
    message_themes="career_growth,education_benefits,technology,personal_development",
    contact_frequency=3,
    conversion_target=0.12,
    cost_per_lead_target=333.33
)
```

### Get Targeting Profile

```python
def get_targeting_profile(profile_id):
    """Retrieve targeting profile."""
    result = client._make_request("GET", f"/targeting-profiles/{profile_id}")
    if result:
        print(f"Targeting Profile {profile_id}:")
        print(f"  Age: {result['target_age_min']}-{result['target_age_max']}")
        print(f"  Education: {result['target_education_level']}")
        print(f"  Locations (CBSA): {result['target_locations']}")
        print(f"  Messaging: {result['message_themes']}")
        print(f"  Contact Frequency: {result['contact_frequency']}x")
        print(f"  Conversion Target: {result['conversion_target']*100}%")
    return result

get_targeting_profile(profile_id)
```

---

## Forecasting & Analytics

### Generate Quarterly Forecast

```python
def generate_forecast(quarter, year):
    """Generate forecast for a quarter."""
    forecast_data = {
        "quarter": quarter,
        "year": year
    }
    
    result = client._make_request("POST", "/forecasts/generate", forecast_data)
    if result:
        print(f"Generated Forecast for Q{quarter} {year}:")
        print(f"  Projected Leads: {result['projected_leads']}")
        print(f"  Projected Conversions: {result['projected_conversions']}")
        print(f"  Projected ROI: {result['projected_roi']:.2f}x")
        print(f"  Confidence: {result['confidence_level']*100:.0f}%")
    return result

# Generate forecasts for the year
for quarter in range(1, 5):
    generate_forecast(quarter, 2025)
```

### Get Quarterly Forecast

```python
def get_forecast(quarter, year):
    """Retrieve forecast for a specific quarter."""
    result = client._make_request("GET", f"/forecasts/{quarter}/{year}")
    if result:
        print(f"Q{result['quarter']} {result['year']} Forecast:")
        print(f"  Leads: {result['projected_leads']}")
        print(f"  Conversions: {result['projected_conversions']}")
        print(f"  ROI: {result['projected_roi']:.2f}x")
        print(f"  Confidence: {result['confidence_level']*100:.0f}%")
    return result

get_forecast(1, 2025)
```

### Get Dashboard Snapshot

```python
def get_dashboard_snapshot():
    """Get comprehensive dashboard snapshot."""
    result = client._make_request("GET", "/analytics/dashboard")
    if result:
        dashboard = result.get("dashboard", {})
        print("Dashboard Snapshot:")
        print(f"  Total Events: {dashboard['total_events']}")
        print(f"  Total Leads: {dashboard['total_leads']}")
        print(f"  Total Conversions: {dashboard['total_conversions']}")
        print(f"  Conversion Rate: {dashboard['conversion_rate']*100:.1f}%")
        print(f"  Avg Cost per Lead: ${dashboard['avg_cost_per_lead']:.2f}")
        print(f"  Avg ROI: {dashboard['avg_roi']:.2f}x")
    return result

get_dashboard_snapshot()
```

---

## Complete Event Workflow

Here's a complete workflow from planning through evaluation:

```python
def complete_event_workflow():
    """Complete event workflow from planning through evaluation."""
    
    print("=" * 50)
    print("TAAIP EVENT WORKFLOW")
    print("=" * 50)
    
    # 1. PLANNING PHASE
    print("\n1. PLANNING - Create Event & Targeting")
    event_id = create_event()
    profile_id = create_targeting_profile(
        event_id=event_id,
        age_min=18, age_max=28,
        education_level="High School, Some College",
        locations="37980,41884",
        message_themes="career_growth,education_benefits,technology",
        contact_frequency=3,
        conversion_target=0.12,
        cost_per_lead_target=333.33
    )
    project_id = create_project(
        event_id=event_id,
        name="Event Planning Project",
        start_date="2025-01-15",
        target_date="2025-02-15",
        owner_id="commander_001"
    )
    create_mipoe_intent(
        event_id=event_id,
        strategic_objective="Increase officer acquisition",
        target_demographic="HS grads, tech-focused",
        commander_intent="Apply D3AE targeting principles",
        owner_id="commander_001"
    )
    
    # 2. EXECUTION PHASE
    print("\n2. EXECUTION - Record Live Metrics")
    record_event_metrics(event_id, leads_generated=100, leads_qualified=65,
                        conversions=8, roi=1.2, engagement_rate=0.55)
    capture_survey_feedback(event_id, "lead_001", "tech_001", 4,
                           "Strong engagement with D3AE targeting")
    move_lead_through_funnel("lead_001", "lead", "qualified",
                            "ASVAB score 70+", "tech_001")
    
    # 3. ANALYTICS PHASE
    print("\n3. ANALYTICS - View Results")
    get_event_metrics(event_id)
    get_funnel_metrics()
    get_dashboard_snapshot()
    
    # 4. EVALUATION PHASE
    print("\n4. EVALUATION - Document Lessons Learned")
    create_mipoe_evaluate(
        event_id=event_id,
        achievements=["Hit lead target", "Strong ROI"],
        challenges=["Minor logistics delays"],
        lessons_learned=["D3AE approach highly effective"],
        recommendations=["Replicate format for Q2"],
        owner_id="commander_001"
    )
    
    # 5. FORECASTING PHASE
    print("\n5. FORECASTING - Project Q2 Results")
    generate_forecast(2, 2025)
    
    print("\n" + "=" * 50)
    print("WORKFLOW COMPLETE")
    print("=" * 50)

# Run the complete workflow
complete_event_workflow()
```

---

## Error Handling

```python
def safe_api_call(method, endpoint, data=None):
    """Safely call API with error handling."""
    try:
        if method == "GET":
            response = requests.get(f"{client.base_url}{endpoint}", 
                                  headers=client.headers)
        else:
            response = requests.post(f"{client.base_url}{endpoint}",
                                    json=data, headers=client.headers)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Resource not found: {endpoint}")
        elif e.response.status_code == 401:
            print("Authentication failed. Check API token.")
        else:
            print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    
    return None
```

---

## Next Steps

1. **Start the TAAIP service**:
   ```bash
   python taaip_service.py
   ```

2. **Run this integration guide**:
   ```bash
   python integration_examples.py
   ```

3. **Check the dashboard** at `http://localhost:3000` for real-time visualization.

4. **Monitor API logs** for insights and debugging.
