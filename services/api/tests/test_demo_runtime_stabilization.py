from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.api.app.main import app
from services.api.app.routers import command_center
from services.api.app.services import mission_decrease_justification as mdj


client = TestClient(app)


def test_command_center_overview_uses_cached_phase2(monkeypatch):
    calls = {"count": 0}

    def _fake_phase2(db, scope_type, scope_value):
        calls["count"] += 1
        return {
            "loe_summary": {"status": "ok"},
            "targeting_focus": {"top_focus_count": 0},
            "targeting_engine": {},
            "accountability": {},
            "market_engine": {},
            "school_access": {},
            "school_plan_engine": {},
            "roi_engine": {},
            "twg_engine": {},
            "targeting_board_engine": {},
            "asset_engine": {},
            "flash_to_bang_processing": {},
            "targeting_execution_tracker": {},
            "execution_quality": {},
            "funnel_engine": {},
            "outcome_learning_summary": {},
            "live_context_summary": {},
            "adaptive_update_summary": {},
            "recommended_actions": {"recommendations": []},
        }

    with command_center._PHASE2_CACHE_LOCK:
        command_center._PHASE2_CACHE.clear()
        command_center._PHASE2_INFLIGHT.clear()

    monkeypatch.setattr(command_center, "_build_phase2_payload", _fake_phase2)
    monkeypatch.setenv("COMMAND_CENTER_PHASE2_CACHE_TTL_SECONDS", "120")

    r1 = client.get("/api/command-center/overview?scope_type=USAREC&scope_value=USAREC")
    r2 = client.get("/api/command-center/overview?scope_type=USAREC&scope_value=USAREC")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert calls["count"] == 1

    phase2 = ((r2.json().get("summary") or {}).get("phase2") or {})
    assert "cache_meta" in phase2


def test_mission_adjustment_uses_signature_cache_without_heavy_refresh(monkeypatch):
    # Disable pytest fast-collect branch so this test exercises demo-safe signal snapshot path.
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "")
    monkeypatch.setattr(mdj, "_refresh_signal_snapshot_async", lambda *a, **k: None)

    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        first = mdj.generate_mission_decrease_justification(
            db=session,
            org_id="1A1",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            baseline_start=date(2025, 12, 1),
            baseline_end=date(2025, 12, 31),
            include_evidence=False,
            force_refresh=False,
        )
        second = mdj.generate_mission_decrease_justification(
            db=session,
            org_id="1A1",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            baseline_start=date(2025, 12, 1),
            baseline_end=date(2025, 12, 31),
            include_evidence=False,
            force_refresh=False,
        )

        assert first.get("request_id")
        assert second.get("request_id") == first.get("request_id")
        assert second.get("decision_output_name") == "mission_adjustment_justification"
    finally:
        session.close()
