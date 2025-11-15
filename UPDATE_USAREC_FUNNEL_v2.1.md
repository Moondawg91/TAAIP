# TAAIP Update: USAREC Recruiting Funnel & Marketing Activity Tracking

**Date**: November 14, 2025  
**Version**: 2.1.0  
**Status**: Complete & Verified

---

## 🎯 What's New

### USAREC Recruiting Funnel (8 Stages)
The system now implements the official Army Recruiting Command funnel:

1. **Lead** — Raw prospect from marketing
2. **Prospect** — Qualified demographic match
3. **Appointment Made** — Recruiter meeting scheduled
4. **Appointment Conducted** — Initial recruiter meeting completed
5. **Test** — ASVAB/qualification test administered
6. **Test Pass** — Passed qualification test
7. **Physical** — Medical/physical qualification completed
8. **Enlist** — Contract signed, enlisted

### Marketing Activity Tracking
Track impressions, engagement, awareness, and activation from:
- **EMM** (Enterprise Marketing Manager)
- **iKrome** (Analytics & Attribution)
- **Vantage** (Performance Analysis)
- **G2 Report Zone** (Competitive Intelligence)
- **AIEM** (Army Integrated Enlisted Marketing)
- **USAREC Systems** (Official Databases)

---

## 📊 New Database Tables

### marketing_activities
Tracks impressions, engagement, awareness, and activation by channel/campaign:
- `activity_id` — Unique ID
- `event_id` — Associated event
- `activity_type` — social_media, email, display_ad, event, etc.
- `campaign_name` — Campaign name
- `channel` — Facebook, Instagram, Email, Google Ads, etc.
- `data_source` — emm, ikrome, vantage, g2_report_zone, aiem, usarec_systems
- `impressions` — Reach count
- `engagement_count` — Interactions
- `awareness_metric` — 0.0-1.0 awareness scale
- `activation_conversions` — Conversions from activity
- `reporting_date` — When metrics were captured

### data_source_mappings
Tracks USAREC data source integrations:
- `mapping_id` — Unique ID
- `source_system` — emm, ikrome, vantage, g2_report_zone, aiem, usarec_systems
- `source_name` — Display name
- `description` — Full description
- `last_sync` — Last sync timestamp
- `sync_status` — pending, synced, error

---

## 🔗 New API Endpoints

### Marketing Activities
```
POST   /api/v2/marketing/activities          Record marketing activity
GET    /api/v2/marketing/activities          Get activities (filter by event/source)
GET    /api/v2/marketing/analytics           Get aggregated metrics
GET    /api/v2/marketing/sources             List USAREC data sources
POST   /api/v2/marketing/sync                Sync from data source
GET    /api/v2/marketing/funnel-attribution  Attribution by funnel stage
```

---

## 📋 Quick Start

### 1. Start the service
```bash
python taaip_service.py
```

### 2. View updated funnel stages
```bash
curl http://localhost:8000/api/v2/funnel/stages
```

Output shows 8 USAREC stages (lead, prospect, appointment_made, etc.)

### 3. Record marketing activity
```bash
curl -X POST http://localhost:8000/api/v2/marketing/activities \
  -d '{
    "event_id": "evt_spring2025",
    "activity_type": "social_media",
    "campaign_name": "Spring Officer Campaign",
    "channel": "Facebook",
    "data_source": "emm",
    "impressions": 50000,
    "engagement_count": 2500,
    "awareness_metric": 0.85,
    "activation_conversions": 250,
    "reporting_date": "2025-02-15"
  }'
```

### 4. Track lead through USAREC funnel
```bash
# Lead → Prospect
curl -X POST http://localhost:8000/api/v2/funnel/transition \
  -d '{
    "lead_id": "lead_001",
    "from_stage": "lead",
    "to_stage": "prospect",
    "transition_reason": "Qualified via EMM demographics"
  }'

# Prospect → Appointment Made
curl -X POST http://localhost:8000/api/v2/funnel/transition \
  -d '{
    "lead_id": "lead_001",
    "from_stage": "prospect",
    "to_stage": "appointment_made",
    "transition_reason": "Appointment scheduled with recruiter"
  }'

# Continue through: appointment_conducted → test → test_pass → physical → enlist
```

### 5. View marketing analytics
```bash
curl http://localhost:8000/api/v2/marketing/analytics?event_id=evt_spring2025
```

### 6. See funnel attribution
```bash
curl http://localhost:8000/api/v2/marketing/funnel-attribution
```

---

## 💻 Code Examples

### Python: Track Campaign Across All Channels

