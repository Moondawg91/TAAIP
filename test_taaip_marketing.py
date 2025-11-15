import os
import time

# Ensure fresh DB for tests
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "taaip.sqlite3")
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception:
        pass

from taaip_service import app, init_db
init_db()

from fastapi.testclient import TestClient
client = TestClient(app)


def test_record_and_analytics():
    # Record two activities for same event across two channels
    payload1 = {
        "event_id": "evt_test_py",
        "activity_type": "social_media",
        "campaign_name": "PyTest Campaign",
        "channel": "Facebook",
        "data_source": "emm",
        "impressions": 1000,
        "engagement_count": 100,
        "awareness_metric": 0.7,
        "activation_conversions": 10,
        "reporting_date": "2025-11-14"
    }
    r1 = client.post("/api/v2/marketing/activities", json=payload1)
    assert r1.status_code == 200 and r1.json().get("status") == "ok"

    payload2 = {
        "event_id": "evt_test_py",
        "activity_type": "email",
        "campaign_name": "PyTest Campaign",
        "channel": "Email",
        "data_source": "aiem",
        "impressions": 500,
        "engagement_count": 50,
        "awareness_metric": 0.85,
        "activation_conversions": 5,
        "reporting_date": "2025-11-14"
    }
    r2 = client.post("/api/v2/marketing/activities", json=payload2)
    assert r2.status_code == 200 and r2.json().get("status") == "ok"

    # Check analytics aggregation
    ra = client.get("/api/v2/marketing/analytics?event_id=evt_test_py")
    assert ra.status_code == 200
    data = ra.json()
    assert data["total_impressions"] == 1500
    assert data["total_engagement"] == 150
    # average awareness is rounded to 2 decimals by the API
    assert data["avg_awareness"] == 0.77
    assert data["total_activations"] == 15


def test_sources_and_sync():
    # List sources
    rs = client.get("/api/v2/marketing/sources")
    assert rs.status_code == 200
    sources = rs.json().get("sources", [])
    assert len(sources) >= 1

    # Sync sample data
    sync_payload = {
        "source_system": "emm",
        "sync_data": {
            "sample_campaign": {
                "type": "email",
                "campaign": "Sync Campaign",
                "channel": "Email",
                "impressions": 200,
                "engagement": 20,
                "awareness": 0.6,
                "activation": 2
            }
        }
    }
    rsync = client.post("/api/v2/marketing/sync", json=sync_payload)
    assert rsync.status_code == 200
    jr = rsync.json()
    assert jr.get("activities_created", 0) >= 1


def test_funnel_attribution_endpoint():
    # Create a lead and move through stages to allow attribution
    lead_payload = {
        "lead_id": "lead_py_001",
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "phone": "555-0001",
        "source": "emm",
        "age": 20,
        "education_level": "High School",
        "cbsa_code": "00001",
        "campaign_source": "pytest"
    }
    rlead = client.post("/api/v1/ingestLead", json=lead_payload)
    assert rlead.status_code == 200

    # Transition lead through funnel
    t1 = client.post("/api/v2/funnel/transition", json={
        "lead_id": "lead_py_001",
        "from_stage": "lead",
        "to_stage": "prospect",
        "transition_reason": "unit test"
    })
    assert t1.status_code == 200

    # Attribution query
    attr = client.get("/api/v2/marketing/funnel-attribution?lead_id=lead_py_001")
    assert attr.status_code == 200
    j = attr.json()
    assert j.get("status") == "ok"
