import os
import json
from taaip_service import app, init_db
from fastapi.testclient import TestClient

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "taaip.sqlite3")
# Ensure clean DB for tests
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception:
        pass

init_db()
client = TestClient(app)


def test_ai_train_and_predict():
    # Train model (uses mock if scikit-learn not installed)
    r = client.post("/api/v2/ai/train", json={})
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "accuracy" in data

    # Predict on sample leads
    leads_payload = {
        "leads": [
            {"lead_id": "t_lead_1", "age": 22, "propensity_score": 0.7, "web_activity": 50, "engagement_count": 4, "education_level": "HS"},
            {"lead_id": "t_lead_2", "age": 29, "propensity_score": 0.3, "web_activity": 10, "engagement_count": 1, "education_level": "College"}
        ]
    }
    r2 = client.post("/api/v2/ai/predict", json=leads_payload)
    assert r2.status_code == 200
    p = r2.json()
    assert p.get("status") == "ok"
    assert isinstance(p.get("predictions"), list)
    assert len(p.get("predictions")) == 2


def test_lms_enroll_and_progress_and_stats():
    # Get available courses
    r = client.get("/api/v2/lms/courses")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("count", 0) >= 1

    # Get stats before enrollments
    s = client.get("/api/v2/lms/stats")
    assert s.status_code == 200
    stats = s.json().get("stats", {})
    # Stats should include total_courses
    assert "total_courses" in stats

    # Enroll a user
    enroll_payload = {"user_id": "test_user_1", "course_id": "usarec-101"}
    er = client.post("/api/v2/lms/enroll", json=enroll_payload)
    assert er.status_code == 200
    enr = er.json()
    assert enr.get("status") == "ok"
    enrollment_id = enr.get("enrollment_id")
    assert enrollment_id

    # Get user enrollments
    ur = client.get(f"/api/v2/lms/enrollments/{enroll_payload['user_id']}")
    assert ur.status_code == 200
    udata = ur.json()
    assert udata.get("status") == "ok"
    assert udata.get("count") >= 1

    # Update progress
    progress_payload = {"enrollment_id": enrollment_id if isinstance(enrollment_id, str) else enrollment_id.get('enrollment_id'), "progress_percent": 75}
    pr = client.put("/api/v2/lms/progress", json=progress_payload)
    assert pr.status_code == 200
    pdat = pr.json()
    assert pdat.get("status") == "ok"

    # Check stats after enrollment
    s2 = client.get("/api/v2/lms/stats")
    assert s2.status_code == 200
    stats2 = s2.json().get("stats", {})
    assert stats2.get("total_enrollments", 0) >= 1
