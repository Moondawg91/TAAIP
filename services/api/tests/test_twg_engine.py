from datetime import date

from fastapi.testclient import TestClient

from services.api.app import database
from services.api.app.main import app
from services.api.app.routers import command_center, powerbi_feed
from services.api.app.services import mission_decrease_justification as mdj
from services.api.app.services import twg_engine

client = TestClient(app)


def _db():
    return next(database.get_db())


def _market_ok(*_a, **_k):
    return {
        "status": "ok",
        "market_engine": {
            "summary": {
                "overall_market_status": "weak",
                "weak_opportunity_zip_count": 3,
            },
            "top_market_gaps": [
                {
                    "zip": "11111",
                    "station_rsid": "1A1D",
                    "trace_id": "market-gap:1A1D:11111",
                }
            ],
            "source_dataset_name": "market.csv",
        },
    }


def _funnel_ok(*_a, **_k):
    return {
        "status": "ok",
        "funnel_engine": {
            "summary": {
                "overall_funnel_status": "critical",
            },
            "prioritized_funnel_gaps": [
                {
                    "station_rsid": "1A1D",
                    "stage": "interview_to_contract",
                    "dropoff_count": 20,
                    "priority_score": 95.0,
                    "trace_id": "funnel-gap:STN:1A1D:interview_to_contract",
                }
            ],
            "source_dataset_name": "funnel.csv",
        },
    }


def _targeting_ok(*_a, **_k):
    return {
        "status": "ok",
        "targeting_engine": {
            "summary": {
                "high_priority_count": 2,
            },
            "prioritized_targets": [
                {
                    "station_rsid": "1A1D",
                    "zip": "11111",
                    "priority_score": 0.92,
                    "trace_id": "targeting:1A1D:11111",
                }
            ],
            "data_sources": {"market": "market.csv"},
        },
    }


def _school_ok(*_a, **_k):
    return {
        "status": "ok",
        "school_plan_engine": {
            "summary": {
                "underengaged_school_count": 2,
            },
            "prioritized_schools": [
                {
                    "school_id": "S1",
                    "school_name": "Alpha HS",
                    "station_rsid": "1A1D",
                    "priority_score": 89.0,
                    "trace_id": "school-plan:1A1D:11111:S1",
                }
            ],
            "source_school_dataset": "schools",
        },
    }


def _roi_ok(*_a, **_k):
    return {
        "status": "ok",
        "roi_engine": {
            "summary": {
                "total_events_scored": 3,
                "low_effectiveness_count": 2,
            },
            "prioritized_events": [
                {
                    "event_id": "E1",
                    "event_name": "Career Fair",
                    "unit_rsid": "1A1D",
                    "roi_score": 32.0,
                    "effectiveness_band": "low",
                    "trace_id": "roi-engine:1A1D:E1",
                },
                {
                    "event_id": "E2",
                    "event_name": "School Night",
                    "unit_rsid": "1A1D",
                    "roi_score": 45.0,
                    "effectiveness_band": "moderate",
                    "trace_id": "roi-engine:1A1D:E2",
                },
            ],
        },
    }


def _acc_ok(*_a, **_k):
    return {"classification": "execution_failure", "confidence": "high"}


def _loe_ok(*_a, **_k):
    return {"status_counts": {"met": 1, "at_risk": 2, "not_met": 1, "unknown": 0}, "total_metrics": 4}


def test_twg_engine_valid_data(monkeypatch):
    monkeypatch.setattr(twg_engine.market_engine, "summarize_market_engine", _market_ok)
    monkeypatch.setattr(twg_engine.funnel_engine, "summarize_funnel_engine", _funnel_ok)
    monkeypatch.setattr(twg_engine.targeting_engine, "summarize_targeting_engine", _targeting_ok)
    monkeypatch.setattr(twg_engine.school_plan_engine, "summarize_school_plan_engine", _school_ok)
    monkeypatch.setattr(twg_engine.roi_engine, "summarize_roi_engine", _roi_ok)
    monkeypatch.setattr(twg_engine.accountability_engine, "classify_scope", _acc_ok)
    monkeypatch.setattr(twg_engine.loe_engine, "summarize_loes", _loe_ok)

    out = twg_engine.summarize_twg_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")

    assert out.get("status") == "ok"
    block = out.get("twg_engine") or {}
    assert (block.get("summary") or {}).get("total_items", 0) > 0
    assert len(block.get("prioritized_items") or []) > 0
    assert len(block.get("twg_agenda") or []) > 0
    assert len(block.get("due_outs") or []) > 0