```python
import requests

# Create marketing tracker
class USARECTracker:
    def __init__(self):
        self.base = "http://localhost:8000/api/v2"
    
    def track_activity(self, **kwargs):
        return requests.post(f"{self.base}/marketing/activities", json=kwargs).json()
    
    def get_analytics(self, event_id=None):
        url = f"{self.base}/marketing/analytics"
        if event_id:
            url += f"?event_id={event_id}"
        return requests.get(url).json()
    
    def get_attribution(self, source=None):
        url = f"{self.base}/marketing/funnel-attribution"
        if source:
            url += f"?data_source={source}"
        return requests.get(url).json()

# Usage
tracker = USARECTracker()

# Record Facebook activity
tracker.track_activity(
    event_id="evt_spring2025",
    activity_type="social_media",
    campaign_name="Spring Officer Campaign",
    channel="Facebook",
    data_source="emm",
    impressions=125000,
    engagement_count=5000,
    awareness_metric=0.75,
    activation_conversions=500,
    reporting_date="2025-02-15"
)

# Record Email activity
tracker.track_activity(
    event_id="evt_spring2025",
    activity_type="email",
    campaign_name="Spring Officer Campaign",
    channel="Email",
    data_source="aiem",
    impressions=75000,
    engagement_count=3500,
    awareness_metric=0.88,
    activation_conversions=350,
    reporting_date="2025-02-15"
)

# View performance
print(tracker.get_analytics("evt_spring2025"))
# Output: {
#   "total_impressions": 200000,
#   "total_engagement": 8500,
#   "avg_awareness": 0.815,
#   "total_activations": 850,
#   ...
# }

# See attribution
print(tracker.get_attribution("emm"))
```

### Sync from EMM

```python
emm_sync_data = {
    "source_system": "emm",
    "sync_data": {
        "march_campaign": {
            "type": "email",
            "campaign": "March Officer Campaign",
            "channel": "Email",
            "impressions": 100000,
            "engagement": 4500,
            "awareness": 0.90,
            "activation": 450
        },
        "social_campaign": {
            "type": "social_media",
            "campaign": "March Social",
            "channel": "Instagram",
            "impressions": 150000,
            "engagement": 7500,
            "awareness": 0.80,
            "activation": 600
        }
    }
}

response = requests.post(
    "http://localhost:8000/api/v2/marketing/sync",
    json=emm_sync_data
)

print(f"Created {response.json()['activities_created']} marketing activities from EMM")
```

---

## 📚 Documentation

- **[USAREC_RECRUITING_FUNNEL.md](USAREC_RECRUITING_FUNNEL.md)** — Comprehensive guide (new!)
- **[API_REFERENCE_V2.md](API_REFERENCE_V2.md)** — Updated with new endpoints
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — Quick command reference
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** — Updated examples

---

## ✅ Verification

```bash
# Test module import
python3 -c "import taaip_service; print('✓ Module imports successfully')"

# Start service
python taaip_service.py

# Run automated tests
python test_taaip_api.py
```

---

## 🔄 Migration from Old Funnel

If you have data using the old 8-stage funnel (lead, qualified, engaged, interested, applicant, interview, offer, contract), it will still work via the funnel_transitions table. However, new records will use the USAREC stages:

**Old Stages** → **New USAREC Stages**
- lead → lead
- qualified → prospect
- engaged → appointment_made / appointment_conducted
- interested → appointment_conducted
- applicant → test / test_pass
- interview → test_pass / physical
- offer → physical
- contract → enlist

---

## 🎯 Key Metrics You Can Now Track

### By Marketing Channel
```
impressions → engagement → awareness → activation conversions
```

### By USAREC Data Source
- EMM
- iKrome
- Vantage
- G2 Report Zone
- AIEM
- USAREC Systems

### By Funnel Stage
- Lead stage: Raw impressions and reach
- Prospect stage: Engagement and qualification
- Appointment Made: Booking conversions
- Appointment Conducted: Meeting effectiveness
- Test through Enlist: Conversion efficiency

---

## 💡 Use Cases

### 1. Campaign ROI Analysis
Track how Facebook, Email, Google Ads, and other channels drive enlistments:
```bash
GET /api/v2/marketing/funnel-attribution?data_source=emm
```

### 2. Cross-Channel Attribution
See which channels contribute most to each funnel stage:
```bash
GET /api/v2/marketing/funnel-attribution
```

### 3. Marketing Performance Dashboard
Get total impressions, engagement, awareness, and activations:
```bash
GET /api/v2/marketing/analytics?event_id=evt_springfair2025
```

### 4. Data Source Sync
Automatically pull metrics from EMM, iKrome, Vantage, G2, AIEM:
```bash
POST /api/v2/marketing/sync
```

### 5. Funnel Conversion Rates
Track leads converting through each USAREC stage:
```bash
GET /api/v2/funnel/metrics
```

---

## 📊 Database Changes

### Tables Added
- `marketing_activities` — Marketing activity tracking
- `data_source_mappings` — USAREC data source configurations

### Tables Modified
- `funnel_stages` — 8 USAREC stages now auto-initialized

### Tables Unchanged
- All existing tables remain compatible (leads, events, projects, etc.)

---

## 🚀 What's Next

### Phase 2 (Planned)
- Real-time syncing from EMM API
- Attribution modeling (multi-touch attribution)
- Predictive analytics for funnel conversion
- Advanced reporting dashboards

### Phase 3 (Planned)
- iKrome integration for attribution data
- Vantage integration for channel performance
- G2 Report Zone integration for competitive intelligence
- AIEM integration for Army-wide metrics

---

## 📞 Support

**Questions about**:
- **New funnel**: See [USAREC_RECRUITING_FUNNEL.md](USAREC_RECRUITING_FUNNEL.md)
- **Marketing tracking**: See [USAREC_RECRUITING_FUNNEL.md](USAREC_RECRUITING_FUNNEL.md)
- **API endpoints**: See [API_REFERENCE_V2.md](API_REFERENCE_V2.md)
- **Quick commands**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

**Status**: ✅ Complete  
**Version**: 2.1.0  
**Date**: November 14, 2025
