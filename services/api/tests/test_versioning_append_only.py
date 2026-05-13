from datetime import datetime

import pytest

from services.api.app import database
from services.api.app import models_intelligence as mi
from services.api.app.routers.intelligence import (
    get_analytics_versions,
    get_recommendation_versions,
    get_frago_versions,
)
from services.api.app.services.versioning import create_version_event, list_versions, get_version
from services.api.app.services.versioning import create_archive_event


@pytest.fixture()
def versioning_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "versioning_append_only.sqlite3")
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

    try:
        yield db
    finally:
        db.close()


def _seed_roots(db):
    snapshot = mi.AnalyticsSnapshot(
        id="snap_root_1",
        snapshot_type="contract_roi",
        station_rsid="1A1D",
        fy="2026",
    )
    record = mi.RecommendationRecord(
        id="rec_root_1",
        recommendation_type="rop_srp",
        station_rsid="1A1D",
        fy="2026",
    )
    frago = mi.FragoOrder(
        id="frago_root_1",
        station_rsid="1A1D",
        title="FRAGO 1A1D",
        status="draft",
    )
    db.add(snapshot)
    db.add(record)
    db.add(frago)
    db.commit()


def test_analytics_versioning_append_only(versioning_db):
    _seed_roots(versioning_db)

    v1 = create_version_event(
        db=versioning_db,
        entity_type="analytics_snapshot",
        entity_id="snap_root_1",
        content={"metric": 1},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"period_analyzed": {"start": "2025-10-01", "end": "2026-09-30"}},
    )
    created_at_v1 = v1.created_at

    v2 = create_version_event(
        db=versioning_db,
        entity_type="analytics_snapshot",
        entity_id="snap_root_1",
        content={"metric": 2},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"period_analyzed": {"start": "2025-10-01", "end": "2026-09-30"}},
    )
    versioning_db.commit()

    versions = list_versions(versioning_db, "analytics_snapshot", "snap_root_1")
    assert [v.version_number for v in versions] == [1, 2]
    assert versions[0].payload == {"metric": 1}
    assert versions[1].payload == {"metric": 2}
    assert versions[0].created_at == created_at_v1
    assert get_version(versioning_db, "analytics_snapshot", "snap_root_1", 1).id == v1.id


def test_recommendation_versioning_append_only(versioning_db):
    _seed_roots(versioning_db)

    v1 = create_version_event(
        db=versioning_db,
        entity_type="recommendation_record",
        entity_id="rec_root_1",
        content={"recommendation": "A"},
        rsid="1A1D",
        period_type="QTR",
        period_value="Q2",
        metadata={"explanation_objects": {"why": "x"}, "analytics_snapshot_id": "snap_root_1"},
    )
    v2 = create_version_event(
        db=versioning_db,
        entity_type="recommendation_record",
        entity_id="rec_root_1",
        content={"recommendation": "B"},
        rsid="1A1D",
        period_type="QTR",
        period_value="Q2",
        metadata={"explanation_objects": {"why": "y"}, "analytics_snapshot_id": "snap_root_1"},
    )
    versioning_db.commit()

    versions = list_versions(versioning_db, "recommendation_record", "rec_root_1")
    assert [v.version_number for v in versions] == [1, 2]
    assert versions[0].payload == {"recommendation": "A"}
    assert versions[1].payload == {"recommendation": "B"}
    assert get_version(versioning_db, "recommendation_record", "rec_root_1", 2).id == v2.id


def test_frago_versioning_append_only(versioning_db):
    _seed_roots(versioning_db)

    content_a = {
        "rsid": "1A1D",
        "unit_scope": ["1A1D"],
        "period_type": "RSM",
        "period_value": "RSM-2026-02",
    }
    content_b = {
        "rsid": "1A1D",
        "unit_scope": ["1A1D"],
        "period_type": "RSM",
        "period_value": "RSM-2026-03",
    }

    create_version_event(
        db=versioning_db,
        entity_type="frago_order",
        entity_id="frago_root_1",
        content=content_a,
        rsid="1A1D",
        period_type="RSM",
        period_value="RSM-2026-02",
        metadata={"generated_from_recommendation_id": "rec_1"},
    )
    create_version_event(
        db=versioning_db,
        entity_type="frago_order",
        entity_id="frago_root_1",
        content=content_b,
        rsid="1A1D",
        period_type="RSM",
        period_value="RSM-2026-03",
        metadata={"generated_from_recommendation_id": "rec_2"},
    )
    versioning_db.commit()

    versions = list_versions(versioning_db, "frago_order", "frago_root_1")
    assert [v.version_number for v in versions] == [1, 2]
    assert versions[0].content["period_value"] == "RSM-2026-02"
    assert versions[1].content["period_value"] == "RSM-2026-03"


def test_archive_events_append_only(versioning_db):
    _seed_roots(versioning_db)

    v1 = create_version_event(
        db=versioning_db,
        entity_type="analytics_snapshot",
        entity_id="snap_root_1",
        content={"metric": 1},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"period_analyzed": {}},
    )
    create_archive_event(
        db=versioning_db,
        entity_type="analytics_snapshot",
        entity_id="snap_root_1",
        version_id=v1.id,
        version_number=v1.version_number,
        content={"metric": 1},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"period_analyzed": {}},
    )

    v2 = create_version_event(
        db=versioning_db,
        entity_type="analytics_snapshot",
        entity_id="snap_root_1",
        content={"metric": 2},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"period_analyzed": {}},
    )
    create_archive_event(
        db=versioning_db,
        entity_type="analytics_snapshot",
        entity_id="snap_root_1",
        version_id=v2.id,
        version_number=v2.version_number,
        content={"metric": 2},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"period_analyzed": {}},
    )
    versioning_db.commit()

    events = versioning_db.query(mi.VersionArchiveEvent).filter(
        mi.VersionArchiveEvent.entity_type == "analytics_snapshot",
        mi.VersionArchiveEvent.entity_id == "snap_root_1",
    ).order_by(mi.VersionArchiveEvent.version_number.asc()).all()

    assert len(events) == 2
    assert [e.version_number for e in events] == [1, 2]


def test_version_endpoints_no_current_semantics(versioning_db):
    _seed_roots(versioning_db)

    create_version_event(
        db=versioning_db,
        entity_type="analytics_snapshot",
        entity_id="snap_root_1",
        content={"metric": 1},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"period_analyzed": {}},
    )
    create_version_event(
        db=versioning_db,
        entity_type="recommendation_record",
        entity_id="rec_root_1",
        content={"rec": 1},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={"explanation_objects": {}},
    )
    create_version_event(
        db=versioning_db,
        entity_type="frago_order",
        entity_id="frago_root_1",
        content={"rsid": "1A1D", "unit_scope": ["1A1D"], "period_type": "FY", "period_value": "2026"},
        rsid="1A1D",
        period_type="FY",
        period_value="2026",
        metadata={},
    )
    versioning_db.commit()

    analytics = get_analytics_versions("snap_root_1", db=versioning_db)
    recommendation = get_recommendation_versions("rec_root_1", db=versioning_db)
    frago = get_frago_versions("frago_root_1", db=versioning_db)

    assert analytics["versions"]
    assert recommendation["versions"]
    assert frago["versions"]

    assert "is_current" not in analytics["versions"][0]
    assert "is_latest" not in analytics["versions"][0]
    assert "is_current" not in recommendation["versions"][0]
    assert "is_latest" not in recommendation["versions"][0]
    assert "is_current" not in frago["versions"][0]
    assert "is_latest" not in frago["versions"][0]
