from typing import Dict, List

import pytest
from sqlalchemy import text

from database import rsid_hierarchy
from services.api.app import database
from services.api.app.intelligence_recommendations import _build_frago_from_recommendation
from services.api.app.routers.intelligence import get_frago_version, get_frago_versions
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


@pytest.fixture()
def frago_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "frago_scope.sqlite3")
    monkeypatch.setenv("TAAIP_DB_PATH", db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    database.reload_engine_if_needed()
    _seed_canonical_org_units(db_path)
    database.reload_engine_if_needed()

    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _known_rsids() -> set:
    with database.engine.connect() as conn:
        rows = conn.execute(text("SELECT rsid FROM org_unit WHERE rsid IS NOT NULL")).mappings().all()
    return {row["rsid"] for row in rows}


def _create_frago_version(db, rsid: str, period_type: str = "FY", period_value: str = "2026"):
    recommendation = {
        "id": f"rec_{rsid}",
        "recommendation_id": f"rec_{rsid}",
        "recommendation_type": "rop_srp",
        "priority": "high",
        "summary": f"FRAGO source for {rsid}",
        "scope": {"station_rsid": rsid},
        "station_rsid": rsid,
        "period_analyzed": {"start_date": "2025-10-01", "end_date": "2026-09-30"},
    }
    frago_version = _build_frago_from_recommendation(
        db=db,
        recommendation=recommendation,
        rop_version_id="rop_v_1",
        srp_version_id="srp_v_1",
        analytics_snapshot_id="snap_1",
        rsid=rsid,
        period_type=period_type,
        period_value=period_value,
    )
    db.commit()
    return frago_version


@pytest.mark.parametrize("rsid", ["1ST BDE", "1A", "1A1", "1A1D", "USAREC"])
def test_frago_content_includes_rsid_unit_scope_period(frago_db, rsid):
    frago_version = _create_frago_version(frago_db, rsid=rsid, period_type="QTR", period_value="Q2")
    content = frago_version.content

    assert content["rsid"] == rsid
    assert isinstance(content["unit_scope"], list)
    assert len(content["unit_scope"]) >= 1
    assert content["unit_scope"][0] == rsid
    assert content["period_type"] == "QTR"
    assert content["period_value"] == "Q2"


@pytest.mark.parametrize("rsid", ["1ST BDE", "1A", "1A1", "1A1D", "USAREC"])
def test_frago_unit_scope_has_no_invented_units(frago_db, rsid):
    frago_version = _create_frago_version(frago_db, rsid=rsid)
    known = _known_rsids()
    invented = set(frago_version.content["unit_scope"]) - known
    assert not invented


def test_frago_unit_scope_order_is_deterministic(frago_db):
    a = _create_frago_version(frago_db, rsid="1A", period_type="FY", period_value="2026")
    b = _create_frago_version(frago_db, rsid="1A", period_type="FY", period_value="2026")
    assert a.content["unit_scope"] == b.content["unit_scope"]


def test_frago_creation_fallback_period_metadata_from_rsm(frago_db):
    recommendation = {
        "id": "rec_rsm",
        "recommendation_id": "rec_rsm",
        "recommendation_type": "vacancy_alignment",
        "scope": {"station_rsid": "1A1"},
        "station_rsid": "1A1",
        "rsm": "RSM-2026-02",
        "period_analyzed": {"start_date": "2026-02-01", "end_date": "2026-02-28"},
    }
    frago_version = _build_frago_from_recommendation(
        db=frago_db,
        recommendation=recommendation,
        rop_version_id="rop_v_1",
        srp_version_id="srp_v_1",
        analytics_snapshot_id="snap_1",
    )
    frago_db.commit()

    assert frago_version.content["period_type"] == "RSM"
    assert frago_version.content["period_value"] == "RSM-2026-02"


def test_frago_retrieval_returns_unit_scope_period_and_snapshots(frago_db):
    frago_version = _create_frago_version(frago_db, rsid="1A", period_type="FY", period_value="2026")

    payload = get_frago_version(frago_version.id, db=frago_db)
    assert payload["rsid"] == "1A"
    assert isinstance(payload["unit_scope"], list)
    assert payload["unit_scope"][0] == "1A"
    assert payload["period_type"] == "FY"
    assert payload["period_value"] == "2026"
    assert payload["analytics_snapshot_id"] == "snap_1"
    assert payload["recommendation_record_version_id"] is None
    assert payload["analytics_snapshot_version_id"] is None


def test_frago_versions_history_returns_metadata(frago_db):
    v1 = _create_frago_version(frago_db, rsid="USAREC", period_type="FY", period_value="2026")
    payload = get_frago_versions(v1.frago_id, db=frago_db)

    assert payload["frago_id"] == v1.frago_id
    assert len(payload["versions"]) >= 1

    first = payload["versions"][0]
    assert first["rsid"] == "USAREC"
    assert isinstance(first["unit_scope"], list)
    assert first["period_type"] == "FY"
    assert first["period_value"] == "2026"


def test_frago_content_includes_linked_snapshots(frago_db):
    frago_version = _create_frago_version(frago_db, rsid="1A1D")
    linkage = frago_version.content.get("linkage") or {}

    assert linkage.get("rop_version_id") == "rop_v_1"
    assert linkage.get("srp_version_id") == "srp_v_1"
    assert linkage.get("analytics_snapshot_id") == "snap_1"
    assert linkage.get("recommendation_record_version_id") is None
    assert linkage.get("analytics_snapshot_version_id") is None
