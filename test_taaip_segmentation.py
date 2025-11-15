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


def test_ingest_survey_and_segment():
    payload = {
        "lead_id": "lead_seg_001",
        "survey_id": "sv_001",
        "responses": {"age": "24", "interest": "tech"}
    }
    r = client.post("/api/v2/ingest/survey", json=payload)
    assert r.status_code == 200
    jr = r.json()
    assert jr.get("status") == "ok"

    # Check profile
    rp = client.get("/api/v2/segments/lead_seg_001")
    assert rp.status_code == 200
    jp = rp.json()
    assert jp.get("status") == "ok"
    assert jp.get("segments").get("age_group") == "18-24"


def test_ingest_census_and_social():
    census = {"geography_code": "12345", "attributes": {"median_income": 55000}}
    rc = client.post("/api/v2/ingest/census", json=census)
    assert rc.status_code == 200

    social = {"external_id": "tw_123", "handle": "@test", "signals": {"followers": 1200}}
    rs = client.post("/api/v2/ingest/social", json=social)
    assert rs.status_code == 200
    js = rs.json()
    assert js.get("status") == "ok"
