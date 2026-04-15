import base64
import json
import os

from fastapi.testclient import TestClient

from services.api.app.main import app
from services.api.app import database as _dbmod
from services.api.app.services import adaptive_update_engine, live_context_engine, outcome_learning_engine, mission_decrease_justification as mdj
from services.api.app.routers import command_center as cc_router
from services.api.app.routers import powerbi_feed as pbi_router


client = TestClient(app)


def _jwt_like(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}.signature"


def _seed_learning_records():
    db = next(_dbmod.get_db())
    try:
        outcome_learning_engine.record_outcome(
            db,
            {
                "recommendation_id": "rec-int-1",
                "source_engine": "funnel_engine",
                "scope_type": "USAREC",
                "scope_value": "USAREC",
                "recommendation_kind": "funnel_shift",
                "expected_kpi": {"appointments": 20},
                "actual_kpi": {"appointments": 14},
                "observed_state": "on_track",
            },
        )
        live_context_engine.ingest_context_signals(
            db,
            [
                {
                    "signal_id": "sig-int-1",
                    "signal_summary": "Community event opportunity improves market reach.",
                    "source": "community_feed",
                    "source_type": "official",
                    "confidence": 0.8,
                    "operational_implication": "Opportunity to increase targeted outreach.",
                    "scope_type": "USAREC",
                    "scope_value": "USAREC",
                }
            ],
        )
        adaptive_update_engine.generate_update_proposals(db, "USAREC", "USAREC", persist=True)
    finally:
        try:
            if _dbmod._shared_session is None:
                db.close()
        except Exception:
            pass


def _patch_lightweight_operational_summaries(monkeypatch):
    def _payload(key: str):
        return {key: {"summary": {}}}

    monkeypatch.setattr(cc_router.loe_engine, "summarize_loes", lambda *a, **k: {"status": "ok", "summary": {}})
    monkeypatch.setattr(cc_router.targeting_expansion, "recommendations_for_scope", lambda *a, **k: {"recommendations": []})
    monkeypatch.setattr(cc_router.targeting_engine, "summarize_targeting_engine", lambda *a, **k: _payload("targeting_engine"))
    monkeypatch.setattr(cc_router.accountability_engine, "classify_scope", lambda *a, **k: {"status": "ok"})
    monkeypatch.setattr(cc_router.market_engine, "summarize_market_engine", lambda *a, **k: _payload("market_engine"))
    monkeypatch.setattr(cc_router.school_access, "summarize_school_access", lambda *a, **k: _payload("school_access"))
    monkeypatch.setattr(cc_router.execution_quality, "summarize_execution_quality", lambda *a, **k: _payload("execution_quality"))
    monkeypatch.setattr(cc_router.funnel_engine, "summarize_funnel_engine", lambda *a, **k: _payload("funnel_engine"))
    monkeypatch.setattr(cc_router.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: _payload("school_plan_engine"))
    monkeypatch.setattr(cc_router._roi_engine_mod, "summarize_roi_engine", lambda *a, **k: _payload("roi_engine"))
    monkeypatch.setattr(cc_router._twg_engine_mod, "summarize_twg_engine", lambda *a, **k: _payload("twg_engine"))
    monkeypatch.setattr(cc_router._targeting_board_engine_mod, "summarize_targeting_board_engine", lambda *a, **k: _payload("targeting_board_engine"))
    monkeypatch.setattr(cc_router._asset_engine_mod, "summarize_asset_engine", lambda *a, **k: _payload("asset_engine"))
    monkeypatch.setattr(cc_router._flash_to_bang_processing_engine_mod, "summarize_flash_to_bang_processing_engine", lambda *a, **k: _payload("flash_to_bang_processing_engine"))
    monkeypatch.setattr(cc_router._targeting_execution_tracker_mod, "summarize_targeting_execution_tracker", lambda *a, **k: _payload("targeting_execution_tracker"))
    monkeypatch.setattr(cc_router.ai_recommendation_engine, "generate_recommendation_bundle", lambda *a, **k: {"recommendations": []})

    monkeypatch.setattr(pbi_router.market_engine, "summarize_market_engine", lambda *a, **k: _payload("market_engine"))
    monkeypatch.setattr(pbi_router.school_access, "summarize_school_access", lambda *a, **k: _payload("school_access"))
    monkeypatch.setattr(pbi_router.execution_quality, "summarize_execution_quality", lambda *a, **k: _payload("execution_quality"))
    monkeypatch.setattr(pbi_router.funnel_engine, "summarize_funnel_engine", lambda *a, **k: _payload("funnel_engine"))
    monkeypatch.setattr(pbi_router.targeting_engine, "summarize_targeting_engine", lambda *a, **k: _payload("targeting_engine"))
    monkeypatch.setattr(pbi_router.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: _payload("school_plan_engine"))
    monkeypatch.setattr(pbi_router._roi_engine_mod, "summarize_roi_engine", lambda *a, **k: _payload("roi_engine"))
    monkeypatch.setattr(pbi_router._twg_engine_mod, "summarize_twg_engine", lambda *a, **k: _payload("twg_engine"))
    monkeypatch.setattr(pbi_router._targeting_board_engine_mod, "summarize_targeting_board_engine", lambda *a, **k: _payload("targeting_board_engine"))
    monkeypatch.setattr(pbi_router._asset_engine_mod, "summarize_asset_engine", lambda *a, **k: _payload("asset_engine"))
    monkeypatch.setattr(pbi_router._flash_to_bang_processing_engine_mod, "summarize_flash_to_bang_processing_engine", lambda *a, **k: _payload("flash_to_bang_processing_engine"))
    monkeypatch.setattr(pbi_router._targeting_execution_tracker_mod, "summarize_targeting_execution_tracker", lambda *a, **k: _payload("targeting_execution_tracker"))
    monkeypatch.setattr(pbi_router.accountability_engine, "classify_scope", lambda *a, **k: {"status": "ok"})


