from sqlalchemy import text

from services.api.app import database
from services.api.app.services import targeting_engine, targeting_expansion


def _db():
    return next(database.get_db())


def test_targeting_engine_priority_scoring_deterministic(monkeypatch):
    monkeypatch.setattr(
        targeting_engine.market_engine,
        "summarize_market_engine",
        lambda *a, **k: {
            "status": "ok",
            "market_engine": {
                "source_dataset_name": "market.csv",
                "prioritized_market_zip": [
                    {
                        "zip": "11111",
                        "station_rsid": "1A1D",
                        "market_capability_score": 82.0,
                        "opportunity_band": "strong",
                        "trace_id": "m:1",
                    },
                    {
                        "zip": "22222",
                        "station_rsid": "1A1D",
                        "market_capability_score": 55.0,
                        "opportunity_band": "moderate",
                        "trace_id": "m:2",
                    },
                ],
            },
        },
    )
    monkeypatch.setattr(
        targeting_engine.funnel_engine,
        "summarize_funnel_engine",
        lambda *a, **k: {
            "status": "ok",
            "funnel_engine": {
                "source_dataset_name": "funnel.csv",
                "by_scope": {
                    "station": [
                        {
                            "station_rsid": "1A1D",
                            "overall_funnel_status": "critical",
                            "lead_to_contract_rate": 0.05,
                            "largest_dropoff_stage": "interview_to_contract",
                        }
                    ]
                },
                "prioritized_funnel_gaps": [
                    {
                        "station_rsid": "1A1D",
                        "stage": "interview_to_contract",
                        "priority_score": 80.0,
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        targeting_engine.school_access,
        "summarize_school_access",
        lambda *a, **k: {
            "status": "ok",
            "school_access": {
                "source_dataset_name": "schools.csv",
                "top_access_gaps": [
                    {
                        "station_rsid": "1A1D",
                        "zip_code": "11111",
                        "school_id": "SCH1",
                        "school_name": "Alpha HS",
                        "contacts_count": 0,
                        "access_gap_score": 95.0,
                    },
                    {
                        "station_rsid": "1A1D",
                        "zip_code": "22222",
                        "school_id": "SCH2",
                        "school_name": "Bravo HS",
                        "contacts_count": 5,
                        "access_gap_score": 20.0,
                    },
                ],
            },
        },
    )

    out = targeting_engine.summarize_targeting_engine(None, "USAREC", "USAREC", "USAREC", "USAREC", top_n=10)
    assert out.get("status") == "ok"
    rows = (out.get("targeting_engine") or {}).get("prioritized_targets") or []
    assert len(rows) == 2
    assert rows[0]["zip"] == "11111"
    assert rows[0]["priority_score"] >= rows[1]["priority_score"]
    assert rows[0]["priority_band"] in {"high", "moderate", "low"}
    assert rows[0]["trace_id"].startswith("targeting-engine:")


def test_targeting_engine_school_contacts_fallback(monkeypatch):
    db = _db()
    db.execute(text("DROP TABLE IF EXISTS fact_school_contacts"))
    db.execute(
        text(
            """
            CREATE TABLE fact_school_contacts (
              id TEXT,
              school_id TEXT,
              school_name TEXT,
              unit_rsid TEXT,
              zip TEXT
            )
            """
        )
    )
    db.execute(
        text(
            "INSERT INTO fact_school_contacts(id, school_id, school_name, unit_rsid, zip) VALUES('1','S1','Central HS','2B2C','33333')"
        )
    )
    db.commit()

    monkeypatch.setattr(
        targeting_engine.market_engine,
        "summarize_market_engine",
        lambda *a, **k: {
            "status": "ok",
            "market_engine": {
                "source_dataset_name": "market.csv",
                "prioritized_market_zip": [
                    {
                        "zip": "33333",
                        "station_rsid": "2B2C",
                        "market_capability_score": 75.0,
                        "opportunity_band": "strong",
                        "trace_id": "m:3",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        targeting_engine.funnel_engine,
        "summarize_funnel_engine",
        lambda *a, **k: {"status": "no_active_dataset", "funnel_engine": {"by_scope": {"station": []}, "prioritized_funnel_gaps": []}},
    )
    monkeypatch.setattr(
        targeting_engine.school_access,
        "summarize_school_access",
        lambda *a, **k: {"status": "no_active_dataset", "school_access": {"top_access_gaps": []}},
    )

    out = targeting_engine.summarize_targeting_engine(db, "STN", "2B2C", "USAREC", "USAREC", top_n=10)
    assert out.get("status") == "ok"
    ds = (out.get("targeting_engine") or {}).get("data_sources") or {}
    assert ds.get("school") == "fact_school_contacts"


def test_targeting_expansion_uses_targeting_engine(monkeypatch):
    monkeypatch.setattr(
        targeting_expansion.targeting_engine,
        "summarize_targeting_engine",
        lambda *a, **k: {
            "status": "ok",
            "targeting_engine": {
                "summary": {"total_priority_zips": 1, "high_priority_count": 1, "moderate_priority_count": 0, "low_priority_count": 0},
                "data_sources": {"market": "market.csv", "funnel": "funnel.csv", "school": "schools.csv"},
                "prioritized_targets": [
                    {
                        "zip": "44444",
                        "station_rsid": "3C3D",
                        "market_capability_score": 88.0,
                        "opportunity_band": "strong",
                        "funnel_signal": {"status": "watch", "weak_stage": "lead_to_appointment", "conversion_rate": 0.08},
                        "school_signal": {"access_level": "low", "gap": True, "contacts_count": 0},
                        "priority_score": 0.82,
                        "priority_band": "high",
                        "recommended_action": "shift_targeting_to_repair_funnel_dropoff",
                        "rationale": "r",
                        "trace_id": "targeting-engine:3C3D:44444",
                    }
                ],
            },
        },
    )

    out = targeting_expansion.recommendations_for_scope(None, "USAREC", "USAREC", top_n=5)
    recs = out.get("recommendations") or []
    assert len(recs) == 1
    assert recs[0]["zip_code"] == "44444"
    assert "market_supports_shift" in (recs[0].get("reason_codes") or [])
