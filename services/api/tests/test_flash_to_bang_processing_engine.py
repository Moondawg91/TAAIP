from services.api.app.routers import powerbi_feed
from services.api.app.services import flash_to_bang_processing_engine as fbp
from services.api.app.services import mission_decrease_justification as mdj


def _execution_quality_ok_payload():
    return {
        "status": "ok",
        "execution_quality": {
            "summary": {
                "overall_execution_status": "execution_degraded",
                "avg_flash_to_bang": 58.5,
                "stall_count": 3,
                "processing_bottleneck_count": 1,
            },
            "by_scope": {
                "bde": [],
                "bn": [],
                "company": [],
                "station": [
                    {
                        "station_rsid": "A111",
                        "lead_count": 8,
                        "avg_flash_to_bang": 95.0,
                        "avg_stage_age_days": 24.0,
                        "stall_count": 2,
                        "processing_bottleneck_count": 1,
                        "execution_status": "execution_degraded",
                    },
                    {
                        "station_rsid": "A112",
                        "lead_count": 6,
                        "avg_flash_to_bang": 42.0,
                        "avg_stage_age_days": 18.0,
                        "stall_count": 1,
                        "processing_bottleneck_count": 0,
                        "execution_status": "execution_degraded",
                    },
                    {
                        "station_rsid": "A113",
                        "lead_count": 5,
                        "avg_flash_to_bang": 21.0,
                        "avg_stage_age_days": 8.0,
                        "stall_count": 0,
                        "processing_bottleneck_count": 0,
                        "execution_status": "execution_stable",
                    },
                ],
            },
            "root_cause_breakdown": [
                {"cause": "processing_problem", "count": 3},
                {"cause": "future_soldier_management_problem", "count": 1},
            ],
            "data_as_of": "2026-04-13T00:00:00Z",
            "last_refresh": "2026-04-13T00:00:00Z",
            "source_dataset_name": "funnel_transitions",
        },
    }


def _execution_quality_twg_payload():
    return {
        "status": "ok",
        "execution_quality": {
            "summary": {
                "overall_execution_status": "execution_degraded",
                "avg_flash_to_bang": 41.0,
                "stall_count": 1,
                "processing_bottleneck_count": 0,
            },
            "by_scope": {
                "bde": [],
                "bn": [],
                "company": [],
                "station": [
                    {
                        "station_rsid": "B221",
                        "lead_count": 4,
                        "avg_flash_to_bang": 40.0,
                        "avg_stage_age_days": 16.0,
                        "stall_count": 1,
                        "processing_bottleneck_count": 0,
                        "execution_status": "execution_degraded",
                    }
                ],
            },
            "root_cause_breakdown": [
                {"cause": "engagement_problem", "count": 1},
            ],
            "data_as_of": "2026-04-13T00:00:00Z",
            "last_refresh": "2026-04-13T00:00:00Z",
            "source_dataset_name": "funnel_transitions",
        },
    }


def _funnel_ok_payload():
    return {
        "status": "ok",
        "funnel_engine": {
            "summary": {
                "overall_funnel_status": "critical",
                "lead_to_contract_rate": 0.06,
            },
            "prioritized_funnel_gaps": [
                {
                    "scope_type": "STN",
                    "scope_value": "A111",
                    "station_rsid": "A111",
                    "stage": "interview_to_contract",
                    "dropoff_count": 4,
                    "conversion_rate": 0.2,
                    "priority_score": 3.2,
                    "trace_id": "FG-001",
                },
                {
                    "scope_type": "STN",
                    "scope_value": "A112",
                    "station_rsid": "A112",
                    "stage": "appointment_to_interview",
                    "dropoff_count": 2,
                    "conversion_rate": 0.5,
                    "priority_score": 1.0,
                    "trace_id": "FG-002",
                },
            ],
            "data_as_of": "2026-04-13T00:00:00Z",
            "source_dataset_name": "Recruiting Funnel Enriched.csv",
        },
    }


def _accountability_payload(classification="execution_failure"):
    return {
        "classification": classification,
        "reason_codes": ["test_reason"],
        "recommended_next_action": "Execute processing recovery plan and weekly flash-to-bang review",
    }


def test_flash_to_bang_processing_valid_data(monkeypatch):
    monkeypatch.setattr(fbp.execution_quality, "summarize_execution_quality", lambda *a, **k: _execution_quality_ok_payload())
    monkeypatch.setattr(fbp.funnel_engine, "summarize_funnel_engine", lambda *a, **k: _funnel_ok_payload())
    monkeypatch.setattr(fbp.accountability_engine, "classify_scope", lambda *a, **k: _accountability_payload())

    out = fbp.summarize_flash_to_bang_processing_engine(
        db=None,
        scope_type="CO",
        scope_value="A11",
        actor_scope_type="CO",
        actor_scope_value="A11",
    )

    assert out["status"] == "ok"
    payload = out["flash_to_bang_processing_engine"]
    assert payload["summary"]["total_leads"] == 19
    assert payload["summary"]["authoritative_flash_to_bang_days"] == 58.5
    assert len(payload["processing_items"]) == 3
    assert len(payload["stalled_items"]) == 1
    assert len(payload["overdue_items"]) == 1
    assert len(payload["escalations"]) == 2


