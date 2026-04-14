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
        "market": {"summary": {"overall_market_status": "supportive"}},
        "targeting": {"raw": {"targeting_engine": {"prioritized_targets": [{"station_rsid": "1A1", "zip": "11111"}]}}},
    }
    ranked = [{"label": "LOE health"}, {"label": "School access penetration"}]

    inc = mdj._derive_recommended_action(
        mission_delta_pct=0.12,
        loe_summary={"rag": "green", "total_metrics": 5, "status_counts": {"at_risk": 0, "not_met": 0}},
        signals=signals,
        confidence={"score": 0.7},
        ranked_factors=[{"label": "LOE health", "impact": 0.2}, {"label": "School access penetration", "impact": 0.2}],
    )
    assert inc["type"] == "increase"

    dec = mdj._derive_recommended_action(
        mission_delta_pct=-0.14,
        loe_summary={"rag": "red", "total_metrics": 5, "status_counts": {"at_risk": 2, "not_met": 1}},
        signals={"access": {"summary": {"penetration_rate": 0.2, "overall_access_status": "access_constrained"}}},
        confidence={"score": 0.6},
        ranked_factors=[{"label": "LOE health", "impact": -0.4}, {"label": "School access penetration", "impact": -0.4}],
    )
    assert dec["type"] == "decrease"

    hold = mdj._derive_recommended_action(
        mission_delta_pct=0.01,
        loe_summary={"rag": "amber", "total_metrics": 0, "status_counts": {}},
        signals={"access": {"summary": {"penetration_rate": 0.45, "overall_access_status": "unknown"}}},
        confidence={"score": 0.5},
        ranked_factors=[{"label": "LOE health", "impact": 0.1}, {"label": "School access penetration", "impact": -0.1}],
    )
    assert hold["type"] == "hold"
    assert hold["rationale"] == "Conditions do not support adjustment due to insufficient confidence or conflicting signals."


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
    assert "completeness" in high.lower() and "agreement" in high.lower() and "recency" in high.lower()


def test_magnitude_classification_uses_delta_confidence_loe_and_degraded_factors():
    assert mdj._magnitude_from_delta(
        delta_pct=0.20,
        confidence_score=0.8,
        loe_summary={"rag": "red"},
        degraded_factor_count=3,
        agreement_score=0.7,
        action_type="decrease",
    ) == "significant"
    assert mdj._magnitude_from_delta(
        delta_pct=0.08,
        confidence_score=0.7,
        loe_summary={"rag": "amber"},
        degraded_factor_count=1,
        agreement_score=0.5,
        action_type="decrease",
    ) == "moderate"
    assert mdj._magnitude_from_delta(
        delta_pct=0.16,
        confidence_score=0.55,
        loe_summary={"rag": "red"},
        degraded_factor_count=4,
        agreement_score=0.8,
        action_type="decrease",
    ) != "significant"
    assert mdj._magnitude_from_delta(
        delta_pct=0.02,
        confidence_score=0.6,
        loe_summary={"rag": "green"},
        degraded_factor_count=0,
        agreement_score=0.5,
        action_type="hold",
    ) == "minor"


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
    assert rec["time_horizon"]
    assert 1 <= int(rec["priority"]) <= 3
    assert rec["rationale"]
    assert isinstance(rec["linked_factors"], list)
    assert "no targeting rows available" not in rec["title"].lower()
    assert "validate inputs" not in rec["action"].lower()


def test_edge_case_high_delta_low_confidence_prevents_significant_overstatement():
    magnitude = mdj._magnitude_from_delta(
        delta_pct=-0.22,
        confidence_score=0.45,
        loe_summary={"rag": "red"},
        degraded_factor_count=4,
        agreement_score=0.9,
        action_type="decrease",
    )
    assert magnitude != "significant"


def test_output_consistency_corrects_mismatch():
    ra, recs, narrative = mdj._validate_and_correct_output(
        recommended_action={"type": "increase", "magnitude": "significant", "confidence": 0.3, "rationale": "x"},
        recommendations=[{"title": "increase recruiting push"}],
        mission_delta_summary={"delta_pct": -0.10},
        confidence={"score": 0.3, "band": "high", "agreement": 0.2},
        commander_narrative="Recommendation: increase mission output at significant magnitude.",
        loe_summary={"rag": "red"},
        signals={},
        ranked_factors=[{"label": "LOE health", "impact": -0.4}],
    )
    assert ra["type"] == "hold"
    assert ra["magnitude"] == "minor"
    assert "Recommendation: hold mission output" in narrative


