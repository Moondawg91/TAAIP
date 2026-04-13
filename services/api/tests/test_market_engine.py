import os
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from services.api.app import database
from services.api.app.services import market_engine, targeting_expansion


def _db():
    return next(database.get_db())


def _write_csv(path: Path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def test_market_engine_no_dataset(monkeypatch):
    monkeypatch.setenv("TAAIP_MARKET_CORE_PATH", str(Path("/tmp/does_not_exist_market_core.csv")))
    payload = market_engine.summarize_market_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")
    assert payload["status"] == "no_active_dataset"
    assert payload["market_engine"]["summary"]["overall_market_status"] == "unknown"


def test_market_engine_invalid_schema(tmp_path, monkeypatch):
    p = tmp_path / "6L MARKET CORE.csv"
    _write_csv(
        p,
        [
            {
                "zip": "12345",
                "rsid_enlisted_station": "1A1D",
                "tot_male_18_19_b01001_007e": 10,
            }
        ],
    )
    monkeypatch.setenv("TAAIP_MARKET_CORE_PATH", str(p))

    payload = market_engine.summarize_market_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")
    assert payload["status"] == "invalid_dataset_schema"
    assert "missing required columns" in str(payload["market_engine"].get("schema_error") or "")


def test_market_engine_valid_dataset_outputs(tmp_path, monkeypatch):
    p = tmp_path / "6L MARKET CORE.csv"
    rows = [
        {
            "zip": "11111",
            "rsid_enlisted_station": "1A1D",
            "rsid_enlisted_company": "1A1",
            "rsid_enlisted_battalion": "1A",
            "rsid_enlisted_brigade": "1",
            "tot_male_18_19_b01001_007e": 100,
            "tot_male_20_b01001_008e": 100,
            "tot_male_21_b01001_009e": 100,
            "tot_male_22_24_b01001_010e": 200,
            "tot_female_18_19_b01001_031e": 100,
            "tot_female_20_b01001_032e": 100,
            "tot_female_21_b01001_033e": 100,
            "tot_female_22_24_b01001_034e": 200,
            "tot_nonvet_education_twenty_five_over_b21003_007e": 600,
            "tot_nonvet_edu_high_school_b21003_009e": 200,
            "tot_nonvet_edu_some_college_or_assoc_degree_b21003_010e": 200,
            "tot_nonvet_edu_bachelors_or_higher_b21003_011e": 200,
            "tot_median_income_nonvet_b21004_005e": 60000,
        },
        {
            "zip": "22222",
            "rsid_enlisted_station": "1A1E",
            "rsid_enlisted_company": "1A1",
            "rsid_enlisted_battalion": "1A",
            "rsid_enlisted_brigade": "1",
            "tot_male_18_19_b01001_007e": 20,
            "tot_male_20_b01001_008e": 20,
            "tot_male_21_b01001_009e": 20,
            "tot_male_22_24_b01001_010e": 40,
            "tot_female_18_19_b01001_031e": 20,
            "tot_female_20_b01001_032e": 20,
            "tot_female_21_b01001_033e": 20,
            "tot_female_22_24_b01001_034e": 40,
            "tot_nonvet_education_twenty_five_over_b21003_007e": 120,
            "tot_nonvet_edu_high_school_b21003_009e": 60,
            "tot_nonvet_edu_some_college_or_assoc_degree_b21003_010e": 40,
            "tot_nonvet_edu_bachelors_or_higher_b21003_011e": 20,
            "tot_median_income_nonvet_b21004_005e": 30000,
        },
    ]
    _write_csv(p, rows)
    monkeypatch.setenv("TAAIP_MARKET_CORE_PATH", str(p))

    payload = market_engine.summarize_market_engine(_db(), "USAREC", "USAREC", "USAREC", "USAREC")
    assert payload["status"] == "ok"
    summary = payload["market_engine"]["summary"]
    assert summary["overall_market_status"] in {"strong", "moderate", "weak"}
    assert summary["overall_market_status"] != "unknown"
    assert len(payload["market_engine"]["prioritized_market_zip"]) > 0

    z1 = [z for z in payload["market_engine"]["prioritized_market_zip"] if z["zip"] == "11111"]
    assert z1
    assert z1[0]["total_recruiting_age_population"] == 1000.0


def test_market_engine_scope_filter(tmp_path, monkeypatch):
    p = tmp_path / "6L MARKET CORE.csv"
    _write_csv(
        p,
        [
            {
                "zip": "11111",
                "rsid_enlisted_station": "1A1D",
                "rsid_enlisted_company": "1A1",
                "rsid_enlisted_battalion": "1A",
                "rsid_enlisted_brigade": "1",
                "tot_male_18_19_b01001_007e": 10,
                "tot_male_20_b01001_008e": 10,
                "tot_male_21_b01001_009e": 10,
                "tot_male_22_24_b01001_010e": 10,
                "tot_female_18_19_b01001_031e": 10,
                "tot_female_20_b01001_032e": 10,
                "tot_female_21_b01001_033e": 10,
                "tot_female_22_24_b01001_034e": 10,
            },
            {
                "zip": "99999",
                "rsid_enlisted_station": "9Z9Z",
                "rsid_enlisted_company": "9Z9",
                "rsid_enlisted_battalion": "9Z",
                "rsid_enlisted_brigade": "9",
                "tot_male_18_19_b01001_007e": 10,
                "tot_male_20_b01001_008e": 10,
                "tot_male_21_b01001_009e": 10,
                "tot_male_22_24_b01001_010e": 10,
                "tot_female_18_19_b01001_031e": 10,
                "tot_female_20_b01001_032e": 10,
                "tot_female_21_b01001_033e": 10,
                "tot_female_22_24_b01001_034e": 10,
            },
        ],
    )
    monkeypatch.setenv("TAAIP_MARKET_CORE_PATH", str(p))

    payload = market_engine.summarize_market_engine(_db(), "STN", "1A1D", "USAREC", "USAREC")
    assert payload["status"] == "ok"
    zips = {z["zip"] for z in payload["market_engine"]["prioritized_market_zip"]}
    assert "11111" in zips
    assert "99999" not in zips


def test_targeting_uses_market_engine_rows(tmp_path, monkeypatch):
    p = tmp_path / "6L MARKET CORE.csv"
    _write_csv(
        p,
        [
            {
                "zip": "37011",
                "rsid_enlisted_station": "1A1D",
                "rsid_enlisted_company": "1A1",
                "rsid_enlisted_battalion": "1A",
                "rsid_enlisted_brigade": "1",
                "tot_male_18_19_b01001_007e": 20,
                "tot_male_20_b01001_008e": 20,
                "tot_male_21_b01001_009e": 20,
                "tot_male_22_24_b01001_010e": 20,
                "tot_female_18_19_b01001_031e": 20,
                "tot_female_20_b01001_032e": 20,
                "tot_female_21_b01001_033e": 20,
                "tot_female_22_24_b01001_034e": 20,
            }
        ],
    )
    monkeypatch.setenv("TAAIP_MARKET_CORE_PATH", str(p))

    db = _db()
    db.execute(
        text(
            """
            INSERT OR IGNORE INTO stations(rsid, display)
            VALUES(:rsid, :disp)
            """
        ),
        {"rsid": "1A1D", "disp": "Station 1A1D"},
    )
    db.execute(
        text(
            """
            INSERT OR REPLACE INTO station_zip_coverage(station_rsid, zip_code, market_category)
            VALUES(:stn, :zip, :cat)
            """
        ),
        {"stn": "1A1D", "zip": "37011", "cat": "MK"},
    )
    db.commit()

    out = targeting_expansion.recommendations_for_scope(_db(), "STN", "1A1D", top_n=10)
    zips = [r for r in (out.get("recommendations") or []) if r.get("entity_type") == "zip"]
    assert len(zips) > 0
    assert out.get("source_dataset_name")
    assert any(z.get("market_opportunity_band") in {"strong", "moderate", "weak"} for z in zips)


def test_targeting_includes_market_and_school_signals_from_engine_rows(tmp_path, monkeypatch):
    p = tmp_path / "6L MARKET CORE.csv"
    _write_csv(
        p,
        [
            {
                "zip": "37011",
                "rsid_enlisted_station": "1A1D",
                "rsid_enlisted_company": "1A1",
                "rsid_enlisted_battalion": "1A",
                "rsid_enlisted_brigade": "1",
                "tot_male_18_19_b01001_007e": 100,
                "tot_male_20_b01001_008e": 80,
                "tot_male_21_b01001_009e": 60,
                "tot_male_22_24_b01001_010e": 40,
                "tot_female_18_19_b01001_031e": 90,
                "tot_female_20_b01001_032e": 70,
                "tot_female_21_b01001_033e": 50,
                "tot_female_22_24_b01001_034e": 30,
            },
            {
                "zip": "37012",
                "rsid_enlisted_station": "1A1D",
                "rsid_enlisted_company": "1A1",
                "rsid_enlisted_battalion": "1A",
                "rsid_enlisted_brigade": "1",
                "tot_male_18_19_b01001_007e": 50,
                "tot_male_20_b01001_008e": 40,
                "tot_male_21_b01001_009e": 30,
                "tot_male_22_24_b01001_010e": 20,
                "tot_female_18_19_b01001_031e": 45,
                "tot_female_20_b01001_032e": 35,
                "tot_female_21_b01001_033e": 25,
                "tot_female_22_24_b01001_034e": 15,
            },
        ],
    )
    monkeypatch.setenv("TAAIP_MARKET_CORE_PATH", str(p))

    db = _db()
    db.execute(
        text(
            """
            INSERT OR REPLACE INTO station_zip_coverage(station_rsid, zip_code, market_category)
            VALUES(:stn, :zip1, :cat), (:stn, :zip2, :cat)
            """
        ),
        {"stn": "1A1D", "zip1": "37011", "zip2": "37012", "cat": "MK"},
    )
    db.execute(
        text(
            """
            INSERT INTO fact_school_contacts(school_name, unit_rsid, zip)
            VALUES
            ('High School 1', '1A1D', '37011'),
            ('High School 2', '1A1D', '37012')
            """
        )
    )
    db.commit()

    out = targeting_expansion.recommendations_for_scope(_db(), "STN", "1A1D", top_n=10)
    rows = [r for r in (out.get("recommendations") or []) if r.get("entity_type") == "zip"]
    assert len(rows) >= 2

    sample = rows[0]
    assert sample.get("zip")
    assert sample.get("station_rsid") == "1A1D"
    assert sample.get("market_capability_score") is not None
    assert sample.get("opportunity_band") in {"strong", "moderate", "weak", "unknown"}
    assert isinstance(sample.get("school_access_signal"), dict)
    assert sample.get("rationale")
    assert sample.get("priority_score") is not None
    assert sample.get("trace_id")