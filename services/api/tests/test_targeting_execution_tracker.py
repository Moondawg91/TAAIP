from datetime import date

from services.api.app.services import mission_decrease_justification as mdj
from services.api.app.services import targeting_execution_tracker as tet
from services.api.app.routers import powerbi_feed


def _board_ok_payload():
    return {
        "status": "ok",
        "targeting_board_engine": {
            "summary": {
                "total_items": 2,
                "approved_count": 2,
                "modified_count": 0,
                "rejected_count": 0,
                "resource_shift_count": 1,
                "overall_board_posture": "balanced",
            },
            "prioritized_board_items": [],
            "board_decisions": [
                {
                    "decision_id": "DEC-001",
                    "action": "Execute funnel acceleration",
                    "decision_type": "approve",
                    "owner_level": "CO",
                    "expected_effect": "lead_to_contract_rate 0.20",
                    "time_horizon": "2026-04-10",
                    "rationale": "high priority",
                    "trace_id": "BD-001",
                },
                {
                    "decision_id": "DEC-002",
                    "action": "Shift school engagement effort",
                    "decision_type": "approve",
                    "owner_level": "CO",
                    "expected_effect": "engagement_rate 0.35",
                    "time_horizon": "2026-04-20",
                    "rationale": "capacity pressure",
                    "trace_id": "BD-002",
                },
            ],
            "directed_shifts": [
                {
                    "shift_type": "effort",
                    "from": "retention",
                    "to": "funnel",
                    "justification": "board directive",
                    "expected_effect": "improve conversion",
                    "trace_id": "SFT-001",
                }
            ],
            "downstream_twg_tasks": [
                {
                    "task_id": "TASK-001",
                    "source_board_decision_id": "DEC-001",
                    "owner_level": "CO",
                    "action": "Execute funnel acceleration",
                    "due_out": "2026-04-10",
                    "expected_effect": "lead_to_contract_rate 0.20",
                    "trace_id": "TASK-T-001",
                },
                {
                    "task_id": "TASK-002",
                    "source_board_decision_id": "DEC-002",
                    "owner_level": "CO",
                    "action": "Shift school engagement effort",
                    "due_out": "2026-04-20",
                    "expected_effect": "engagement_rate 0.35",
                    "trace_id": "TASK-T-002",
                },
            ],
        },
    }


def _twg_ok_payload():
    return {
        "status": "ok",
        "twg_engine": {
            "summary": {
                "total_items": 2,
                "high_priority_count": 1,
                "medium_priority_count": 1,
                "low_priority_count": 0,
                "board_elevation_count": 2,
                "overall_twg_status": "watch",
            },
            "prioritized_items": [
                {
                    "item_id": "twg-funnel-001",
                    "category": "funnel",
                    "title": "Funnel issue",
                    "priority_score": 75.0,
                    "owner_level": "CO",
                    "recommended_action": "Execute funnel acceleration",
                    "due_out": "within 7 days",
                    "expected_effect": "Increase conversion",
                    "trace_id": "TWG-001",
                }
            ],
            "due_outs": [
                {
                    "item_id": "twg-funnel-001",
                    "owner_level": "CO",
                    "action": "Execute funnel acceleration",
                    "due_out": "within 7 days",
                    "expected_effect": "Increase conversion",
                    "trace_id": "TWG-DO-001",
                }
            ],
            "board_candidates": [],
        },
    }


def _asset_ok_payload(blocked=False):
    constraints = []
    if blocked:
        constraints = [
            {
                "constraint_id": "CONST-001",
                "constraint_type": "personnel",
                "description": "resource tradeoff: overloaded assets",
                "severity": "high",
                "trace_id": "CONST-T-001",
            }
        ]

    return {
        "status": "ok",
        "asset_engine": {
            "summary": {
                "total_assets": 4,
                "overutilized_assets": 1,
                "underutilized_assets": 0,
                "balanced_assets": 3,
                "execution_risk_level": "medium",
                "feasibility_posture": "feasible",
            },
            "asset_distribution": [
                {"asset_id": "REC-001", "status": "balanced", "capacity": 1760.0, "current_load": 1200.0}
            ],
            "recommended_shifts": [
                {
                    "shift_id": "SHIFT-001",
                    "board_decision_id": "DEC-001",
                    "shift_type": "effort",
                    "justification": "board support",
                    "feasibility": "high",
                    "trace_id": "SHIFT-T-001",
                }
            ],
            "execution_constraints": constraints,
        },
    }


def _funnel_ok_payload(rate=0.12):
    return {
        "status": "ok",
        "funnel_engine": {
            "summary": {
                "lead_to_contract_rate": rate,
                "overall_funnel_status": "watch",
            },
            "prioritized_funnel_gaps": [],
        },
    }


def _school_ok_payload(rate=0.30):
    return {
        "status": "ok",
        "school_plan_engine": {
            "summary": {
                "engagement_rate": rate,
                "underengaged_school_count": 2,
                "total_schools": 8,
            },
            "prioritized_schools": [],
            "school_recruiting_plan": [],
        },
    }


