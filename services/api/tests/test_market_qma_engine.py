import uuid

import pytest

from services.api.app import database, models
from services.api.app.db import connect
from services.api.app.services import market_qma, targeting_expansion


def _session():
    return next(database.get_db())


def _seed_station_zip(station_rsid: str, zip_code: str, market_category: str = "MK") -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO stations(rsid, display) VALUES(?, ?)",
        (station_rsid, f"Station {station_rsid}"),
    )
    cur.execute(
        """
        INSERT OR REPLACE INTO station_zip_coverage(station_rsid, zip_code, market_category)
        VALUES(?, ?, ?)
        """,
        (station_rsid, zip_code, market_category),
    )
    conn.commit()
    conn.close()


def _seed_market_zip_metrics_valid(station_rsid: str, zip_code: str, market_category: str = "MK") -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS market_zip_metrics")
    cur.execute(
        """
        CREATE TABLE market_zip_metrics (
          zip_code TEXT,
          station_rsid TEXT,
          market_category TEXT,
          qma_population REAL,
          contracts_actual REAL,
          write_rate_actual REAL,
          data_as_of TEXT,
          fy INTEGER,
          qtr TEXT
        )
        """
    )
    cur.execute(
        """
        INSERT INTO market_zip_metrics(
          zip_code, station_rsid, market_category, qma_population,
          contracts_actual, write_rate_actual, data_as_of, fy, qtr
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (zip_code, station_rsid, market_category, 1000.0, 20.0, 0.02, "2026-01-01T00:00:00Z", 2026, "Q1"),
    )
    conn.commit()
    conn.close()


def test_market_qma_no_active_dataset_for_scope():
    db = _session()
    unique_stn = f"Z{uuid.uuid4().hex[:3]}"
    payload = market_qma.summarize_market_qma(
        db,
        scope_type="STN",
        scope_value=unique_stn,
        actor_scope_type="USAREC",
        actor_scope_value="USAREC",
    )
    assert payload["status"] == "no_active_dataset"
    assert payload["market_qma"]["summary"]["high_opportunity_zip_count"] == 0


def test_market_qma_invalid_dataset_schema_status():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS market_zip_metrics")
    cur.execute(
        """
        CREATE TABLE market_zip_metrics (
          station_rsid TEXT,
          market_category TEXT
        )
        """
    )
    cur.execute(
        "INSERT INTO market_zip_metrics(station_rsid, market_category) VALUES(?, ?)",
        ("A111", "MK"),
    )
    conn.commit()
    conn.close()

    db = _session()
    payload = market_qma.summarize_market_qma(
        db,
        scope_type="USAREC",
        scope_value="USAREC",
        actor_scope_type="USAREC",
        actor_scope_value="USAREC",
    )
    assert payload["status"] == "invalid_dataset_schema"
    assert payload["market_qma"].get("schema_error")


def test_market_qma_valid_dataset_and_summary_shape():
    station = "B123"
    zip_code = "12345"
    _seed_market_zip_metrics_valid(station, zip_code)

    db = _session()
    payload = market_qma.summarize_market_qma(
        db,
        scope_type="STN",
        scope_value=station,
        actor_scope_type="USAREC",
        actor_scope_value="USAREC",
    )

    assert payload["status"] == "ok"
    summary = payload["market_qma"]["summary"]
    assert summary["market_capability_score"] is not None
    assert "overall_market_status" in summary
    assert isinstance(payload["market_qma"]["prioritized_market_zip"], list)
    assert payload["market_qma"]["source_dataset_name"] in {"market_zip_metrics", "market_zip_fact", "mi_zip_fact"}


def test_market_qma_scope_restriction_enforced():
    db = _session()
    with pytest.raises(Exception) as ex:
        market_qma.summarize_market_qma(
            db,
            scope_type="BN",
            scope_value="AB",
            actor_scope_type="BN",
            actor_scope_value="AA",
        )
    assert getattr(ex.value, "status_code", None) == 403


def test_targeting_expansion_includes_market_reason_codes():
    station = "C234"
    zip_code = "23456"

    _seed_station_zip(station, zip_code, market_category="MK")
    _seed_market_zip_metrics_valid(station, zip_code, market_category="MK")

    db = _session()

    # Keep category weights deterministic for this test station's category.
    existing = db.query(models.MarketCategoryWeights).filter(models.MarketCategoryWeights.category == models.MarketCategory.MK).first()
    if not existing:
        db.add(models.MarketCategoryWeights(category=models.MarketCategory.MK, weight=10))
        db.commit()

    recs = targeting_expansion.recommendations_for_scope(db, "STN", station, top_n=10)
    zip_recs = [r for r in recs.get("recommendations", []) if r.get("entity_type") == "zip" and r.get("zip_code") == zip_code]
    assert zip_recs, "expected seeded zip in targeting recommendations"

    reason_codes = set(zip_recs[0].get("reason_codes") or [])
    assert "high_qma_low_output" in reason_codes or "market_supports_shift" in reason_codes