def test_mission_service_exposes_controlled_learning_layer():
    db = next(_dbmod.get_db())
    try:
        block = mdj._build_controlled_learning_layer(db, "USAREC", "USAREC")
        assert "outcome_learning_summary" in block
        assert "live_context_summary" in block
        assert "adaptive_update_summary" in block
        assert block["adaptive_awareness"]["auto_apply_enabled"] is False
    finally:
        try:
            if _dbmod._shared_session is None:
                db.close()
        except Exception:
            pass


def test_command_center_and_powerbi_include_controlled_learning_blocks(monkeypatch):
    _patch_lightweight_operational_summaries(monkeypatch)
    _seed_learning_records()

    cc = client.get("/api/command-center/overview?scope_type=USAREC&scope_value=USAREC")
    assert cc.status_code == 200
    phase2 = (cc.json().get("summary") or {}).get("phase2") or {}
    assert "outcome_learning_summary" in phase2
    assert "live_context_summary" in phase2
    assert "adaptive_update_summary" in phase2

    pbi = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert pbi.status_code == 200
    data = (pbi.json() or {}).get("data") or {}
    assert "outcome_learning_summary" in data
    assert "outcome_evaluations" in data
    assert "live_context_summary" in data
    assert "context_signals" in data
    assert "adaptive_update_summary" in data
    assert "adaptive_update_proposals" in data


def test_admin_controlled_learning_proposals_visibility_is_admin_only(monkeypatch):
    _seed_learning_records()

    monkeypatch.setenv("LOCAL_DEV_AUTH_BYPASS", "0")
    try:
        _dbmod.reload_engine_if_needed()
    except Exception:
        pass

    admin_token = _jwt_like({"sub": "admin", "roles": ["system_admin"], "permissions": ["admin.permissions.manage"], "scopes": []})
    commander_token = _jwt_like({"sub": "commander", "roles": ["co_cmd"], "permissions": [], "scopes": []})

    ok = client.get(
        "/api/v2/admin/controlled-learning/proposals?scope_type=USAREC&scope_value=USAREC",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    denied = client.get(
        "/api/v2/admin/controlled-learning/proposals?scope_type=USAREC&scope_value=USAREC",
        headers={"Authorization": f"Bearer {commander_token}"},
    )

    assert ok.status_code == 200
    assert denied.status_code == 403
    assert ok.json().get("status") == "ok"
    assert isinstance(ok.json().get("items"), list)

    os.environ["LOCAL_DEV_AUTH_BYPASS"] = "1"
