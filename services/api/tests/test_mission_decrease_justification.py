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


def test_generate_commander_narrative_command_grade_shape_and_quality():
    narrative = mdj.generate_commander_narrative(
        mission_delta_pct=-0.2,
        factors=[
            {"label": "LOE health"},
            {"label": "School access penetration"},
            {"label": "Execution stalls"},
        ],
        recommended_action={"type": "decrease", "magnitude": "moderate"},
        loe_summary={"rag": "red"},
        confidence={"band": "medium"},
        accountability_brief={"classification": "execution_failure"},
    )
    sentences = [s for s in narrative.split(". ") if s.strip()]
    assert 3 <= len(sentences) <= 5
    assert "Recommendation: decrease mission output" in narrative
    assert "no rows available" not in narrative.lower()
    assert "null" not in narrative.lower()


def test_decision_output_generate_and_retrieve(monkeypatch):
    headers = _headers_for_admin()
    fixed_now = datetime(2026, 1, 1, 12, 0, 0)

    def _fake_generate(db, org_id, period_start, period_end, baseline_start=None, baseline_end=None, include_evidence=True, force_refresh=False):
        return {
            "request_id": "mdj-fixed-001",
            "traceability_id": "trace-mdj-fixed-001",
            "generated_at": fixed_now.isoformat() + "Z",
            "decision_output_name": "mission_adjustment_justification",
            "mission_adjustment_type": "mission_adjustment",
            "scope": {"scope_type": "CO", "scope_value": "1A1"},
            "mission_delta_summary": {
                "current_period": {"start": "2026-01-01", "end": "2026-01-31", "mission_total": 10.0, "sample_count": 1},
                "baseline_period": {"start": "2025-12-01", "end": "2025-12-31", "mission_total": 20.0, "sample_count": 1},
                "delta": -10.0,
                "delta_pct": -0.5,
            },
            "decision_summary": {
                "recommended_action": "decrease",
                "mission_delta": -10.0,
                "confidence_score": 0.4,
                "loe_rag": "red",
            },
            "recommended_action": {
                "type": "decrease",
                "magnitude": "significant",
                "confidence": 0.4,
                "rationale": "Performance is below baseline with degraded LOE and constrained access.",
            },
            "causal_factors": [],
            "recommendations": [
                {
                    "recommendation_id": "rec-1",
                    "trace_id": "trace-1",
                    "kind": "targeting_shift",
                    "priority": 2,
                    "title": "BN establish priority targeting coverage",
                    "owner_level": "BN",
                    "action": "Establish targeting coverage for top five schools.",
                    "expected_effect": "Improves access depth.",
                    "time_horizon": "next 14 days",
                    "rationale": "Coverage is insufficient.",
                    "linked_factors": ["school_access"],
                    "source": "targeting_expansion",
                    "timestamp": fixed_now.isoformat() + "Z",
                    "actions": ["Assign owners"],
                    "evidence_refs": ["ev-targeting-empty"],
                }
            ],
            "accountability_brief": {"classification": "insufficient_data"},
            "loe_summary": {"rag": "amber"},
            "confidence": {"score": 0.4, "band": "low", "completeness": 0.5, "agreement": 0.0},
            "confidence_explanation": "Confidence is low because signal coverage and agreement are limited.",
            "executive_summary": ["summary"],
            "commander_narrative": "narrative",
            "one_slide_payload": {
                "title": "Mission Adjustment Justification",
                "decision_summary": {"recommended_action": "decrease"},
                "confidence_explanation": "Confidence is low because signal coverage and agreement are limited.",
            },
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
    assert data.get("recommended_action", {}).get("type") == "decrease"
    assert data.get("decision_output_name") == "mission_adjustment_justification"

    alias_resp = client.post("/api/v2/decision-output/mission-adjustment-justification", json=payload, headers=headers)
    assert alias_resp.status_code == 200
    alias_data = alias_resp.json().get("data", {})
    assert alias_data.get("mission_adjustment_type") == "mission_adjustment"

    fetch = client.get("/api/v2/decision-output/mission-decrease-justification/mdj-fixed-001", headers=headers)
    assert fetch.status_code == 200
    fetched = fetch.json().get("data", {})
    assert fetched.get("traceability_id") == "trace-mdj-fixed-001"

    alias_fetch = client.get("/api/v2/decision-output/mission-adjustment-justification/mdj-fixed-001", headers=headers)
    assert alias_fetch.status_code == 200


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


def test_recommended_action_deterministic_increase_decrease_hold():
    signals = {
        "access": {"summary": {"penetration_rate": 0.7, "overall_access_status": "access_supportive"}},
    }
    ranked = [{"label": "LOE health"}, {"label": "School access penetration"}]

    inc = mdj._derive_recommended_action(
        mission_delta_pct=0.12,
        loe_summary={"rag": "green"},
        signals=signals,
        confidence={"score": 0.7},
        ranked_factors=ranked,
    )
    assert inc["type"] == "increase"

    dec = mdj._derive_recommended_action(
        mission_delta_pct=-0.14,
        loe_summary={"rag": "red"},
        signals={"access": {"summary": {"penetration_rate": 0.2, "overall_access_status": "access_constrained"}}},
        confidence={"score": 0.6},
        ranked_factors=ranked,
    )
    assert dec["type"] == "decrease"

    hold = mdj._derive_recommended_action(
        mission_delta_pct=0.01,
        loe_summary={"rag": "amber"},
        signals={"access": {"summary": {"penetration_rate": 0.45, "overall_access_status": "unknown"}}},
        confidence={"score": 0.5},
        ranked_factors=ranked,
    )
    assert hold["type"] == "hold"


def test_confidence_explanation_generation():
    low = mdj._build_confidence_explanation(
        confidence={"band": "low", "completeness": 0.30, "agreement": 0.25},
        recency_signal=0.40,
        degraded_factor_count=3,
    )
    assert low.startswith("Confidence is low")

    medium = mdj._build_confidence_explanation(
        confidence={"band": "medium", "completeness": 0.60, "agreement": 0.52},
        recency_signal=0.70,
        degraded_factor_count=2,
    )
    assert medium.startswith("Confidence is medium")

    high = mdj._build_confidence_explanation(
        confidence={"band": "high", "completeness": 0.92, "agreement": 0.80},
        recency_signal=0.90,
        degraded_factor_count=1,
    )
    assert high.startswith("Confidence is high")


def test_magnitude_classification_uses_delta_confidence_loe_and_degraded_factors():
    assert mdj._magnitude_from_delta(delta_pct=0.20, confidence_score=0.8, loe_rag="red", degraded_factor_count=3) == "significant"
    assert mdj._magnitude_from_delta(delta_pct=0.08, confidence_score=0.7, loe_rag="amber", degraded_factor_count=1) == "moderate"
    assert mdj._magnitude_from_delta(delta_pct=0.08, confidence_score=0.3, loe_rag="red", degraded_factor_count=4) == "moderate"
    assert mdj._magnitude_from_delta(delta_pct=0.02, confidence_score=0.6, loe_rag="green", degraded_factor_count=0) == "minor"


def test_recommendation_quality_structure():
    rec = mdj._targeting_shift_recommendation(
        signals={
            "targeting": {"raw": {"recommendations": []}},
        },
        owner_level="BN",
    )
    assert rec["title"]
    assert rec["owner_level"] in {"BN", "CO", "STN"}
    assert rec["action"]
    assert rec["expected_effect"]
    assert 1 <= int(rec["priority"]) <= 3
    assert rec["rationale"]
    assert isinstance(rec["linked_factors"], list)
    assert "no targeting rows available" not in rec["title"].lower()
