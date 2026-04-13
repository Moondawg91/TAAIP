from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import text

from services.api.app import database
from services.api.app.main import app
from services.api.app.routers import command_center, powerbi_feed
from services.api.app.services import mission_decrease_justification as mdj
from services.api.app.services import school_plan_engine


client = TestClient(app)


def _db():
    return next(database.get_db())


def test_school_plan_engine_priority_scoring_deterministic(monkeypatch):
    db = _db()
    db.execute(text("DROP TABLE IF EXISTS schools"))
    db.execute(
        text(
            """
            CREATE TABLE schools (
                school_id TEXT,
                school_name TEXT,
                station_rsid TEXT,
                zip_code TEXT
            )
            """
        )
    )
    db.execute(text("INSERT INTO schools(school_id, school_name, station_rsid, zip_code) VALUES('S1','Alpha HS','1A1D','11111')"))
    db.execute(text("INSERT INTO schools(school_id, school_name, station_rsid, zip_code) VALUES('S2','Bravo HS','1A1D','22222')"))
    db.commit()

    monkeypatch.setattr(
        school_plan_engine.market_engine,
        "summarize_market_engine",
        lambda *a, **k: {
            "status": "ok",
            "market_engine": {
                "source_dataset_name": "market.csv",
                "data_as_of": "2026-01-01T00:00:00Z",
                "prioritized_market_zip": [
                    {"station_rsid": "1A1D", "zip": "11111", "market_capability_score": 90.0, "opportunity_band": "strong"},
                    {"station_rsid": "1A1D", "zip": "22222", "market_capability_score": 55.0, "opportunity_band": "moderate"},
                ],
            },
        },
    )
    monkeypatch.setattr(
        school_plan_engine.funnel_engine,
        "summarize_funnel_engine",
        lambda *a, **k: {
            "status": "ok",
            "funnel_engine": {
                "source_dataset_name": "funnel.csv",
                "data_as_of": "2026-01-01T00:00:00Z",
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
                "prioritized_funnel_gaps": [{"station_rsid": "1A1D", "stage": "interview_to_contract", "priority_score": 80.0}],
            },
        },
    )
    monkeypatch.setattr(
        school_plan_engine.school_access,
        "summarize_school_access",
        lambda *a, **k: {
            "status": "ok",
            "school_access": {
                "source_dataset_name": "schools.csv",
                "data_as_of": "2026-01-01T00:00:00Z",
                "top_access_gaps": [
                    {
                        "school_id": "S1",
                        "school_name": "Alpha HS",
                        "station_rsid": "1A1D",
                        "zip_code": "11111",
                        "contacts_count": 0,
                        "contracts_count": 0,
                        "access_gap_score": 92.0,
                        "access_classification": "underpenetrated",
                    },
                    {
                        "school_id": "S2",
                        "school_name": "Bravo HS",
                        "station_rsid": "1A1D",
                        "zip_code": "22222",
                        "contacts_count": 6,
                        "contracts_count": 1,
                        "access_gap_score": 20.0,
                        "access_classification": "supported",
                    },
                ],
            },
        },
    )
    monkeypatch.setattr(
        school_plan_engine.targeting_engine,
        "summarize_targeting_engine",
        lambda *a, **k: {
            "status": "ok",
            "targeting_engine": {
                "data_as_of": "2026-01-01T00:00:00Z",
                "data_sources": {"market": "market.csv", "funnel": "funnel.csv", "school": "schools.csv"},
                "prioritized_targets": [
                    {"station_rsid": "1A1D", "zip": "11111", "priority_score": 0.9},
                    {"station_rsid": "1A1D", "zip": "22222", "priority_score": 0.2},
                ],
            },
        },
    )

    out1 = school_plan_engine.summarize_school_plan_engine(db, "USAREC", "USAREC", "USAREC", "USAREC", top_n=10)
    out2 = school_plan_engine.summarize_school_plan_engine(db, "USAREC", "USAREC", "USAREC", "USAREC", top_n=10)

    rows1 = out1.get("school_plan_engine", {}).get("prioritized_schools", [])
    rows2 = out2.get("school_plan_engine", {}).get("prioritized_schools", [])
    assert out1.get("status") == "ok"
    assert len(rows1) == 2
    assert rows1 == rows2
    assert rows1[0]["school_id"] == "S1"
    assert rows1[0]["priority_score"] >= rows1[1]["priority_score"]
    assert out1.get("school_plan_engine", {}).get("school_recruiting_plan", [])


def test_school_plan_engine_no_data():
    db = _db()
    db.execute(text("DROP TABLE IF EXISTS schools"))
    db.execute(text("DROP TABLE IF EXISTS fact_school_contacts"))
    db.commit()

    out = school_plan_engine.summarize_school_plan_engine(db, "USAREC", "USAREC", "USAREC", "USAREC")
    assert out.get("status") == "no_data"
    assert out.get("school_plan_engine", {}).get("prioritized_schools") == []


def test_school_plan_engine_invalid_dataset_schema_without_fallback():
    db = _db()
    db.execute(text("DROP TABLE IF EXISTS schools"))
    db.execute(text("DROP TABLE IF EXISTS fact_school_contacts"))
    db.execute(text("CREATE TABLE schools (bad_col TEXT, another_bad_col TEXT)"))
    db.execute(text("INSERT INTO schools(bad_col, another_bad_col) VALUES('x', 'y')"))
    db.commit()

    out = school_plan_engine.summarize_school_plan_engine(db, "USAREC", "USAREC", "USAREC", "USAREC")
    assert out.get("status") == "invalid_dataset_schema"
    assert "schema_error" in (out.get("school_plan_engine") or {})