def test_flash_to_bang_processing_no_data(monkeypatch):
    monkeypatch.setattr(
        fbp.execution_quality,
        "summarize_execution_quality",
        lambda *a, **k: {"status": "no_active_dataset", "execution_quality": {"summary": {}, "by_scope": {"station": []}, "root_cause_breakdown": []}},
    )
    monkeypatch.setattr(fbp.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "no_active_dataset", "funnel_engine": {}})
    monkeypatch.setattr(fbp.accountability_engine, "classify_scope", lambda *a, **k: _accountability_payload("insufficient_data"))

    out = fbp.summarize_flash_to_bang_processing_engine(
        db=None,
        scope_type="CO",
        scope_value="A11",
        actor_scope_type="CO",
        actor_scope_value="A11",
    )

    assert out["status"] == "no_data"
    assert out["flash_to_bang_processing_engine"]["processing_items"] == []


def test_flash_to_bang_processing_deterministic(monkeypatch):
    monkeypatch.setattr(fbp.execution_quality, "summarize_execution_quality", lambda *a, **k: _execution_quality_ok_payload())
    monkeypatch.setattr(fbp.funnel_engine, "summarize_funnel_engine", lambda *a, **k: _funnel_ok_payload())
    monkeypatch.setattr(fbp.accountability_engine, "classify_scope", lambda *a, **k: _accountability_payload())

    out1 = fbp.summarize_flash_to_bang_processing_engine(db=None, scope_type="CO", scope_value="A11", actor_scope_type="CO", actor_scope_value="A11")
    out2 = fbp.summarize_flash_to_bang_processing_engine(db=None, scope_type="CO", scope_value="A11", actor_scope_type="CO", actor_scope_value="A11")
    assert out1 == out2


def test_flash_to_bang_processing_stalled_and_overdue(monkeypatch):
    monkeypatch.setattr(fbp.execution_quality, "summarize_execution_quality", lambda *a, **k: _execution_quality_ok_payload())
    monkeypatch.setattr(fbp.funnel_engine, "summarize_funnel_engine", lambda *a, **k: _funnel_ok_payload())
    monkeypatch.setattr(fbp.accountability_engine, "classify_scope", lambda *a, **k: _accountability_payload())

    out = fbp.summarize_flash_to_bang_processing_engine(db=None, scope_type="CO", scope_value="A11", actor_scope_type="CO", actor_scope_value="A11")
    payload = out["flash_to_bang_processing_engine"]

    statuses = {item["station_rsid"]: item["status"] for item in payload["processing_items"]}
    assert statuses["A111"] == "overdue"
    assert statuses["A112"] == "stalled"
    assert statuses["A113"] == "on_track"


def test_flash_to_bang_processing_escalation_routing(monkeypatch):
    monkeypatch.setattr(fbp.execution_quality, "summarize_execution_quality", lambda *a, **k: _execution_quality_twg_payload())
    monkeypatch.setattr(fbp.funnel_engine, "summarize_funnel_engine", lambda *a, **k: _funnel_ok_payload())
    monkeypatch.setattr(fbp.accountability_engine, "classify_scope", lambda *a, **k: _accountability_payload("balanced"))

    out = fbp.summarize_flash_to_bang_processing_engine(db=None, scope_type="CO", scope_value="B22", actor_scope_type="CO", actor_scope_value="B22")
    escalations = out["flash_to_bang_processing_engine"]["escalations"]
    assert len(escalations) == 1
    assert escalations[0]["escalate_to"] == "TWG"


def test_flash_to_bang_processing_mission_and_powerbi_integration(monkeypatch):
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
    monkeypatch.setattr(mdj.flash_to_bang_processing_engine, "summarize_flash_to_bang_processing_engine", lambda *a, **k: {"status": "ok", "flash_to_bang_processing_engine": {"summary": {"total_leads": 5, "stalled": 1, "overdue": 0, "processing_posture": "watch"}, "processing_items": [{"processing_item_id": "P1"}]}})
    monkeypatch.setattr(mdj.targeting_execution_tracker, "summarize_targeting_execution_tracker", lambda *a, **k: {"status": "ok", "targeting_execution_tracker": {"summary": {"total_tasks": 1}, "execution_items": [{"task_id": "T1"}]}})

    signals = mdj._collect_signal_summaries(db=None, scope_type="CO", scope_value="A11")
    assert "flash_to_bang_processing" in signals
    assert signals["flash_to_bang_processing"]["summary"]["total_leads"] == 5

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
    monkeypatch.setattr(powerbi_feed._flash_to_bang_processing_engine_mod, "summarize_flash_to_bang_processing_engine", lambda *a, **k: {"flash_to_bang_processing_engine": {"summary": {"total_leads": 5}, "processing_items": [{"processing_item_id": "P1"}], "stalled_items": [], "overdue_items": [], "escalations": [], "processing_scorecard": {"on_track_rate": 1.0}}})
    monkeypatch.setattr(powerbi_feed._targeting_execution_tracker_mod, "summarize_targeting_execution_tracker", lambda *a, **k: {"targeting_execution_tracker": {"summary": {}, "execution_items": [], "blocked_items": [], "off_track_items": [], "escalations": [], "execution_scorecard": {}}})
    monkeypatch.setattr(powerbi_feed.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})

    class _DummyDb:
        def close(self):
            return None

    monkeypatch.setattr(powerbi_feed._dbmod, "get_db", lambda: iter([_DummyDb()]))

    payload = powerbi_feed.operational_command_dataset(scope_type="CO", scope_value="A11")
    data = payload["data"]
    assert "processing_summary" in data
    assert "processing_items" in data
    assert "processing_stalled_items" in data
    assert "processing_overdue_items" in data
    assert "processing_escalations" in data
    assert "processing_scorecard" in data