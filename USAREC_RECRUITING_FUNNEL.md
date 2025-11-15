# USAREC Recruiting Funnel & Marketing Activity Tracking

## Overview

TAAIP now fully supports the **USAREC recruiting funnel** with 8 stages and integrated **marketing activity tracking** from all major Army recruiting data sources.

---

## 🎯 USAREC Recruiting Funnel (8 Stages)

The system now implements the official Army Recruiting Command funnel:

| Stage | Name | Description | Key Activities |
|-------|------|-------------|-----------------|
| 1 | **Lead** | Raw prospect, initial capture from marketing channels | Marketing impression, first click, lead gen form submission |
| 2 | **Prospect** | Qualified demographic match, engaged with content | Content consumption, email engagement, social interaction |
| 3 | **Appointment Made** | Scheduled appointment with recruiter | Calendar booking, confirmation sent, reminder sent |
| 4 | **Appointment Conducted** | Met with recruiter, initial discussion completed | Meeting notes, recruiter assessment, fit evaluation |
| 5 | **Test** | ASVAB or qualification test administered | Test scheduled, test date confirmed, administered |
| 6 | **Test Pass** | Passed ASVAB with qualifying score | Score verified, eligibility confirmed |
| 7 | **Physical** | Medical examination and physical qualification completed | Physical exam scheduled, exam conducted, results reviewed |
| 8 | **Enlist** | Contract signed, enlisted into service | Contract prepared, signed, enlisted confirmed |

### Track Progression

```bash
# Get all funnel stages
curl http://localhost:8000/api/v2/funnel/stages

# Response includes 8 USAREC stages:
# lead, prospect, appointment_made, appointment_conducted, 
# test, test_pass, physical, enlist
```

### Record Lead Movement

```bash
# Move lead through funnel
curl -X POST http://localhost:8000/api/v2/funnel/transition \
  -d '{
    "lead_id": "lead_001",
    "from_stage": "lead",
    "to_stage": "prospect",
    "transition_reason": "Qualified age/education via EMM",
    "technician_id": "recruiter_001"
  }'
```

---

## 📊 Marketing Activity Tracking

Track impressions, engagement, awareness, and activation across all USAREC data sources.

### Supported USAREC Data Sources

| System | Full Name | Purpose | Data Captured |
|--------|-----------|---------|---------------|
| **EMM** | Enterprise Marketing Manager | USAREC lead management system | Leads, impressions, engagement by campaign |
| **iKrome** | iKrome Platform | Advanced analytics and attribution | Multi-touch attribution, conversion paths |
| **Vantage** | Vantage | Marketing performance analysis | Channel performance, ROI, audience metrics |
| **G2 Report Zone** | G2 Report Zone | Competitive intelligence | Market trends, competitor activity, insights |
| **AIEM** | Army Integrated Enlisted Marketing | Army-wide enlisted marketing coordination | Army-level campaigns, cross-service metrics |
| **USAREC Systems** | USAREC Databases | Official USAREC recruiting data | Recruits, conversions, funnel data |

### Get Available Data Sources

```bash
curl http://localhost:8000/api/v2/marketing/sources

# Response
{
  "status": "ok",
  "sources": [
    {
      "mapping_id": "map_1",
      "source_system": "emm",
      "source_name": "EMM",
      "description": "Enterprise Marketing Manager - USAREC lead management",
      "last_sync": null,
      "sync_status": "pending"
    },
    {
      "mapping_id": "map_2",
      "source_system": "ikrome",
      "source_name": "iKrome",
      "description": "Advanced analytics and attribution platform",
      "last_sync": null,
      "sync_status": "pending"
    },
    ...
  ]
}
```

### Record Marketing Activity

Track impressions, engagement, awareness, and activation metrics:

```bash
curl -X POST http://localhost:8000/api/v2/marketing/activities \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_springfair2025",
    "activity_type": "social_media",
    "campaign_name": "Spring Officer Campaign 2025",
    "channel": "Facebook",
    "data_source": "emm",
    "impressions": 50000,
    "engagement_count": 2500,
    "awareness_metric": 0.85,
    "activation_conversions": 250,
    "reporting_date": "2025-02-15"
  }'

# Response
{
  "status": "ok",
  "activity_id": "mkt_a1b2c3d4e5f6"
}
```