def _roi_ok_payload(avg=0.25):
    return {
        "status": "ok",
        "roi_engine": {
            "summary": {
                "avg_roi_score": avg,
                "low_effectiveness_count": 1,
                "total_events_scored": 5,
            },
            "prioritized_events": [],
            "roi_recommendations": [],
        },
    }


def _mission_signal(delta=-0.08):
    return {
        "status": "ok",
        "mission_delta_summary": {
            "delta_pct": delta,
        },
        "decision_summary": {
            "recommended_action": "decrease",
            "confidence_score": 0.7,
        },
    }


def _patch_upstream(monkeypatch, blocked=False, funnel_rate=0.12):
    monkeypatch.setattr(tet.targeting_board_engine, "summarize_targeting_board_engine", lambda *a, **k: _board_ok_payload())
    monkeypatch.setattr(tet.twg_engine, "summarize_twg_engine", lambda *a, **k: _twg_ok_payload())
    monkeypatch.setattr(tet.asset_engine, "summarize_asset_engine", lambda *a, **k: _asset_ok_payload(blocked=blocked))
    monkeypatch.setattr(tet.funnel_engine, "summarize_funnel_engine", lambda *a, **k: _funnel_ok_payload(rate=funnel_rate))
    monkeypatch.setattr(tet.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: _school_ok_payload())
    monkeypatch.setattr(tet.roi_engine, "summarize_roi_engine", lambda *a, **k: _roi_ok_payload())


def test_execution_tracker_valid_data_scorecard_and_escalations(monkeypatch):
    _patch_upstream(monkeypatch, blocked=True, funnel_rate=0.10)

    out = tet.summarize_targeting_execution_tracker(
        db=None,
        scope_type="CO",
        scope_value="1A1",
        actor_scope_type="CO",
        actor_scope_value="1A1",
        mission_signal=_mission_signal(),
        include_mission_signal=False,
    )

    assert out["status"] == "ok"
    payload = out["targeting_execution_tracker"]
    assert payload["summary"]["total_tasks"] == 2
    assert "execution_scorecard" in payload
    assert len(payload["execution_items"]) == 2
    assert len(payload["escalations"]) >= 1


def test_execution_tracker_no_data(monkeypatch):
    monkeypatch.setattr(
        tet.targeting_board_engine,
        "summarize_targeting_board_engine",
        lambda *a, **k: {
            "status": "no_data",
            "targeting_board_engine": {
                "summary": {},
                "board_decisions": [],
                "downstream_twg_tasks": [],
                "directed_shifts": [],
            },
        },
    )
    monkeypatch.setattr(tet.twg_engine, "summarize_twg_engine", lambda *a, **k: {"status": "no_data", "twg_engine": {}})
    monkeypatch.setattr(tet.asset_engine, "summarize_asset_engine", lambda *a, **k: {"status": "no_data", "asset_engine": {}})
    monkeypatch.setattr(tet.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "no_data", "funnel_engine": {}})
    monkeypatch.setattr(tet.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "no_data", "school_plan_engine": {}})
    monkeypatch.setattr(tet.roi_engine, "summarize_roi_engine", lambda *a, **k: {"status": "no_data", "roi_engine": {}})

    out = tet.summarize_targeting_execution_tracker(
        db=None,
        scope_type="CO",
        scope_value="1A1",
        actor_scope_type="CO",
        actor_scope_value="1A1",
        include_mission_signal=False,
    )

    assert out["status"] == "no_data"


def test_execution_tracker_deterministic(monkeypatch):
    _patch_upstream(monkeypatch, blocked=True, funnel_rate=0.10)

    out1 = tet.summarize_targeting_execution_tracker(
        db=None,
        scope_type="CO",
        scope_value="1A1",
        actor_scope_type="CO",
        actor_scope_value="1A1",
        mission_signal=_mission_signal(),
        include_mission_signal=False,
    )
    out2 = tet.summarize_targeting_execution_tracker(
        db=None,
        scope_type="CO",
        scope_value="1A1",
        actor_scope_type="CO",
        actor_scope_value="1A1",
        mission_signal=_mission_signal(),
        include_mission_signal=False,
    )

    assert out1 == out2


def test_execution_tracker_blocked_and_off_track_classification(monkeypatch):
    _patch_upstream(monkeypatch, blocked=True, funnel_rate=0.05)

    out = tet.summarize_targeting_execution_tracker(
        db=None,
        scope_type="CO",
        scope_value="1A1",
        actor_scope_type="CO",
        actor_scope_value="1A1",
        mission_signal=_mission_signal(delta=-0.10),
        include_mission_signal=False,
    )

    payload = out["targeting_execution_tracker"]
    assert payload["summary"]["blocked"] >= 1
    assert payload["summary"]["off_track"] >= 1
    assert len(payload["blocked_items"]) >= 1
    assert len(payload["off_track_items"]) >= 1


def test_execution_tracker_escalation_logic(monkeypatch):
    _patch_upstream(monkeypatch, blocked=True, funnel_rate=0.05)

    out = tet.summarize_targeting_execution_tracker(
        db=None,
        scope_type="CO",
        scope_value="1A1",
        actor_scope_type="CO",
        actor_scope_value="1A1",
        mission_signal=_mission_signal(delta=-0.12),
        include_mission_signal=False,
    )

    escalations = out["targeting_execution_tracker"]["escalations"]
    assert len(escalations) >= 1
    assert any(e["escalate_to"] in {"TWG", "BOARD"} for e in escalations)
    assert any(e["escalate_to"] == "BOARD" for e in escalations)


