from fastapi.testclient import TestClient
import time

from services.api.app.db import connect
from services.api.app.main import app
from services.api.app.routers import powerbi_feed


client = TestClient(app)


def test_powerbi_operational_dataset_shape():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS station_zip_coverage")
    cur.execute("DROP TABLE IF EXISTS market_category_weights")
    cur.execute(
        """
        CREATE TABLE station_zip_coverage(
          id INTEGER PRIMARY KEY,
          station_rsid TEXT,
          zip_code TEXT,
          market_category TEXT,
          source_file TEXT,
          created_at TEXT
        )
        """
    )
    cur.execute("CREATE TABLE market_category_weights(id INTEGER PRIMARY KEY, category TEXT, weight INTEGER)")
    cur.execute("INSERT INTO market_category_weights(category, weight) VALUES('MK', 5)")
    cur.execute("INSERT INTO station_zip_coverage(station_rsid, zip_code, market_category, source_file, created_at) VALUES('Z999','99999','MK','test',datetime('now'))")
    conn.commit()
    conn.close()

    r = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("status") == "ok"
    data = payload.get("data", {})
    # Per-block shape: data has diagnostics/twg/execution blocks + _meta
    assert "diagnostics" in data, f"missing diagnostics block, got keys: {list(data.keys())}"
    assert "twg" in data, "missing twg block"
    assert "execution" in data, "missing execution block"
    diag = data["diagnostics"]
    assert diag.get("status") in ("ok", "timeout", "error")
    diag_data = diag.get("data") or {}
    assert "market_qma_summary" in diag_data
    assert "school_access_summary" in diag_data
    assert "execution_quality_summary" in diag_data
    assert "accountability" in diag_data
    twg_data = (data["twg"].get("data") or {})
    assert "twg_summary" in twg_data
    exec_data = (data["execution"].get("data") or {})
    assert "execution_summary" in exec_data


def test_powerbi_operational_dataset_returns_partial_when_block_slow(monkeypatch):
    def _slow_market(*args, **kwargs):
      time.sleep(0.12)
      return {"market_engine": {"summary": {"overall_market_status": "slow"}}}

    monkeypatch.setenv("OP_COMMAND_DATASET_COMPONENT_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setattr(powerbi_feed, "_OP_DATASET_COMPONENT_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(powerbi_feed.market_engine, "summarize_market_engine", _slow_market)

    r = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("status") == "ok"
    data = payload.get("data", {})
    meta = data.get("_meta", {})
    assert meta.get("partial") is True
    assert "market" in (meta.get("partial_blocks") or [])


def test_powerbi_embed_token_returns_controlled_not_configured_state():
    r = client.post("/api/powerbi/embedToken", json={"reportId": "test-report"})
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("status") == "not_configured"
    assert payload.get("configured") is False
    assert "message" in payload