### Track Marketing Metrics

Get aggregated marketing performance:

```bash
# By event
curl "http://localhost:8000/api/v2/marketing/analytics?event_id=evt_springfair2025"

# All events
curl http://localhost:8000/api/v2/marketing/analytics

# Response
{
  "status": "ok",
  "total_impressions": 250000,
  "total_engagement": 12500,
  "avg_awareness": 0.82,
  "total_activations": 1250,
  "sources_count": 6,
  "channels_count": 8
}
```

### Get Marketing Activities

```bash
# All activities
curl http://localhost:8000/api/v2/marketing/activities

# By event
curl "http://localhost:8000/api/v2/marketing/activities?event_id=evt_springfair2025"

# By data source
curl "http://localhost:8000/api/v2/marketing/activities?data_source=emm"

# Response
{
  "status": "ok",
  "count": 15,
  "activities": [
    {
      "activity_id": "mkt_a1b2c3d4e5f6",
      "event_id": "evt_springfair2025",
      "activity_type": "social_media",
      "campaign_name": "Spring Officer Campaign 2025",
      "channel": "Facebook",
      "data_source": "emm",
      "impressions": 50000,
      "engagement_count": 2500,
      "awareness_metric": 0.85,
      "activation_conversions": 250,
      "reporting_date": "2025-02-15",
      "created_at": "2025-02-15T10:30:00"
    }
  ]
}
```

---

## 🔄 Sync USAREC Data Sources

Automatically sync data from EMM, iKrome, Vantage, G2, AIEM, and USAREC systems:

```bash
curl -X POST http://localhost:8000/api/v2/marketing/sync \
  -H "Content-Type: application/json" \
  -d '{
    "source_system": "emm",
    "sync_data": {
      "spring_campaign": {
        "type": "email",
        "campaign": "Spring 2025 Officer Campaign",
        "channel": "Email",
        "impressions": 75000,
        "engagement": 3500,
        "awareness": 0.88,
        "activation": 350
      },
      "facebook_campaign": {
        "type": "social_media",
        "campaign": "Facebook Spring Campaign",
        "channel": "Facebook",
        "impressions": 125000,
        "engagement": 5000,
        "awareness": 0.75,
        "activation": 500
      }
    }
  }'

# Response
{
  "status": "ok",
  "source": "emm",
  "activities_created": 2,
  "sync_timestamp": "2025-02-15T10:35:00"
}
```

---

## 📈 Funnel Attribution Analysis

See how marketing activities drive funnel progression:

```bash
# Attribution by all sources
curl http://localhost:8000/api/v2/marketing/funnel-attribution

# Attribution by specific data source
curl "http://localhost:8000/api/v2/marketing/funnel-attribution?data_source=emm"

# Response
{
  "status": "ok",
  "attribution": [
    {
      "stage": "Lead",
      "leads_in_stage": 5000,
      "impressions": 250000,
      "engagement": 12500,
      "awareness": 0.82,
      "activations": 1250
    },
    {
      "stage": "Prospect",
      "leads_in_stage": 1250,
      "impressions": 150000,
      "engagement": 8500,
      "awareness": 0.88,
      "activations": 850
    },
    {
      "stage": "Appointment Made",
      "leads_in_stage": 850,
      "impressions": 100000,
      "engagement": 6000,
      "awareness": 0.92,
      "activations": 600
    },
    {
      "stage": "Appointment Conducted",
      "leads_in_stage": 600,
      "impressions": 75000,
      "engagement": 4500,
      "awareness": 0.94,
      "activations": 450
    },
    {
      "stage": "Test",
      "leads_in_stage": 450,
      "impressions": 50000,
      "engagement": 3000,
      "awareness": 0.96,
      "activations": 300
    },
    {
      "stage": "Test Pass",
      "leads_in_stage": 300,
      "impressions": 40000,
      "engagement": 2400,
      "awareness": 0.97,
      "activations": 240
    },
    {
      "stage": "Physical",
      "leads_in_stage": 240,
      "impressions": 30000,
      "engagement": 1800,
      "awareness": 0.98,
      "activations": 180
    },
    {
      "stage": "Enlist",
      "leads_in_stage": 180,
      "impressions": 25000,
      "engagement": 1500,
      "awareness": 0.99,
      "activations": 180
    }
  ]
}
```