def test_twg_engine_no_data(monkeypatch):
    monkeypatch.setattr(twg_engine.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "no_data", "market_engine": {"summary": {}, "top_market_gaps": []}})
    monkeypatch.setattr(twg_engine.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "no_data", "funnel_engine": {"summary": {}, "prioritized_funnel_gaps": []}})
    monkeypatch.setattr(twg_engine.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "no_data", "targeting_engine": {"summary": {}, "prioritized_targets": []}})
    monkeypatch.setattr(twg_engine.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "no_data", "school_plan_engine": {"summary": {}, "prioritized_schools": []}})
    monkeypatch.setattr(twg_engine.roi_engine, "summarize_roi_engine", lambda *a, **k: {"status": "no_data", "roi_engine": {"summary": {}, "prioritized_events": []}})
    monkeypatch.setattr(twg_engine.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})
    monkeypatch.setattr(twg_engine.loe_engine, "summarize_loes", lambda *a, **k: {"status_counts": {"met": 0, "at_risk": 0, "not_met": 0, "unknown": 0}, "total_metrics": 0})

    out = twg_engine.summarize_twg_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")
    assert out.get("status") == "no_data"
    assert out.get("twg_engine", {}).get("prioritized_items") == []


def test_twg_engine_deterministic(monkeypatch):
    monkeypatch.setattr(twg_engine.market_engine, "summarize_market_engine", _market_ok)
    monkeypatch.setattr(twg_engine.funnel_engine, "summarize_funnel_engine", _funnel_ok)
    monkeypatch.setattr(twg_engine.targeting_engine, "summarize_targeting_engine", _targeting_ok)
    monkeypatch.setattr(twg_engine.school_plan_engine, "summarize_school_plan_engine", _school_ok)
    monkeypatch.setattr(twg_engine.roi_engine, "summarize_roi_engine", _roi_ok)
    monkeypatch.setattr(twg_engine.accountability_engine, "classify_scope", _acc_ok)
    monkeypatch.setattr(twg_engine.loe_engine, "summarize_loes", _loe_ok)

    out1 = twg_engine.summarize_twg_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")
    out2 = twg_engine.summarize_twg_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")

    assert out1.get("twg_engine", {}).get("prioritized_items") == out2.get("twg_engine", {}).get("prioritized_items")
    assert out1.get("twg_engine", {}).get("twg_agenda") == out2.get("twg_engine", {}).get("twg_agenda")


def test_twg_engine_board_elevation(monkeypatch):
    monkeypatch.setattr(twg_engine.market_engine, "summarize_market_engine", _market_ok)
    monkeypatch.setattr(twg_engine.funnel_engine, "summarize_funnel_engine", _funnel_ok)
    monkeypatch.setattr(twg_engine.targeting_engine, "summarize_targeting_engine", _targeting_ok)
    monkeypatch.setattr(twg_engine.school_plan_engine, "summarize_school_plan_engine", _school_ok)
    monkeypatch.setattr(twg_engine.roi_engine, "summarize_roi_engine", _roi_ok)
    monkeypatch.setattr(twg_engine.accountability_engine, "classify_scope", _acc_ok)
    monkeypatch.setattr(twg_engine.loe_engine, "summarize_loes", _loe_ok)

    out = twg_engine.summarize_twg_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")
    board = out.get("twg_engine", {}).get("board_candidates") or []
    assert len(board) >= 1


def test_command_center_and_powerbi_include_twg(monkeypatch):
    fake_twg = {
        "status": "ok",
        "twg_engine": {
            "summary": {
                "total_items": 3,
                "high_priority_count": 1,
                "medium_priority_count": 2,
                "low_priority_count": 0,
                "board_elevation_count": 1,
                "overall_twg_status": "watch",
            },
            "prioritized_items": [{"item_id": "twg-1", "title": "Issue"}],
            "twg_agenda": [{"sequence": 1, "title": "Issue"}],
            "due_outs": [{"item_id": "twg-1", "action": "Do"}],
            "board_candidates": [{"item_id": "twg-1"}],
        },
    }

    monkeypatch.setattr(command_center._twg_engine_mod, "summarize_twg_engine", lambda *a, **k: fake_twg)
    monkeypatch.setattr(powerbi_feed._twg_engine_mod, "summarize_twg_engine", lambda *a, **k: fake_twg)

    monkeypatch.setattr(command_center.loe_engine, "summarize_loes", lambda *a, **k: {"status": "ok"})
    monkeypatch.setattr(command_center.targeting_expansion, "recommendations_for_scope", lambda *a, **k: {"recommendations": []})
    monkeypatch.setattr(command_center.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})
    monkeypatch.setattr(command_center.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}}})
    monkeypatch.setattr(command_center.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "ok", "school_plan_engine": {"summary": {}}})
    monkeypatch.setattr(command_center._roi_engine_mod, "summarize_roi_engine", lambda *a, **k: {"status": "ok", "roi_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(command_center.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.ai_recommendation_engine, "generate_recommendation_bundle", lambda *a, **k: {"status": "ok", "recommendations": []})

    monkeypatch.setattr(powerbi_feed.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "ok", "school_plan_engine": {"summary": {}, "prioritized_schools": [], "school_recruiting_plan": []}})
    monkeypatch.setattr(powerbi_feed._roi_engine_mod, "summarize_roi_engine", lambda *a, **k: {"status": "ok", "roi_engine": {"summary": {}, "prioritized_events": [], "roi_recommendations": [], "event_type_performance": []}})
    monkeypatch.setattr(powerbi_feed.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})

    cc = client.get("/api/command-center/overview?scope_type=USAREC&scope_value=USAREC")
    assert cc.status_code == 200
    cc_phase2 = cc.json().get("summary", {}).get("phase2", {})
    assert "twg_engine" in cc_phase2
    assert (cc_phase2.get("twg_engine") or {}).get("twg_engine", {}).get("summary", {}).get("total_items") == 3

    pb = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert pb.status_code == 200
    pb_data = pb.json().get("data", {})
    assert pb_data.get("twg_summary", {}).get("total_items") == 3
    assert isinstance(pb_data.get("twg_prioritized_items"), list)
    assert isinstance(pb_data.get("twg_due_outs"), list)
    assert isinstance(pb_data.get("twg_board_candidates"), list)


