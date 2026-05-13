from fastapi.testclient import TestClient

from services.api.app import database
from services.api.app.main import app
from services.api.app import models_intelligence as mi
from services.api.app.intelligence_recommendations import (
    _persist_analytics_snapshot_version,
    _persist_recommendation_record_version,
)


client = TestClient(app)


def _db():
    return next(database.get_db())


def test_append_only_analytics_snapshot_versions_create_archive_events():
    db = _db()

    meta1 = _persist_analytics_snapshot_version(
        db=db,
        snapshot_type="vacancy_alignment",
        station_rsid="1A1D",
        fy="26",
        quarter="Q2",
        rsm="1A1",
        payload={"k": 1},
        period_analyzed={"start_date": "2026-01-01", "end_date": "2026-03-31"},
    )
    meta2 = _persist_analytics_snapshot_version(
        db=db,
        snapshot_type="vacancy_alignment",
        station_rsid="1A1D",
        fy="26",
        quarter="Q2",
        rsm="1A1",
        payload={"k": 2},
        period_analyzed={"start_date": "2026-01-01", "end_date": "2026-03-31"},
    )
    db.commit()

    snapshot_id = meta1["analytics_snapshot_id"]
    assert snapshot_id == meta2["analytics_snapshot_id"]

    versions = (
        db.query(mi.AnalyticsSnapshotVersion)
        .filter(mi.AnalyticsSnapshotVersion.snapshot_id == snapshot_id)
        .order_by(mi.AnalyticsSnapshotVersion.version_number.asc())
        .all()
    )
    assert len(versions) == 2
    assert versions[0].version_number == 1
    assert versions[1].version_number == 2
    assert bool(versions[0].is_current) is True
    assert bool(versions[1].is_current) is True

    archive_events = (
        db.query(mi.VersionArchiveEvent)
        .filter(
            mi.VersionArchiveEvent.entity_type == "analytics_snapshot",
            mi.VersionArchiveEvent.entity_id == snapshot_id,
        )
        .order_by(mi.VersionArchiveEvent.version_number.asc())
        .all()
    )
    assert len(archive_events) == 2
    assert archive_events[0].version_number == 1
    assert archive_events[1].version_number == 2


def test_append_only_recommendation_versions_create_archive_events():
    db = _db()

    rec_meta1 = _persist_recommendation_record_version(
        db=db,
        recommendation_type="vacancy_alignment",
        station_rsid="1A1D",
        fy="26",
        quarter="Q2",
        rsm="1A1",
        payload={"recommendations": [{"id": "r1"}]},
        explanation_objects={"items": []},
        analytics_snapshot_id=None,
    )
    rec_meta2 = _persist_recommendation_record_version(
        db=db,
        recommendation_type="vacancy_alignment",
        station_rsid="1A1D",
        fy="26",
        quarter="Q2",
        rsm="1A1",
        payload={"recommendations": [{"id": "r2"}]},
        explanation_objects={"items": []},
        analytics_snapshot_id=None,
    )
    db.commit()

    record_id = rec_meta1["record_id"]
    assert record_id == rec_meta2["record_id"]

    versions = (
        db.query(mi.RecommendationRecordVersion)
        .filter(mi.RecommendationRecordVersion.record_id == record_id)
        .order_by(mi.RecommendationRecordVersion.version_number.asc())
        .all()
    )
    assert len(versions) == 2
    assert versions[0].version_number == 1
    assert versions[1].version_number == 2
    assert bool(versions[0].is_current) is True
    assert bool(versions[1].is_current) is True

    archive_events = (
        db.query(mi.VersionArchiveEvent)
        .filter(
            mi.VersionArchiveEvent.entity_type == "recommendation_record",
            mi.VersionArchiveEvent.entity_id == record_id,
        )
        .order_by(mi.VersionArchiveEvent.version_number.asc())
        .all()
    )
    assert len(archive_events) == 2
    assert archive_events[0].version_number == 1
    assert archive_events[1].version_number == 2


def test_archive_events_endpoint_supports_filters():
    r = client.get("/api/api/v2/intelligence/archive/events?entity_type=analytics_snapshot&limit=10")
    assert r.status_code == 200
    payload = r.json()
    assert "events" in payload
    for event in payload["events"]:
        assert event["entity_type"] == "analytics_snapshot"