---

## 🎓 Marketing Activity Types

Supported activity types for categorization:

- **social_media** — Facebook, Instagram, TikTok, YouTube, LinkedIn campaigns
- **email** — Email marketing, newsletter campaigns
- **display_ad** — Google Ads, programmatic display advertising
- **event** — In-person events, career fairs, campus visits
- **referral** — Word-of-mouth, employee referrals, influencer recommendations
- **organic** — SEO, organic search, natural discovery
- **video** — Video marketing, YouTube campaigns
- **mobile** — Mobile app, SMS campaigns
- **partnership** — Partnership campaigns, co-marketing

---

## 💼 Integration Examples

### Example 1: Track Spring Campaign Across All Channels

```python
import requests

class USARECMarketingTracker:
    def __init__(self, base_url="http://localhost:8000/api/v2"):
        self.base_url = base_url
    
    def track_campaign(self, event_id, campaign_data):
        """Track all marketing activities for a campaign."""
        activities = []
        
        for channel, metrics in campaign_data.items():
            response = requests.post(
                f"{self.base_url}/marketing/activities",
                json={
                    "event_id": event_id,
                    "activity_type": metrics["type"],
                    "campaign_name": metrics["campaign"],
                    "channel": channel,
                    "data_source": metrics["source"],
                    "impressions": metrics.get("impressions", 0),
                    "engagement_count": metrics.get("engagement", 0),
                    "awareness_metric": metrics.get("awareness", 0.0),
                    "activation_conversions": metrics.get("activations", 0),
                    "reporting_date": metrics["date"]
                }
            )
            activities.append(response.json())
        
        return activities
    
    def get_campaign_performance(self, event_id):
        """Get aggregated campaign performance."""
        response = requests.get(
            f"{self.base_url}/marketing/analytics?event_id={event_id}"
        )
        return response.json()
    
    def get_funnel_attribution(self, data_source=None):
        """Get how marketing drove funnel progression."""
        url = f"{self.base_url}/marketing/funnel-attribution"
        if data_source:
            url += f"?data_source={data_source}"
        response = requests.get(url)
        return response.json()

# Usage
tracker = USARECMarketingTracker()

# Track Spring 2025 campaign
campaign_data = {
    "Facebook": {
        "type": "social_media",
        "campaign": "Spring Officer Campaign",
        "source": "emm",
        "impressions": 125000,
        "engagement": 5000,
        "awareness": 0.75,
        "activations": 500,
        "date": "2025-02-15"
    },
    "Email": {
        "type": "email",
        "campaign": "Spring Officer Campaign",
        "source": "aiem",
        "impressions": 75000,
        "engagement": 3500,
        "awareness": 0.88,
        "activations": 350,
        "date": "2025-02-15"
    },
    "Google Ads": {
        "type": "display_ad",
        "campaign": "Spring Officer Campaign",
        "source": "vantage",
        "impressions": 200000,
        "engagement": 4000,
        "awareness": 0.70,
        "activations": 400,
        "date": "2025-02-15"
    }
}

activities = tracker.track_campaign("evt_spring2025", campaign_data)
performance = tracker.get_campaign_performance("evt_spring2025")
attribution = tracker.get_funnel_attribution()

print("Campaign Performance:")
print(f"  Total Impressions: {performance['total_impressions']:,}")
print(f"  Total Engagement: {performance['total_engagement']:,}")
print(f"  Avg Awareness: {performance['avg_awareness']:.1%}")
print(f"  Total Activations: {performance['total_activations']:,}")
```

### Example 2: Sync from EMM

```python
emm_data = {
    "source_system": "emm",
    "sync_data": {
        "q1_campaign": {
            "type": "email",
            "campaign": "Q1 2025 Campaign",
            "channel": "Email",
            "impressions": 100000,
            "engagement": 4000,
            "awareness": 0.85,
            "activation": 400
        },
        "social_campaign": {
            "type": "social_media",
            "campaign": "Q1 2025 Social",
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
    json=emm_data
)

print(f"Synced {response.json()['activities_created']} activities from EMM")
```

