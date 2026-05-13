import pytest

from services.api.app import database
from services.api.app import models_intelligence as mi
from services.api.app.routers.intelligence import (
    get_analytics_versions,
    get_recommendation_versions,
    get_frago_versions,
    get_archive_events,
    get_version_detail,
    compare_versions,
)
from services.api.app.services.versioning import create_version_event, create_archive_event


@pytest.fixture()
def e2e_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "integration_end_to_end.sqlite3")
    monkeypatch.setenv("TAAIP_DB_PATH", db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    database.reload_engine_if_needed()

    db = database.SessionLocal()
    bind = db.get_bind()

    mi.AnalyticsSnapshot.__table__.create(bind=bind, checkfirst=True)
    mi.AnalyticsSnapshotVersion.__table__.create(bind=bind, checkfirst=True)
    mi.RecommendationRecord.__table__.create(bind=bind, checkfirst=True)
    mi.RecommendationRecordVersion.__table__.create(bind=bind, checkfirst=True)
    mi.FragoOrder.__table__.create(bind=bind, checkfirst=True)
    mi.FragoOrderVersion.__table__.create(bind=bind, checkfirst=True)
    mi.VersionArchiveEvent.__table__.create(bind=bind, checkfirst=True)

    db.add(mi.AnalyticsSnapshot(id="snap_e2e_1", snapshot_type="contract_roi", station_rsid="1A1D", fy="2026"))
    db.add(mi.RecommendationRecord(id="rec_e2e_1", recommendation_type="rop_srp", station_rsid="1A1D", fy="2026"))
    db.add(mi.FragoOrder(id="frago_e2e_1", station_rsid="1A1D", title="FRAGO E2E", status="draft"))
    db.commit()

    try:
        yield db
    finally:
        db.close()


def _write_version_and_archive(db, entity_type, entity_id, content, metadata):
    version = create_version_event(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        content=content,
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata=metadata,
    )
    archive = create_archive_event(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        version_id=version.id,
        version_number=version.version_number,
        content=content,
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata=metadata,
    )
    return version, archive


def test_e2e_chain_is_deterministic_and_complete(e2e_db):
    # 1) analytics
    _write_version_and_archive(
        e2e_db,
        "analytics_snapshot",
        "snap_e2e_1",
        {"summary_metrics": {"total_events": 11, "contracts": 3}},
        {"snapshot_type": "contract_roi", "unit_scope": ["1A1D"]},
    )

    # 2) recommendation
    rec_v1, _ = _write_version_and_archive(
        e2e_db,
        "recommendation_record",
        "rec_e2e_1",
        {"recommendation_type": "rop_srp", "priority": "high", "status": "draft"},
        {"recommendation_type": "rop_srp", "analytics_snapshot_id": "snap_e2e_1", "unit_scope": ["1A1D"]},
    )

    # 3) frago
    _write_version_and_archive(
        e2e_db,
        "frago_order",
        "frago_e2e_1",
        {
            "summary": "Execute school push",
            "rsid": "1A1D",
            "unit_scope": ["1A1D"],
            "period_type": "FY",
            "period_value": "2026",
            "recommendation": {"recommendation_type": "rop_srp", "priority": "high"},
        },
        {"recommendation_record_version_id": rec_v1.id, "unit_scope": ["1A1D"]},
    )

    e2e_db.commit()

    analytics_payload = get_analytics_versions("snap_e2e_1", db=e2e_db)
    recommendation_payload = get_recommendation_versions("rec_e2e_1", db=e2e_db)
    frago_payload = get_frago_versions("frago_e2e_1", db=e2e_db)
    archive_payload = get_archive_events(station_rsid="1A1D", db=e2e_db)

    assert analytics_payload["versions"]
    assert recommendation_payload["versions"]
    assert frago_payload["versions"]
    assert archive_payload["count"] >= 3

    # 4) deterministic detail retrieval
    detail_a = get_version_detail(entity_type="recommendation_record", entity_id="rec_e2e_1", version_number=1, db=e2e_db)
    detail_b = get_version_detail(entity_type="recommendation_record", entity_id="rec_e2e_1", version_number=1, db=e2e_db)
    assert detail_a == detail_b

    # 5) deterministic compare
    _write_version_and_archive(
        e2e_db,
        "recommendation_record",
        "rec_e2e_1",
        {"recommendation_type": "rop_srp", "priority": "medium", "status": "draft"},
        {"recommendation_type": "rop_srp", "analytics_snapshot_id": "snap_e2e_1", "unit_scope": ["1A1D"]},
    )
    e2e_db.commit()

    compare_req = type(
        "CompareReq",
        (),
        {
            "entity_type": "recommendation_record",
            "entity_id": "rec_e2e_1",
            "left_version": 1,
            "right_version": 2,
        },
    )
    cmp_1 = compare_versions(req=compare_req, db=e2e_db)
    cmp_2 = compare_versions(req=compare_req, db=e2e_db)
    assert cmp_1 == cmp_2

    # 6) no invented RSIDs / metadata completeness
    for row in archive_payload["events"]:
        assert row["station_rsid"] in {"1A1D", None}
        metadata = row.get("metadata") or {}
        explanation = metadata.get("explanation") or {}
        assert explanation.get("entity_type")
        assert explanation.get("entity_id")
        assert "unit_scope" in explanation
        assert "summary" in explanation
        assert "key_drivers" in explanation


def test_ui_fetch_contract_endpoints_are_stable(e2e_db):
    _write_version_and_archive(
        e2e_db,
        "analytics_snapshot",
        "snap_e2e_1",
        {"summary_metrics": {"total_events": 7}},
        {"snapshot_type": "contract_roi", "unit_scope": ["1A1D"]},
    )
    e2e_db.commit()

    # These are the same payloads consumed by intelligence UI pages.
    versions = get_analytics_versions("snap_e2e_1", db=e2e_db)
    detail = get_version_detail(entity_type="analytics_snapshot", entity_id="snap_e2e_1", version_number=1, db=e2e_db)
    archives = get_archive_events(entity_type="analytics_snapshot", station_rsid="1A1D", db=e2e_db)

    assert "versions" in versions
    assert "content" in detail
    assert "archive_event" in detail
    assert "events" in archives