def test_mission_includes_school_plan_signal_and_recommendation(monkeypatch):
    monkeypatch.setattr(
        mdj,
        "_compute_mission_total",
        lambda *a, **k: mdj.MissionPeriodTotals(start=date(2026, 1, 1), end=date(2026, 1, 31), total=100.0, sample_count=10, source="fact_production.date_key"),
    )

    def _signals(*_a, **_k):
        return {
            "market": {"raw": {"status": "ok"}, "summary": {"overall_market_status": "moderate", "market_capability_score": 0.6}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "market.csv", "rows_used": 1},
            "access": {"raw": {"status": "ok"}, "summary": {"overall_access_status": "access_constrained", "penetration_rate": 0.2}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "schools.csv", "rows_used": 1},
            "execution": {"raw": {"status": "ok"}, "summary": {"overall_execution_status": "execution_degraded", "stall_count": 2}, "data_as_of": "2026-01-01T00:00:00Z"},
            "funnel": {"raw": {"status": "ok"}, "summary": {"overall_funnel_status": "watch", "lead_to_contract_rate": 0.1}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "funnel.csv", "rows_used": 1},
            "accountability": {"raw": {}, "summary": {"classification": "execution_failure", "confidence": "medium"}, "data_as_of": "2026-01-01T00:00:00Z"},
            "loe": {"raw": {}, "summary": {"status_counts": {"met": 1, "at_risk": 2, "not_met": 0, "unknown": 0}, "total_metrics": 3}, "data_as_of": "2026-01-01T00:00:00Z"},
            "targeting": {"raw": {"targeting_engine": {"prioritized_targets": [{"station_rsid": "1A1D", "zip": "11111", "priority_score": 0.9}]}} , "summary": {"recommendations_count": 1, "high_priority_count": 1}, "data_as_of": "2026-01-01T00:00:00Z", "source_dataset_name": "market.csv", "rows_used": 1},
            "school_plan": {
                "raw": {
                    "status": "ok",
                    "school_plan_engine": {
                        "summary": {"total_schools": 1, "priority_school_count": 1, "underengaged_school_count": 1},
                        "prioritized_schools": [{"school_id": "S1"}],
                        "school_recruiting_plan": [{"action": "Increase cadence", "expected_effect": "Raise engagement", "time_horizon": "next 14 days", "rationale": "r", "trace_id": "school-plan:1A1D:11111:S1"}],
                        "source_school_dataset": "schools",
                    },
                },
                "summary": {"total_schools": 1, "priority_school_count": 1, "underengaged_school_count": 1},
                "data_as_of": "2026-01-01T00:00:00Z",
                "source_dataset_name": "schools",
                "rows_used": 1,
            },
        }

    monkeypatch.setattr(mdj, "_collect_signal_summaries", _signals)

    out = mdj.generate_mission_adjustment_justification(
        db=_db(),
        org_id="1A1D",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        include_evidence=True,
        force_refresh=True,
    )

    signal_summaries = out.get("signal_summaries") or {}
    recs = out.get("recommendations") or []
    evidence = out.get("evidence") or []

    assert "school_plan" in signal_summaries
    assert signal_summaries["school_plan"].get("rows_used") == 1
    assert any(r.get("kind") == "school_plan_action" for r in recs)
    assert any(e.get("evidence_id") == "ev-school_plan" for e in evidence)


def test_command_center_and_powerbi_expose_school_plan(monkeypatch):
    fake = {
        "status": "ok",
        "school_plan_engine": {
            "summary": {"total_schools": 1, "priority_school_count": 1},
            "prioritized_schools": [{"school_id": "S1"}],
            "school_recruiting_plan": [{"school_id": "S1", "action": "Increase cadence"}],
        },
    }

    monkeypatch.setattr(command_center.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: fake)
    monkeypatch.setattr(powerbi_feed.school_plan_engine, "summarize_school_plan_engine", lambda *a, **k: fake)
    monkeypatch.setattr(command_center.loe_engine, "summarize_loes", lambda *a, **k: {"status": "ok"})
    monkeypatch.setattr(command_center.targeting_expansion, "recommendations_for_scope", lambda *a, **k: {"recommendations": []})
    monkeypatch.setattr(command_center.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})
    monkeypatch.setattr(command_center.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}}})
    monkeypatch.setattr(command_center.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(command_center.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.ai_recommendation_engine, "generate_recommendation_bundle", lambda *a, **k: {"status": "ok", "recommendations": []})
    monkeypatch.setattr(powerbi_feed.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.funnel_engine, "summarize_funnel_engine", lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.targeting_engine, "summarize_targeting_engine", lambda *a, **k: {"status": "ok", "targeting_engine": {"summary": {}}})
    monkeypatch.setattr(powerbi_feed.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})

    cc = client.get("/api/command-center/overview?scope_type=USAREC&scope_value=USAREC")
    assert cc.status_code == 200
    cc_data = cc.json().get("summary", {}).get("phase2", {})
    assert "school_plan_engine" in cc_data
    assert (cc_data.get("school_plan_engine") or {}).get("school_plan_engine", {}).get("summary", {}).get("total_schools") == 1

    pb = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert pb.status_code == 200
    pb_data = pb.json().get("data", {})
    assert pb_data.get("school_plan_summary", {}).get("total_schools") == 1
    assert isinstance(pb_data.get("school_plan_prioritized_schools"), list)
    assert isinstance(pb_data.get("school_plan_actions"), list)
