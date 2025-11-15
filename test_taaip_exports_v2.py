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

AUTH_HEADERS = {"X-API-KEY": os.environ.get("EXPORT_API_TOKEN", "devtoken123")}


def test_exports_endpoints_v2():
    ev = {"name": "Export Event 2", "type": "recruiting", "location": "Test", "start_date": "2025-11-01", "end_date": "2025-11-30", "budget": 2000, "team_size": 2, "targeting_principles": "export"}
    r = client.post("/api/v2/events", json=ev)
    assert r.status_code == 200
    event_id = r.json().get("event_id")

    a = {"event_id": event_id, "activity_type": "social_media", "campaign_name": "exp2", "channel": "FB", "data_source": "emm", "impressions": 100, "engagement_count": 10, "awareness_metric": 0.6, "activation_conversions": 1, "reporting_date": "2025-11-14", "metadata": None}
    ract = client.post("/api/v2/marketing/activities", json=a)
    assert ract.status_code == 200

    ra = client.get("/api/v2/exports/activities.csv", headers=AUTH_HEADERS)
    assert ra.status_code == 200
    assert ra.headers.get("content-type", "").startswith("text/csv")
    assert "activity_id" in ra.text

    rk = client.get(f"/api/v2/exports/kpis.csv?event_id={event_id}", headers=AUTH_HEADERS)
    assert rk.status_code == 200
    assert rk.headers.get("content-type", "").startswith("text/csv")
    assert "event_id" in rk.text

    re = client.post("/api/v2/exports/run", headers=AUTH_HEADERS)
    assert re.status_code == 200
    jr = re.json()
    assert "exports" in jr and len(jr["exports"]) >= 1