---

## 📋 Database Schema

### marketing_activities Table
```sql
CREATE TABLE marketing_activities (
    activity_id TEXT PRIMARY KEY,           -- Unique identifier (mkt_xxx)
    event_id TEXT,                          -- Associated event (optional)
    activity_type TEXT,                     -- Type: social_media, email, etc.
    campaign_name TEXT,                     -- Campaign name
    channel TEXT,                           -- Channel: Facebook, Instagram, Email, etc.
    data_source TEXT,                       -- EMM, iKrome, Vantage, G2, AIEM, USAREC
    impressions INTEGER DEFAULT 0,          -- Impressions (reach)
    engagement_count INTEGER DEFAULT 0,     -- Engagement count (clicks, likes, etc.)
    awareness_metric REAL DEFAULT 0.0,      -- Awareness 0.0-1.0
    activation_conversions INTEGER DEFAULT 0, -- Conversions/activations
    reporting_date TEXT,                    -- Date metrics reported
    metadata TEXT,                          -- Additional metadata (JSON)
    created_at TEXT,                        -- Creation timestamp
    updated_at TEXT                         -- Update timestamp
);
```

### data_source_mappings Table
```sql
CREATE TABLE data_source_mappings (
    mapping_id TEXT PRIMARY KEY,            -- Unique identifier (map_x)
    source_system TEXT,                     -- emm, ikrome, vantage, g2_report_zone, aiem, usarec_systems
    source_name TEXT,                       -- Display name
    description TEXT,                       -- Full description
    api_endpoint TEXT,                      -- API endpoint (if applicable)
    last_sync TEXT,                         -- Last sync timestamp
    sync_status TEXT,                       -- pending, synced, error
    created_at TEXT,                        -- Creation timestamp
    updated_at TEXT                         -- Update timestamp
);
```

---

## 🔗 Key API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/marketing/activities` | Record marketing activity |
| GET | `/api/v2/marketing/activities` | Get marketing activities |
| GET | `/api/v2/marketing/analytics` | Get aggregated metrics |
| GET | `/api/v2/marketing/sources` | List data sources |
| POST | `/api/v2/marketing/sync` | Sync from data source |
| GET | `/api/v2/marketing/funnel-attribution` | Attribution by funnel stage |
| GET | `/api/v2/funnel/stages` | Get 8 USAREC funnel stages |

---

## 🎯 Typical Workflow

1. **Create Event**:
   ```bash
   POST /api/v2/events → Returns event_id
   ```

2. **Record Marketing Activities** (throughout campaign):
   ```bash
   POST /api/v2/marketing/activities (multiple times for different channels)
   ```

3. **Track Lead Progression** (as leads move through funnel):
   ```bash
   POST /api/v2/funnel/transition (lead → prospect → appointment → test → enlist)
   ```

4. **Analyze Performance**:
   ```bash
   GET /api/v2/marketing/analytics
   GET /api/v2/marketing/funnel-attribution
   GET /api/v2/funnel/metrics
   ```

5. **Sync External Data** (from EMM, iKrome, etc.):
   ```bash
   POST /api/v2/marketing/sync
   ```

---

## 📊 Metrics Definitions

| Metric | Definition |
|--------|-----------|
| **Impressions** | Number of times content was displayed (reach) |
| **Engagement** | Clicks, shares, comments, or interactions |
| **Awareness** | Scale 0.0-1.0 measuring brand/message awareness |
| **Activation** | Conversions or actions leading to lead creation |

---

## 🚀 Next Steps

1. Start the service: `python taaip_service.py`
2. Create a test event: `POST /api/v2/events`
3. Record marketing activities: `POST /api/v2/marketing/activities`
4. Track leads through funnel: `POST /api/v2/funnel/transition`
5. View analytics: `GET /api/v2/marketing/analytics`

---

**Version**: 2.1.0 (USAREC Enhanced)  
**Status**: Production Ready  
**Last Updated**: November 2025
