import pytest

from services.api.app import database
from services.api.app import models_intelligence as mi
from services.api.app.routers.intelligence import (
    get_analytics_versions,
    get_recommendation_versions,
    get_frago_versions,
    get_version_detail,
    compare_versions,
)
from services.api.app.services.versioning import (
    create_version_event,
    create_archive_event,
    list_versions,
)


@pytest.fixture()
def archival_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "archival_explanations.sqlite3")
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

    db.add(mi.AnalyticsSnapshot(id="snap_1", snapshot_type="contract_roi", station_rsid="1A1D", fy="2026"))
    db.add(mi.RecommendationRecord(id="rec_1", recommendation_type="rop_srp", station_rsid="1A1D", fy="2026"))
    db.add(mi.FragoOrder(id="frago_1", station_rsid="1A1D", title="FRAGO 1", status="draft"))
    db.commit()

    try:
        yield db
    finally:
        db.close()


def _create_version_plus_archive(db, entity_type, entity_id, content, rsid="1A1D", period_type="FY", period_value="2026", metadata=None):
    version = create_version_event(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        content=content,
        rsid=rsid,
        period_type=period_type,
        period_value=period_value,
        metadata=metadata or {},
    )
    archive = create_archive_event(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        version_id=version.id,
        version_number=version.version_number,
        content=content,
        rsid=rsid,
        period_type=period_type,
        period_value=period_value,
        metadata=metadata or {},
    )
    db.commit()
    return version, archive


def test_every_version_has_matching_archive_event(archival_db):
    version, archive = _create_version_plus_archive(
        archival_db,
        "analytics_snapshot",
        "snap_1",
        {"summary_metrics": {"total_events": 5}},
        metadata={"snapshot_type": "contract_roi", "unit_scope": ["1A1D"]},
    )

    assert archive.entity_type == "analytics_snapshot"
    assert archive.entity_id == "snap_1"
    assert archive.version_number == version.version_number
    assert archive.version_id == version.id


def test_archive_event_includes_explanation_object(archival_db):
    _, archive = _create_version_plus_archive(
        archival_db,
        "recommendation_record",
        "rec_1",
        {"recommendation_type": "rop_srp", "status": "draft"},
        metadata={
            "recommendation_type": "rop_srp",
            "unit_scope": ["1A1D"],
            "confidence": 0.91,
        },
    )

    explanation = (archive.event_metadata or {}).get("explanation") or {}
    required = {
        "entity_type",
        "entity_id",
        "version_number",
        "rsid",
        "period_type",
        "period_value",
        "unit_scope",
        "summary",
        "key_drivers",
        "confidence",
        "metadata",
    }
    assert required.issubset(set(explanation.keys()))
    assert explanation["entity_type"] == "recommendation_record"
    assert explanation["entity_id"] == "rec_1"
    assert explanation["unit_scope"][0] == "1A1D"


def test_archive_events_are_append_only_and_ordered(archival_db):
    _create_version_plus_archive(
        archival_db,
        "frago_order",
        "frago_1",
        {"summary": "A", "unit_scope": ["1A1D"]},
        period_type="RSM",
        period_value="RSM-2026-01",
    )
    _create_version_plus_archive(
        archival_db,
        "frago_order",
        "frago_1",
        {"summary": "B", "unit_scope": ["1A1D"]},
        period_type="RSM",
        period_value="RSM-2026-02",
    )

    versions = list_versions(archival_db, "frago_order", "frago_1")
    events = archival_db.query(mi.VersionArchiveEvent).filter(
        mi.VersionArchiveEvent.entity_type == "frago_order",
        mi.VersionArchiveEvent.entity_id == "frago_1",
    ).order_by(mi.VersionArchiveEvent.version_number.asc()).all()

    assert [v.version_number for v in versions] == [1, 2]
    assert [e.version_number for e in events] == [1, 2]


def test_retrieval_endpoints_return_archive_and_explanation(archival_db):
    _create_version_plus_archive(
        archival_db,
        "analytics_snapshot",
        "snap_1",
        {"summary_metrics": {"total_events": 7}},
        metadata={"snapshot_type": "contract_roi", "unit_scope": ["1A1D"]},
    )
    _create_version_plus_archive(
        archival_db,
        "recommendation_record",
        "rec_1",
        {"recommendation_type": "rop_srp", "status": "draft"},
        metadata={"recommendation_type": "rop_srp", "unit_scope": ["1A1D"]},
    )
    _create_version_plus_archive(
        archival_db,
        "frago_order",
        "frago_1",
        {"summary": "FRAGO one", "unit_scope": ["1A1D"], "period_type": "FY", "period_value": "2026"},
        metadata={"unit_scope": ["1A1D"]},
    )

    analytics = get_analytics_versions("snap_1", db=archival_db)
    recommendation = get_recommendation_versions("rec_1", db=archival_db)
    frago = get_frago_versions("frago_1", db=archival_db)

    assert analytics["versions"][0]["archive_event"]
    assert analytics["versions"][0]["explanation"]
    assert recommendation["versions"][0]["archive_event"]
    assert recommendation["versions"][0]["explanation"]
    assert frago["versions"][0]["archive_event"]
    assert frago["versions"][0]["explanation"]


def test_version_detail_returns_archive_and_explanation(archival_db):
    _create_version_plus_archive(
        archival_db,
        "analytics_snapshot",
        "snap_1",
        {"summary_metrics": {"total_events": 9}},
        metadata={"snapshot_type": "contract_roi", "unit_scope": ["1A1D"]},
    )

    detail = get_version_detail(
        entity_type="analytics_snapshot",
        entity_id="snap_1",
        version_number=1,
        db=archival_db,
    )

    assert detail["content"]
    assert detail["archive_event"]
    assert detail["explanation"]
    assert detail["version_number"] == 1


def test_compare_versions_returns_structured_diff_with_explanation(archival_db):
    _create_version_plus_archive(
        archival_db,
        "frago_order",
        "frago_1",
        {"summary": "A", "unit_scope": ["1A1D"], "period_type": "FY", "period_value": "2026"},
        metadata={"unit_scope": ["1A1D"]},
    )
    _create_version_plus_archive(
        archival_db,
        "frago_order",
        "frago_1",
        {"summary": "B", "unit_scope": ["1A1D"], "period_type": "FY", "period_value": "2026"},
        metadata={"unit_scope": ["1A1D"]},
    )

    req = type(
        "Req",
        (),
        {
            "entity_type": "frago_order",
            "entity_id": "frago_1",
            "left_version": 1,
            "right_version": 2,
        },
    )
    result = compare_versions(req=req, db=archival_db)

    assert result["entity_type"] == "frago_order"
    assert result["entity_id"] == "frago_1"
    assert set(result["diff"].keys()) == {"analytics", "recommendations", "frago", "explanation"}
    assert isinstance(result["left_explanation"], dict)
    assert isinstance(result["right_explanation"], dict)
