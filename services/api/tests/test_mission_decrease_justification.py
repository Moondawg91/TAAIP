from datetime import date, datetime

from fastapi.testclient import TestClient

from services.api.app import auth, main as app_module, models
from services.api.app.database import SessionLocal, engine
from services.api.app.models import Base
from services.api.app.services import mission_decrease_justification as mdj

client = TestClient(app_module.app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def _seed_user(db):
    user = db.query(models.User).filter(models.User.username == "usarec_admin").first()
    if user:
        return user
    user = models.User(username="usarec_admin", role=models.UserRole.USAREC, scope="USAREC")
    db.add(user)
    db.commit()
    return user


def _headers_for_admin():
    db = SessionLocal()
    user = _seed_user(db)
    token = auth.create_token_for_user(user)
    return {"Authorization": f"Bearer {token}"}


def test_rank_causal_factors_deterministic_tie_break():
    candidates = [
        {
            "factor_id": "z_factor",
            "label": "Z",
            "impact": 0.6,
            "source": "unit",
            "recency_score": 0.5,
            "agreement_tokens": ["shared"],
            "rationale": "z",
        },
        {
            "factor_id": "a_factor",
            "label": "A",
            "impact": 0.6,
            "source": "unit",
            "recency_score": 0.5,
            "agreement_tokens": ["shared"],
            "rationale": "a",
        },
    ]

    ranked = mdj.rank_causal_factors(candidates)

    # Weighted scores tie; deterministic ordering should use factor_id asc.
    assert ranked[0]["factor_id"] == "a_factor"
    assert ranked[1]["factor_id"] == "z_factor"


def test_generate_commander_narrative_fallback_when_no_factors():
    narrative = mdj.generate_commander_narrative(
        mission_delta_pct=-0.2,
        factors=[],
        recommendation={},
        accountability_brief={},
    )
    assert "Signal coverage is limited" in narrative


def test_decision_output_generate_and_retrieve(monkeypatch):
    headers = _headers_for_admin()
    fixed_now = datetime(2026, 1, 1, 12, 0, 0)

    def _fake_generate(db, org_id, period_start, period_end, baseline_start=None, baseline_end=None, include_evidence=True, force_refresh=False):
        return {
            "request_id": "mdj-fixed-001",
            "traceability_id": "trace-mdj-fixed-001",
            "generated_at": fixed_now.isoformat() + "Z",
            "scope": {"scope_type": "CO", "scope_value": "1A1"},
            "mission_delta_summary": {
                "current_period": {"start": "2026-01-01", "end": "2026-01-31", "mission_total": 10.0, "sample_count": 1},
                "baseline_period": {"start": "2025-12-01", "end": "2025-12-31", "mission_total": 20.0, "sample_count": 1},
                "delta": -10.0,
                "delta_pct": -0.5,
            },
            "causal_factors": [],
            "recommendations": [],
            "accountability_brief": {"classification": "insufficient_data"},
            "loe_summary": {"rag": "amber"},
            "confidence": {"score": 0.4, "band": "low", "completeness": 0.5, "agreement": 0.0},
            "executive_summary": ["summary"],
            "commander_narrative": "narrative",
            "one_slide_payload": {"title": "Mission Decrease Justification"},
            "assumptions_and_limits": ["assumption"],
            "evidence": [],
            "force_refresh_used": force_refresh,
        }

    monkeypatch.setattr(mdj, "generate_mission_decrease_justification", _fake_generate)
    monkeypatch.setattr(mdj, "get_cached_justification", lambda request_id: _fake_generate(None, "1A1", date(2026, 1, 1), date(2026, 1, 31)))

    payload = {
        "org_id": "1A1",
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
        "include_evidence": True,
        "force_refresh": False,
    }

    resp = client.post("/api/v2/decision-output/mission-decrease-justification", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json().get("data", {})
    assert data.get("request_id") == "mdj-fixed-001"
    assert data.get("confidence", {}).get("band") == "low"

    fetch = client.get("/api/v2/decision-output/mission-decrease-justification/mdj-fixed-001", headers=headers)
    assert fetch.status_code == 200
    fetched = fetch.json().get("data", {})
    assert fetched.get("traceability_id") == "trace-mdj-fixed-001"


def test_decision_output_structured_error(monkeypatch):
    headers = _headers_for_admin()

    def _boom(*args, **kwargs):
        raise mdj.DecisionOutputError(
            code="invalid_request",
            message="bad payload",
            details={"field": "period_start"},
        )

    monkeypatch.setattr(mdj, "generate_mission_decrease_justification", _boom)

    payload = {
        "org_id": "1A1",
        "period_start": "2026-02-01",
        "period_end": "2026-01-01",
    }

    resp = client.post("/api/v2/decision-output/mission-decrease-justification", json=payload, headers=headers)
    assert resp.status_code == 400
    detail = resp.json().get("detail", {})
    assert detail.get("code") == "invalid_request"
    assert detail.get("message") == "bad payload"