def test_mission_references_twg_issue_concentration(monkeypatch):
    monkeypatch.setattr(
        mdj,
        "_compute_mission_total",
        lambda *a, **k: mdj.MissionPeriodTotals(
            start=date(2026, 1, 1), end=date(2026, 1, 31), total=90.0, sample_count=10, source="fact_production.date_key"
        ),
    )

    monkeypatch.setattr(mdj, "_collect_signal_summaries", lambda *_a, **_k: {
        "market": {"raw": {"status": "ok"}, "summary": {"overall_market_status": "weak", "market_capability_score": 0.2}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "market.csv", "rows_used": 2},
        "access": {"raw": {"status": "ok"}, "summary": {"overall_access_status": "access_constrained", "penetration_rate": 0.2}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "schools.csv", "rows_used": 2},
        "execution": {"raw": {"status": "ok"}, "summary": {"overall_execution_status": "execution_degraded", "stall_count": 2}, "data_as_of": "2026-01-01T00:00:00Z"},
        "funnel": {"raw": {"status": "ok"}, "summary": {"overall_funnel_status": "critical", "lead_to_contract_rate": 0.05}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "funnel.csv", "rows_used": 2},
        "accountability": {"raw": {}, "summary": {"classification": "execution_failure", "confidence": "high"}, "data_as_of": "2026-01-01T00:00:00Z"},
        "loe": {"raw": {}, "summary": {"status_counts": {"met": 1, "at_risk": 2, "not_met": 1, "unknown": 0}, "total_metrics": 4}, "data_as_of": "2026-01-01T00:00:00Z"},
        "targeting": {"raw": {"targeting_engine": {"prioritized_targets": [{"station_rsid": "1A1D", "zip": "11111", "priority_score": 0.9}]}}, "summary": {"recommendations_count": 1, "high_priority_count": 1}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "market.csv", "rows_used": 1},
        "school_plan": {"raw": {"status": "ok", "school_plan_engine": {"summary": {"total_schools": 1, "priority_school_count": 1, "underengaged_school_count": 1}, "prioritized_schools": [{"school_id": "S1"}], "school_recruiting_plan": [{"action": "Increase cadence", "expected_effect": "Raise engagement", "time_horizon": "next 14 days", "rationale": "r", "trace_id": "school-plan:1A1D:11111:S1"}], "source_school_dataset": "schools"}}, "summary": {"total_schools": 1, "priority_school_count": 1, "underengaged_school_count": 1}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "schools", "rows_used": 1},
        "roi": {"raw": {"status": "ok", "roi_engine": {"summary": {"total_events_scored": 2, "high_effectiveness_count": 0, "low_effectiveness_count": 1}, "prioritized_events": [{"event_id": "E1"}], "roi_recommendations": []}}, "summary": {"total_events_scored": 2, "high_effectiveness_count": 0, "low_effectiveness_count": 1}, "data_as_of": "2026-01-01T00:00:00Z", "rows_used": 1},
        "twg": {"raw": {"status": "ok", "twg_engine": {"summary": {"total_items": 3, "high_priority_count": 2, "overall_twg_status": "critical"}, "prioritized_items": [{"item_id": "twg-1"}] }}, "summary": {"total_items": 3, "high_priority_count": 2, "overall_twg_status": "critical"}, "data_as_of": "2026-01-01T00:00:00Z", "rows_used": 1},
    })

    out = mdj.generate_mission_adjustment_justification(
        db=_db(),
        org_id="1A1D",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        include_evidence=True,
        force_refresh=True,
    )

    factors = out.get("causal_factors") or []
    assert any(f.get("code") == "twg_issue_concentration" for f in factors)
    signal_summaries = out.get("signal_summaries") or {}
    assert "twg" in signal_summaries
