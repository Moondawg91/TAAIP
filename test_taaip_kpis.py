import os
from taaip_service import app, init_db
from fastapi.testclient import TestClient

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "taaip.sqlite3")
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception:
        pass

init_db()
client = TestClient(app)


def test_kpis_basic_and_with_budget():
    # Create an event
    ev = {"name": "KPI Event", "type": "recruiting", "location": "Test", "start_date": "2025-11-01", "end_date": "2025-11-30", "budget": 10000, "team_size": 5, "targeting_principles": "test"}
    r = client.post("/api/v2/events", json=ev)
    assert r.status_code == 200
    event_id = r.json().get("event_id")

    # Add two activities with cost
    # prepare first activity payload
    # Use lower-level insertion: POST marketing activities
    a1p = {"event_id": event_id, "activity_type": "social_media", "campaign_name": "camp1", "channel": "FB", "data_source": "emm", "impressions": 1000, "engagement_count": 100, "awareness_metric": 0.5, "activation_conversions": 10, "reporting_date": "2025-11-14", "metadata": None}
    r1 = client.post("/api/v2/marketing/activities", json=a1p)
    assert r1.status_code == 200
    act1 = r1.json().get("activity_id")

    # Update activity cost directly via SQL (since API doesn't yet accept cost field)
    from taaip_service import get_db_conn
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE marketing_activities SET cost = ? WHERE activity_id = ?", (200.0, act1))
    conn.commit()

    # Create another activity
    a2p = {"event_id": event_id, "activity_type": "email", "campaign_name": "camp1", "channel": "Email", "data_source": "aiem", "impressions": 500, "engagement_count": 50, "awareness_metric": 0.7, "activation_conversions": 5, "reporting_date": "2025-11-15", "metadata": None}
    r2 = client.post("/api/v2/marketing/activities", json=a2p)
    assert r2.status_code == 200
    act2 = r2.json().get("activity_id")
    cur.execute("UPDATE marketing_activities SET cost = ? WHERE activity_id = ?", (100.0, act2))
    conn.commit()

    # Add a budget allocation for the event
    import uuid
    budget_id = f"bud_{uuid.uuid4().hex[:8]}"
    now = "2025-11-01T00:00:00"
    cur.execute("INSERT INTO budgets (budget_id, event_id, campaign_name, allocated_amount, start_date, end_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (budget_id, event_id, "camp1", 500.0, now, now, now, now))
    conn.commit()
    conn.close()

    # Request KPIs for the event
    kr = client.get(f"/api/v2/kpis?event_id={event_id}")
    assert kr.status_code == 200
    kd = kr.json()
    # Combined cost should be activity costs (200+100) + budget (500) = 800
    assert abs(kd.get("total_cost") - 800.0) < 1e-6
    assert kd.get("total_impressions") == 1500
    assert kd.get("total_engagements") == 150
    assert kd.get("total_activations") == 15
    # cpl = 800 / 15 -> rounded to 2 decimals
    assert kd.get("cpl") == round(800.0 / 15, 2)
