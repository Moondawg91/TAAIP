from fastapi import APIRouter, Depends
from services.api.app.db import get_db_conn
from services.api.app.routers.rbac import get_current_user
from datetime import datetime
import uuid

router = APIRouter(prefix="/v1")


@router.post("/ingestLead")
async def ingest_lead(payload: dict, user: dict = Depends(get_current_user)):
    conn = get_db_conn()
    cur = conn.cursor()
    lid = payload.get("lead_id") or ("lead_" + uuid.uuid4().hex[:10])
    cur.execute(
        "INSERT OR REPLACE INTO leads(lead_id,first_name,last_name,email,phone,source,age,education_level,cbsa_code,campaign_source,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            lid,
            payload.get("first_name"),
            payload.get("last_name"),
            payload.get("email"),
            payload.get("phone"),
            payload.get("source"),
            payload.get("age"),
            payload.get("education_level"),
            payload.get("cbsa_code"),
            payload.get("campaign_source"),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "lead_id": lid}


@router.post("/scoreLead")
async def score_lead(payload: dict):
    """Lightweight scoring endpoint used by the lightweight frontend demo.

    Returns a mocked score and recommendation derived from simple heuristics.
    """
    # Basic heuristics for demo purposes
    age = int(payload.get('age') or 30)
    education = (payload.get('education_level') or '').lower()
    campaign = payload.get('campaign_source') or ''
    base = 50
    # age influence
    if age < 25:
        base += 10
    elif age >= 45:
        base -= 5
    # education
    if 'masters' in education or 'phd' in education:
        base += 10
    elif 'high' in education:
        base -= 5
    # campaign boost
    if campaign:
        base += 5
    score = max(0, min(100, base))
    prob = round(score / 100.0, 3)
    rec = 'Recommend contact' if score >= 60 else 'Monitor and nurture'
    return {
        'lead_id': payload.get('lead_id') or f"lead-{int(datetime.utcnow().timestamp())}",
        'score': score,
        'predicted_probability': prob,
        'recommendation': rec,
    }