def test_integration_validation_mission_and_powerbi(monkeypatch):
    # Mission integration path: _collect_signal_summaries contains execution tracker block.
    monkeypatch.setattr(mdj.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}, "prioritized_market_zip": []}})
    monkeypatch.setattr(mdj.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}, "top_access_gaps": []}})
    monkeypatch.setattr(mdj.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(mdj.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {}, "prioritized_funnel_gaps": []}})
    monkeypatch.setattr(mdj.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})
    monkeypatch.setattr(mdj.loe_engine, "summarize_loes", lambda *a, **k: {"total_metrics": 0, "status_counts": {}})
    monkeypatch.setattr(mdj.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}, "prioritized_targets": [], "data_sources": {}}})
    monkeypatch.setattr(mdj.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"status": "ok", "school_plan_engine": {"summary": {}, "prioritized_schools": []}})
    monkeypatch.setattr(mdj.roi_engine, "summarize_roi_engine", lambda *a, **k: {"status": "ok", "roi_engine": {"summary": {}, "prioritized_events": []}})
    monkeypatch.setattr(mdj.twg_engine, "summarize_twg_engine", lambda *a, **k: {"status": "ok", "twg_engine": {"summary": {}, "prioritized_items": []}})
    monkeypatch.setattr(mdj.targeting_board_engine, "summarize_targeting_board_engine", lambda *a, **k: {"status": "ok", "targeting_board_engine": {"summary": {}, "prioritized_board_items": []}})
    monkeypatch.setattr(mdj.asset_engine, "summarize_asset_engine", lambda *a, **k: {"status": "ok", "asset_engine": {"summary": {}, "asset_distribution": []}})
    monkeypatch.setattr(mdj.targeting_execution_tracker, "summarize_targeting_execution_tracker", lambda *a, **k: {"status": "ok", "targeting_execution_tracker": {"summary": {"total_tasks": 1, "blocked": 0, "off_track": 0, "execution_posture": "on_track"}, "execution_items": [{"task_id": "T1"}]}})

    signals = mdj._collect_signal_summaries(db=None, scope_type="CO", scope_value="1A1")
    assert "execution_tracker" in signals
    assert signals["execution_tracker"]["summary"]["total_tasks"] == 1

    # Power BI integration path: command dataset exports execution blocks.
    monkeypatch.setattr(powerbi_feed.market_engine, "summarize_market_engine", lambda *a, **k: {"market_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.school_access, "summarize_school_access", lambda *a, **k: {"school_access": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.execution_quality, "summarize_execution_quality", lambda *a, **k: {"execution_quality": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"funnel_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"targeting_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: {"school_plan_engine": {"summary": {}, "prioritized_schools": [], "school_recruiting_plan": []}})
    monkeypatch.setattr(powerbi_feed._roi_engine_mod, "summarize_roi_engine", lambda *a, **k: {"roi_engine": {"summary": {}, "prioritized_events": [], "roi_recommendations": [], "event_type_performance": []}})
    monkeypatch.setattr(powerbi_feed._twg_engine_mod, "summarize_twg_engine", lambda *a, **k: {"twg_engine": {"summary": {}, "prioritized_items": [], "due_outs": [], "board_candidates": []}})
    monkeypatch.setattr(powerbi_feed._targeting_board_engine_mod, "summarize_targeting_board_engine", lambda *a, **k: {"targeting_board_engine": {"summary": {}, "prioritized_board_items": [], "board_decisions": [], "directed_shifts": [], "downstream_twg_tasks": []}})
    monkeypatch.setattr(powerbi_feed._asset_engine_mod, "summarize_asset_engine", lambda *a, **k: {"asset_engine": {"summary": {}, "asset_distribution": [], "recommended_shifts": [], "execution_constraints": []}})
    monkeypatch.setattr(powerbi_feed._targeting_execution_tracker_mod, "summarize_targeting_execution_tracker", lambda *a, **k: {"targeting_execution_tracker": {"summary": {"total_tasks": 1}, "execution_items": [{"task_id": "T1"}], "blocked_items": [], "off_track_items": [], "escalations": [], "execution_scorecard": {"completion_rate": 0.0, "blocked_rate": 0.0, "on_time_rate": 1.0, "effect_realization_rate": 0.0}}})
    monkeypatch.setattr(powerbi_feed.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})

    class _DummyDb:
        def close(self):
            return None

    monkeypatch.setattr(powerbi_feed._dbmod, "get_db", lambda: iter([_DummyDb()]))

    payload = powerbi_feed.operational_command_dataset(scope_type="CO", scope_value="1A1")
    data = payload["data"]
    assert "execution_summary" in data
    assert "execution_items" in data
    assert "blocked_items" in data
    assert "off_track_items" in data
    assert "escalations" in data
    assert "execution_scorecard" in data
