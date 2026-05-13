from fastapi.testclient import TestClient
from sqlalchemy import text

from database import rsid_hierarchy
from services.api.app import database
from services.api.scripts.import_org_units import connect_db, ensure_indexes, link_parents, upsert_rows
from services.api.scripts.seed_master_org_units import ensure_org_unit_table


def _seed_canonical_org_units(db_path: str) -> None:
    conn = connect_db(db_path)
    try:
        ensure_org_unit_table(conn)
        ensure_indexes(conn)
        rows = rsid_hierarchy.get_org_unit_seed_rows()
        upsert_rows(conn, rows, "test_seed", dry_run=False)
        link_parents(conn, dry_run=False)
    finally:
        conn.close()


def _build_client_with_db(monkeypatch, tmp_path):
    db_path = str(tmp_path / "unit_scope.sqlite3")
    monkeypatch.setenv("TAAIP_DB_PATH", db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("LOCAL_DEV_AUTH_BYPASS", "1")

    database.reload_engine_if_needed()
    _seed_canonical_org_units(db_path)
    database.reload_engine_if_needed()

    from services.api.app.main import app

    return TestClient(app)


def test_unit_scope_subordinates_payload_for_command(monkeypatch, tmp_path):
    client = _build_client_with_db(monkeypatch, tmp_path)

    resp = client.get("/api/v2/unit-scope/subordinates", params={"rsid": "USAREC"})
    assert resp.status_code == 200

    payload = resp.json()
    assert set(payload.keys()) == {"rsid", "echelon", "display_name", "subordinates", "count"}
    assert payload["rsid"] == "USAREC"
    assert payload["echelon"] == "CMD"
    assert payload["display_name"] == "USAREC"
    assert payload["count"] == len(payload["subordinates"])
    assert payload["subordinates"] == sorted(payload["subordinates"])
    assert len(payload["subordinates"]) == len(set(payload["subordinates"]))

    with database.engine.connect() as conn:
        total_units = conn.execute(text("SELECT COUNT(1) AS cnt FROM org_unit")).mappings().first()["cnt"]
    assert payload["count"] == total_units - 1


def test_unit_scope_subordinates_payload_for_station(monkeypatch, tmp_path):
    client = _build_client_with_db(monkeypatch, tmp_path)

    resp = client.get("/api/v2/unit-scope/subordinates", params={"rsid": "1A1D"})
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["rsid"] == "1A1D"
    assert payload["echelon"] == "STN"
    assert payload["subordinates"] == ["1A1D"]
    assert payload["count"] == 1


def test_unit_scope_subordinates_not_found(monkeypatch, tmp_path):
    client = _build_client_with_db(monkeypatch, tmp_path)

    resp = client.get("/api/v2/unit-scope/subordinates", params={"rsid": "NOPE"})
    assert resp.status_code == 404