def test_mission_adjustment_consumes_repaired_funnel_signal(monkeypatch, tmp_path):
    import csv

    csv_path = tmp_path / "Recruiting Funnel Enriched.csv"
    rows = [
        ["1001", "2001", "2000", "hash-a", "M", "2024-01-01", "N", "L", "HS", "", "Y", "AH", "INTERESTED - FOLLOW UP", "A", "ACTIVE", "E", "ENLISTED", "", "", "1A1D", "lead1@example.com", "DOE", "JANE", "", "100 MAIN", "NASHVILLE", "TN", "37011", "37011", "", "2024", "615", "5551111", "6155551111", "B", "PROSPECT", "", "", "", "1704067200000,1704153600000,1704672000000,1705276800000", "B, C, D, Z", "PROSPECT, APPLICANT, DELAYED ENTRY PROGRAM, SHIPPED", "FF, IA, DF, ZB", "FACE TO FACE, APPOINTMENT-INITIAL, FUTURE SOLDIER TRAINING, VALIDATE AFTER SHIP VERIFIED"],
        ["1002", "2002", "2001", "hash-b", "F", "2024-01-03", "N", "L", "HS", "", "Y", "AH", "INTERESTED - FOLLOW UP", "A", "ACTIVE", "E", "ENLISTED", "", "", "1A1E", "lead2@example.com", "SMITH", "JOHN", "", "101 MAIN", "NASHVILLE", "TN", "37012", "37012", "", "2024", "615", "5552222", "6155552222", "A", "LEAD", "", "", "", "1704240000000,1704326400000", "A, B", "LEAD, PROSPECT", "FF, IA", "FACE TO FACE, APPOINTMENT-INITIAL"],
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    monkeypatch.setenv("TAAIP_FUNNEL_DATASET_PATH", str(csv_path))
    monkeypatch.setattr(mdj.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}, "prioritized_market_zip": [], "source_dataset_name": "market.csv"}})
    monkeypatch.setattr(mdj.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}, "top_access_gaps": [], "source_dataset_name": "schools"}})
    monkeypatch.setattr(mdj.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {"overall_execution_status": "healthy", "stall_count": 0, "processing_bottleneck_count": 0}}})
    monkeypatch.setattr(mdj.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})
    monkeypatch.setattr(mdj.loe_engine, "summarize_loes", lambda *a, **k: {"total_metrics": 0, "status_counts": {}})
    monkeypatch.setattr(mdj.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}, "prioritized_targets": [], "data_sources": {}}})
    monkeypatch.setattr(mdj.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "ok", "school_plan_engine": {"summary": {}, "prioritized_schools": []}})
    monkeypatch.setattr(mdj.roi_engine, "summarize_roi_engine", lambda *a, **k: {"status": "no_data", "roi_engine": {"summary": {}, "prioritized_events": []}})
    monkeypatch.setattr(mdj.twg_engine, "summarize_twg_engine", lambda *a, **k: {"status": "ok", "twg_engine": {"summary": {}, "prioritized_items": []}})
    monkeypatch.setattr(mdj.targeting_board_engine, "summarize_targeting_board_engine", lambda *a, **k: {"status": "ok", "targeting_board_engine": {"summary": {}, "prioritized_board_items": []}})
    monkeypatch.setattr(mdj.asset_engine, "summarize_asset_engine", lambda *a, **k: {"status": "ok", "asset_engine": {"summary": {}, "asset_distribution": []}})
    monkeypatch.setattr(mdj.flash_to_bang_processing_engine, "summarize_flash_to_bang_processing_engine", lambda *a, **k: {"status": "ok", "flash_to_bang_processing_engine": {"summary": {}, "processing_items": []}})
    monkeypatch.setattr(mdj.targeting_execution_tracker, "summarize_targeting_execution_tracker", lambda *a, **k: {"status": "ok", "targeting_execution_tracker": {"summary": {}, "execution_items": []}})

    signals = mdj._collect_signal_summaries(db=None, scope_type="USAREC", scope_value="USAREC")
    funnel = signals.get("funnel") or {}
    assert (funnel.get("raw") or {}).get("status") == "ok"
    assert (funnel.get("summary") or {}).get("total_leads", 0) >= 2
    assert isinstance((funnel.get("raw") or {}).get("funnel_engine", {}).get("prioritized_funnel_gaps"), list)


def test_mission_adjustment_includes_real_signal_summaries_when_data_exists(monkeypatch, tmp_path):
    import pandas as pd

    p = tmp_path / "6L MARKET CORE.csv"
    pd.DataFrame(
        [
            {
                "zip": "37011",
                "rsid_enlisted_station": "1A1D",
                "rsid_enlisted_company": "1A1",
                "rsid_enlisted_battalion": "1A",
                "rsid_enlisted_brigade": "1",
                "tot_male_18_19_b01001_007e": 100,
                "tot_male_20_b01001_008e": 80,
                "tot_male_21_b01001_009e": 60,
                "tot_male_22_24_b01001_010e": 40,
                "tot_female_18_19_b01001_031e": 90,
                "tot_female_20_b01001_032e": 70,
                "tot_female_21_b01001_033e": 50,
                "tot_female_22_24_b01001_034e": 30,
            }
        ]
    ).to_csv(p, index=False)
    monkeypatch.setenv("TAAIP_MARKET_CORE_PATH", str(p))

    db = SessionLocal()
    db.execute(
        mdj.text(
            """
            CREATE TABLE IF NOT EXISTS fact_school_contacts (
                id TEXT,
                school_id TEXT,
                school_name TEXT,
                unit_rsid TEXT,
                zip TEXT
            )
            """
        )
    )
    db.execute(
        mdj.text(
            """
            INSERT INTO fact_school_contacts(school_name, unit_rsid, zip)
            VALUES('High School 1','1A1D','37011')
            """
        )
    )
    db.commit()

    out = mdj.generate_mission_adjustment_justification(
        db=db,
        org_id="1A1D",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        include_evidence=True,
        force_refresh=True,
    )

    sig = out.get("signal_summaries") or {}
    market = sig.get("market") or {}
    school = sig.get("school_access") or {}
    targeting = sig.get("targeting") or {}

    assert market.get("status") in {"ok", "no_active_dataset", "invalid_dataset_schema"}
    assert market.get("source_dataset_name")
    assert isinstance(market.get("rows_used"), int)

    assert school.get("status") == "ok"
    assert school.get("source_dataset_name") in {"schools", "fact_school_contacts"}
    assert isinstance(school.get("rows_used"), int)

    assert targeting.get("status") == "ok"
    assert targeting.get("source_dataset_name")
    assert isinstance(targeting.get("rows_used"), int)
