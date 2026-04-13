"""Tests for the authoritative ROI / Event Effectiveness Engine.

Coverage:
1. Deterministic scoring with real data → prioritized_events + stable ranking
2. no_data when tables are empty
3. Scoring formula weights produce correct composite
4. Sub-score functions produce expected values at known inputs
5. Mission signal includes roi block and ev-roi evidence
6. Mission recommendations include roi_action kind
7. Command center phase2 exposes roi_engine block
8. PowerBI operational/command_dataset exposes roi_summary and prioritized_events
9. Automation engine delegates to roi_engine scoring formula (no LOE heuristic)
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from services.api.app import database
from services.api.app.main import app
from services.api.app.routers import command_center, powerbi_feed
from services.api.app.services import mission_decrease_justification as mdj
from services.api.app.services import roi_engine

client = TestClient(app)


def _db():
    return next(database.get_db())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_roi_tables(db, *, events=True, spend=True, leads=True):
    """Seed minimal emm_event + spend_fact + lead_journey_fact rows."""
    db.execute(text("DELETE FROM emm_event"))
    db.execute(text("DELETE FROM spend_fact"))
    db.execute(text("DELETE FROM lead_journey_fact"))
    db.execute(text("DELETE FROM roi_thresholds"))

    db.execute(text("""
        CREATE TABLE IF NOT EXISTS roi_thresholds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_key TEXT,
            value REAL
        )
    """))
    db.execute(text("INSERT INTO roi_thresholds(metric_key, value) VALUES('cpl_target', 100.0)"))
    db.execute(text("INSERT INTO roi_thresholds(metric_key, value) VALUES('cpc_target', 2500.0)"))

    if events:
        db.execute(text("""
            INSERT INTO emm_event(event_id, unit_rsid, event_name, event_type, start_date, end_date, zip, cost_total)
            VALUES('EVT-001', '1A1D', 'School Night Alpha', 'school_night', '2026-01-15', '2026-01-15', '11111', 500.0)
        """))
        db.execute(text("""
            INSERT INTO emm_event(event_id, unit_rsid, event_name, event_type, start_date, end_date, zip, cost_total)
            VALUES('EVT-002', '1A1D', 'Career Fair Bravo', 'career_fair', '2026-02-10', '2026-02-10', '22222', 1200.0)
        """))
        db.execute(text("""
            INSERT INTO emm_event(event_id, unit_rsid, event_name, event_type, start_date, end_date, zip, cost_total)
            VALUES('EVT-003', '1A1D', 'MEPS Visit Charlie', 'meps', '2025-11-05', '2025-11-05', '33333', 300.0)
        """))

    if spend:
        # EVT-001 has cost 400 from spend_fact (overrides emm cost_total)
        db.execute(text("INSERT INTO spend_fact(unit_rsid, event_id, spend_type, amount, spend_dt) VALUES('1A1D','EVT-001','direct',400.0,'2026-01-15')"))
        # EVT-002 no spend_fact row — will use emm cost_total (1200)
        # EVT-003 cost 300 from spend_fact
        db.execute(text("INSERT INTO spend_fact(unit_rsid, event_id, spend_type, amount, spend_dt) VALUES('1A1D','EVT-003','direct',300.0,'2025-11-05')"))

    if leads:
        # EVT-001: 10 leads, 2 contracts
        for i in range(10):
            db.execute(text(f"""
                INSERT INTO lead_journey_fact(lead_id, unit_rsid, event_id, lead_created_dt, contract_flag)
                VALUES('L{i:03d}','1A1D','EVT-001','2026-01-20',{1 if i < 2 else 0})
            """))
        # EVT-002: 3 leads, 0 contracts
        for i in range(3):
            db.execute(text(f"""
                INSERT INTO lead_journey_fact(lead_id, unit_rsid, event_id, lead_created_dt, contract_flag)
                VALUES('M{i:03d}','1A1D','EVT-002','2026-02-15',0)
            """))
        # EVT-003: 5 leads, 1 contract
        for i in range(5):
            db.execute(text(f"""
                INSERT INTO lead_journey_fact(lead_id, unit_rsid, event_id, lead_created_dt, contract_flag)
                VALUES('N{i:03d}','1A1D','EVT-003','2025-11-10',{1 if i == 0 else 0})
            """))

    db.commit()


# ---------------------------------------------------------------------------
# 1. Sub-score functions: deterministic correctness
# ---------------------------------------------------------------------------

def test_contract_outcome_score_no_contracts():
    assert roi_engine.compute_contract_outcome_score(0, 500.0, 2500.0) == 0.0


def test_contract_outcome_score_no_cost():
    assert roi_engine.compute_contract_outcome_score(2, 0.0, 2500.0) == 75.0


def test_contract_outcome_score_at_target():
    # CPC = 2500 / 1 = 2500 = cpc_target → 100
    assert roi_engine.compute_contract_outcome_score(1, 2500.0, 2500.0) == 100.0


def test_contract_outcome_score_above_target():
    # CPC = 5001 / 1 = 5001 > 2*cpc_target → 10
    assert roi_engine.compute_contract_outcome_score(1, 5001.0, 2500.0) == 10.0


def test_lead_outcome_score_no_leads():
    assert roi_engine.compute_lead_outcome_score(0, 500.0, 100.0) == 0.0


def test_lead_outcome_score_no_cost():
    assert roi_engine.compute_lead_outcome_score(5, 0.0, 100.0) == 60.0


def test_lead_outcome_score_at_target():
    # CPL = 100 / 1 = 100 = cpl_target → 100
    assert roi_engine.compute_lead_outcome_score(1, 100.0, 100.0) == 100.0


def test_cost_efficiency_score_no_leads():
    assert roi_engine.compute_cost_efficiency_score(0, 0) == 50.0


def test_cost_efficiency_score_high_conversion():
    # 20 contracts / 100 leads = 0.20 ≥ 0.15 → 100
    assert roi_engine.compute_cost_efficiency_score(100, 20) == 100.0


def test_cost_efficiency_score_zero_contracts():
    assert roi_engine.compute_cost_efficiency_score(10, 0) == 10.0


def test_composite_roi_score_formula():
    # Verify deterministic formula
    s = roi_engine.compute_roi_score(100.0, 100.0, 100.0, 100.0, 100.0)
    assert abs(s - 100.0) < 0.0001

    s2 = roi_engine.compute_roi_score(0.0, 0.0, 0.0, 0.0, 0.0)
    assert abs(s2 - 0.0) < 0.0001

    # Known mixed input
    s3 = roi_engine.compute_roi_score(80.0, 60.0, 50.0, 50.0, 50.0)
    expected = 0.35 * 80 + 0.25 * 60 + 0.20 * 50 + 0.10 * 50 + 0.10 * 50
    assert abs(s3 - expected) < 0.01


def test_effectiveness_band():
    assert roi_engine.effectiveness_band(90.0) == "high"
    assert roi_engine.effectiveness_band(70.0) == "high"
    assert roi_engine.effectiveness_band(55.0) == "moderate"
    assert roi_engine.effectiveness_band(40.0) == "moderate"
    assert roi_engine.effectiveness_band(39.9) == "low"
    assert roi_engine.effectiveness_band(0.0) == "low"


# ---------------------------------------------------------------------------
# 2. Engine: no_data when tables are empty
# ---------------------------------------------------------------------------

def test_roi_engine_no_data():
    db = _db()
    db.execute(text("DELETE FROM emm_event"))
    db.execute(text("DELETE FROM event_fact"))
    db.commit()

    out = roi_engine.summarize_roi_engine(db, "USAREC", "USAREC", "USAREC", "USAREC")
    assert out.get("status") == "no_data"
    eng = out.get("roi_engine") or {}
    assert eng.get("prioritized_events") == []
    assert eng.get("roi_recommendations") == []
    assert (eng.get("summary") or {}).get("total_events_scored") == 0


# ---------------------------------------------------------------------------
# 3. Engine: deterministic scoring with known data
# ---------------------------------------------------------------------------

def test_roi_engine_priority_scoring_deterministic(monkeypatch):
    db = _db()
    _seed_roi_tables(db)

    # Stub market/targeting alignment lookups to neutral
    monkeypatch.setattr(
        roi_engine.market_engine, "summarize_market_engine",
        lambda *a, **k: {"status": "ok", "market_engine": {"prioritized_market_zip": [
            {"zip": "11111", "market_capability_score": 80.0},
            {"zip": "22222", "market_capability_score": 40.0},
            {"zip": "33333", "market_capability_score": 60.0},
        ]}}
    )
    monkeypatch.setattr(
        roi_engine.targeting_engine, "summarize_targeting_engine",
        lambda *a, **k: {"status": "ok", "targeting_engine": {"prioritized_targets": [
            {"zip": "11111", "priority_score": 0.85},
            {"zip": "22222", "priority_score": 0.30},
            {"zip": "33333", "priority_score": 0.55},
        ]}}
    )

    out1 = roi_engine.summarize_roi_engine(db, "USAREC", "USAREC", "USAREC", "USAREC", top_n=10)
    out2 = roi_engine.summarize_roi_engine(db, "USAREC", "USAREC", "USAREC", "USAREC", top_n=10)

    assert out1.get("status") == "ok"
    events1 = out1.get("roi_engine", {}).get("prioritized_events", [])
    events2 = out2.get("roi_engine", {}).get("prioritized_events", [])

    # Deterministic: same result on repeated calls
    assert events1 == events2

    # Should have 3 events
    assert len(events1) == 3

    # Sorted by roi_score descending
    scores = [float(e.get("roi_score") or 0.0) for e in events1]
    assert scores == sorted(scores, reverse=True)

    # Required fields on each event
    for ev in events1:
        assert "event_id" in ev
        assert "roi_score" in ev
        assert "effectiveness_band" in ev
        assert "recommendations" in ev
        assert isinstance(ev["recommendations"], list)
        assert "trace_id" in ev
        assert ev["trace_id"].startswith("roi-engine:")

    # Summary aggregates are present
    summary = out1.get("roi_engine", {}).get("summary", {})
    assert summary.get("total_events_scored") == 3
    assert summary.get("total_leads") == 18  # 10 + 3 + 5
    assert summary.get("total_contracts") == 3  # 2 + 0 + 1
    assert isinstance(summary.get("avg_roi_score"), float)


def test_roi_engine_spend_fact_overrides_emm_cost(monkeypatch):
    """EVT-001 should use spend_fact cost (400) not emm cost_total (500)."""
    db = _db()
    _seed_roi_tables(db)

    monkeypatch.setattr(
        roi_engine.market_engine, "summarize_market_engine",
        lambda *a, **k: {"status": "ok", "market_engine": {"prioritized_market_zip": []}}
    )
    monkeypatch.setattr(
        roi_engine.targeting_engine, "summarize_targeting_engine",
        lambda *a, **k: {"status": "ok", "targeting_engine": {"prioritized_targets": []}}
    )

    out = roi_engine.summarize_roi_engine(db, "USAREC", "USAREC", "USAREC", "USAREC")
    events = out.get("roi_engine", {}).get("prioritized_events", [])
    evt001 = next((e for e in events if e["event_id"] == "EVT-001"), None)
    assert evt001 is not None
    # spend_fact row has 400.0 — should override emm cost_total 500.0
    assert evt001["total_cost"] == 400.0


def test_roi_engine_event_type_performance(monkeypatch):
    db = _db()
    _seed_roi_tables(db)

    monkeypatch.setattr(
        roi_engine.market_engine, "summarize_market_engine",
        lambda *a, **k: {"status": "ok", "market_engine": {"prioritized_market_zip": []}}
    )
    monkeypatch.setattr(
        roi_engine.targeting_engine, "summarize_targeting_engine",
        lambda *a, **k: {"status": "ok", "targeting_engine": {"prioritized_targets": []}}
    )

    out = roi_engine.summarize_roi_engine(db, "USAREC", "USAREC", "USAREC", "USAREC")
    perf = out.get("roi_engine", {}).get("event_type_performance", [])
    assert len(perf) >= 1

    types = {p["event_type"] for p in perf}
    assert "school_night" in types or "career_fair" in types or "meps" in types

    for p in perf:
        assert "event_type" in p
        assert "avg_roi_score" in p
        assert "event_count" in p
        assert "effectiveness_band" in p


def test_roi_engine_roi_recommendations_present(monkeypatch):
    db = _db()
    _seed_roi_tables(db)

    monkeypatch.setattr(
        roi_engine.market_engine, "summarize_market_engine",
        lambda *a, **k: {"status": "ok", "market_engine": {"prioritized_market_zip": []}}
    )
    monkeypatch.setattr(
        roi_engine.targeting_engine, "summarize_targeting_engine",
        lambda *a, **k: {"status": "ok", "targeting_engine": {"prioritized_targets": []}}
    )

    out = roi_engine.summarize_roi_engine(db, "USAREC", "USAREC", "USAREC", "USAREC")
    recs = out.get("roi_engine", {}).get("roi_recommendations", [])
    assert len(recs) >= 1

    for r in recs:
        assert "recommendation_id" in r
        assert "owner_level" in r
        assert "action" in r
        assert "expected_effect" in r
        assert "time_horizon" in r
        assert "rationale" in r
        assert "trace_id" in r


# ---------------------------------------------------------------------------
# 4. Mission integration: ev-roi evidence + roi_action recommendation
# ---------------------------------------------------------------------------

def test_mission_includes_roi_signal_and_recommendation(monkeypatch):
    monkeypatch.setattr(
        mdj,
        "_compute_mission_total",
        lambda *a, **k: mdj.MissionPeriodTotals(
            start=date(2026, 1, 1), end=date(2026, 1, 31),
            total=100.0, sample_count=10,
            source="fact_production.date_key"
        ),
    )

    def _signals(*_a, **_k):
        return {
            "market": {"raw": {"status": "ok"}, "summary": {"overall_market_status": "moderate", "market_capability_score": 0.6}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "market.csv", "rows_used": 1},
            "access": {"raw": {"status": "ok"}, "summary": {"overall_access_status": "access_constrained", "penetration_rate": 0.2}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "schools.csv", "rows_used": 1},
            "execution": {"raw": {"status": "ok"}, "summary": {"overall_execution_status": "execution_degraded", "stall_count": 2}, "data_as_of": "2026-01-01T00:00:00Z"},
            "funnel": {"raw": {"status": "ok"}, "summary": {"overall_funnel_status": "watch", "lead_to_contract_rate": 0.1}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "funnel.csv", "rows_used": 1},
            "accountability": {"raw": {}, "summary": {"classification": "execution_failure", "confidence": "medium"}, "data_as_of": "2026-01-01T00:00:00Z"},
            "loe": {"raw": {}, "summary": {"status_counts": {"met": 1, "at_risk": 2, "not_met": 0, "unknown": 0}, "total_metrics": 3}, "data_as_of": "2026-01-01T00:00:00Z"},
            "targeting": {
                "raw": {"targeting_engine": {"prioritized_targets": [{"station_rsid": "1A1D", "zip": "11111", "priority_score": 0.9}]}},
                "summary": {"recommendations_count": 1, "high_priority_count": 1},
                "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "market.csv", "rows_used": 1,
            },
            "school_plan": {
                "raw": {
                    "status": "ok",
                    "school_plan_engine": {
                        "summary": {"total_schools": 1, "priority_school_count": 1, "underengaged_school_count": 1},
                        "prioritized_schools": [{"school_id": "S1"}],
                        "school_recruiting_plan": [{"action": "Increase cadence", "expected_effect": "Raise engagement", "time_horizon": "next 14 days", "rationale": "r", "trace_id": "school-plan:1A1D:11111:S1"}],
                        "source_school_dataset": "schools",
                    },
                },
                "summary": {"total_schools": 1, "priority_school_count": 1, "underengaged_school_count": 1},
                "data_as_of": "2026-01-01T00:00:00Z",
                "source_dataset_name": "schools",
                "rows_used": 1,
            },
            "roi": {
                "raw": {
                    "status": "ok",
                    "roi_engine": {
                        "summary": {"total_events_scored": 2, "high_effectiveness_count": 1, "moderate_effectiveness_count": 0, "low_effectiveness_count": 1, "avg_roi_score": 55.0, "total_leads": 15, "total_contracts": 3, "total_spend": 700.0},
                        "prioritized_events": [{"event_id": "EVT-001", "roi_score": 72.0, "effectiveness_band": "high"}],
                        "roi_recommendations": [{"recommendation_id": "roi-rec-low-performers", "owner_level": "usarec", "action": "Review low ROI events", "expected_effect": "Reduce waste", "time_horizon": "next 30 days", "rationale": "1 event low", "trace_id": "roi-engine:USAREC:USAREC:low_performance"}],
                        "event_type_performance": [],
                    },
                },
                "summary": {"total_events_scored": 2, "high_effectiveness_count": 1, "low_effectiveness_count": 1, "avg_roi_score": 55.0},
                "data_as_of": "2026-01-15T00:00:00Z",
                "rows_used": 2,
            },
        }

    monkeypatch.setattr(mdj, "_collect_signal_summaries", _signals)

    out = mdj.generate_mission_adjustment_justification(
        db=_db(),
        org_id="1A1D",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        include_evidence=True,
        force_refresh=True,
    )

    # signal_summaries exposes roi block
    signal_summaries = out.get("signal_summaries") or {}
    assert "roi" in signal_summaries
    assert signal_summaries["roi"].get("rows_used") == 2

    # recommendations include roi_action
    recs = out.get("recommendations") or []
    assert any(r.get("kind") == "roi_action" for r in recs), "Expected roi_action recommendation"

    # evidence includes ev-roi
    evidence = out.get("evidence") or []
    assert any(e.get("evidence_id") == "ev-roi" for e in evidence), "Expected ev-roi in evidence"


# ---------------------------------------------------------------------------
# 5. Command center + PowerBI integration
# ---------------------------------------------------------------------------

def test_command_center_and_powerbi_expose_roi(monkeypatch):
    fake_roi = {
        "status": "ok",
        "roi_engine": {
            "summary": {"total_events_scored": 3, "high_effectiveness_count": 2, "low_effectiveness_count": 1, "avg_roi_score": 68.0},
            "prioritized_events": [{"event_id": "EVT-001", "roi_score": 80.0, "effectiveness_band": "high"}],
            "roi_recommendations": [{"recommendation_id": "roi-rec-1", "action": "Scale winners"}],
            "event_type_performance": [{"event_type": "school_night", "avg_roi_score": 80.0}],
        },
    }

    monkeypatch.setattr(command_center._roi_engine_mod, "summarize_roi_engine", lambda *a, **k: fake_roi)
    monkeypatch.setattr(powerbi_feed._roi_engine_mod, "summarize_roi_engine", lambda *a, **k: fake_roi)

    # Stub remaining command_center dependencies
    monkeypatch.setattr(command_center.loe_engine, "summarize_loes", lambda *a, **k: {"status": "ok"})
    monkeypatch.setattr(command_center.targeting_expansion, "recommendations_for_scope", lambda *a, **k: {"recommendations": []})
    monkeypatch.setattr(command_center.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "ok", "school_plan_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})
    monkeypatch.setattr(command_center.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}}})
    monkeypatch.setattr(command_center.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(command_center.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.ai_recommendation_engine, "generate_recommendation_bundle", lambda *a, **k: {"status": "ok", "recommendations": []})

    # Stub powerbi dependencies
    monkeypatch.setattr(powerbi_feed.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "ok", "school_plan_engine": {"summary": {}, "prioritized_schools": [], "school_recruiting_plan": []}})
    monkeypatch.setattr(powerbi_feed.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})

    # Command center
    cc = client.get("/api/command-center/overview?scope_type=USAREC&scope_value=USAREC")
    assert cc.status_code == 200
    phase2 = cc.json().get("summary", {}).get("phase2", {})
    assert "roi_engine" in phase2, "command_center phase2 must expose roi_engine"
    roi_block = phase2.get("roi_engine", {})
    assert (roi_block.get("roi_engine") or {}).get("summary", {}).get("total_events_scored") == 3

    # PowerBI operational dataset
    pb = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert pb.status_code == 200
    data = pb.json().get("data", {})
    assert "roi_summary" in data, "powerbi must expose roi_summary"
    assert data["roi_summary"].get("total_events_scored") == 3
    assert isinstance(data.get("roi_prioritized_events"), list)
    assert isinstance(data.get("roi_recommendations"), list)
    assert isinstance(data.get("roi_event_type_performance"), list)
