import os
import csv

from fastapi.testclient import TestClient

from services.api.app.main import app
from services.api.app.routers import command_center, powerbi_feed
from services.api.app.services import funnel_engine


client = TestClient(app)


def _write_funnel_csv(path: str) -> None:
    rows = [
        ["c0", "c1", "c2", "c3", "c4", "c5", "c6"],
        ["L-001", "1A1D", "12345", "2026-01-01", "LEAD APPLICANT INTERVIEW PROCESS CONTRACT DEP", "APPOINT,INTERVIEW,PROCESS,CONTRACT", "1704067200000,1704672000000,1705276800000,1705881600000"],
        ["L-002", "1A1D", "12345", "2026-01-02", "LEAD APPLICANT INTERVIEW PROCESS CONTRACT DEP", "APPOINT,INTERVIEW,PROCESS,CONTRACT", "1704153600000,1704758400000,1705363200000,1705968000000"],
        ["L-003", "1A1E", "12346", "2026-01-03", "LEAD APPLICANT INTERVIEW PROCESS", "APPOINT,INTERVIEW,PROCESS", "1704240000000,1704844800000,1705449600000"],
        ["L-004", "1A1E", "12346", "2026-01-04", "LEAD APPLICANT", "APPOINT,INTERVIEW", "1704326400000,1704931200000"],
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def _write_headerless_realish_funnel_csv(path: str) -> None:
    rows = [
        [
            "1001", "2001", "2000", "hash-a", "M", "2024-01-01", "N", "L", "HS", "", "Y", "AH",
            "INTERESTED - FOLLOW UP", "A", "ACTIVE", "E", "ENLISTED", "", "", "1A1D", "lead1@example.com",
            "DOE", "JANE", "", "100 MAIN", "NASHVILLE", "TN", "37011", "37011", "", "2024", "615",
            "5551111", "6155551111", "B", "PROSPECT", "", "", "", "1704067200000,1704153600000,1704672000000,1705276800000",
            "B, C, D, Z", "PROSPECT, APPLICANT, DELAYED ENTRY PROGRAM, SHIPPED", "FF, IA, DF, ZB",
            "FACE TO FACE, APPOINTMENT-INITIAL, FUTURE SOLDIER TRAINING, VALIDATE AFTER SHIP VERIFIED"
        ],
        [
            "1002", "2002", "2001", "hash-b", "F", "2024-01-03", "N", "L", "HS", "", "Y", "AH",
            "INTERESTED - FOLLOW UP", "A", "ACTIVE", "E", "ENLISTED", "", "", "1A1E", "lead2@example.com",
            "SMITH", "JOHN", "", "101 MAIN", "NASHVILLE", "TN", "37012", "37012", "", "2024", "615",
            "5552222", "6155552222", "A", "LEAD", "", "", "", "1704240000000,1704326400000",
            "A, B", "LEAD, PROSPECT", "FF, IA", "FACE TO FACE, APPOINTMENT-INITIAL"
        ],
        [
            "1003", "2003", "2002", "hash-c", "M", "2024-01-05", "N", "L", "HS", "", "Y", "AH",
            "INTERESTED - FOLLOW UP", "A", "ACTIVE", "E", "ENLISTED", "", "", "1A1D", "lead3@example.com",
            "BROWN", "ALEX", "", "102 MAIN", "NASHVILLE", "TN", "37013", "37013", "", "2024", "615",
            "5553333", "6155553333", "C", "APPLICANT", "", "", "", "1704412800000,1704499200000,1704585600000",
            "B, C, C", "PROSPECT, APPLICANT, APPLICANT", "FF, IA, TP", "FACE TO FACE, APPOINTMENT-INITIAL, TEST/PHYSICAL"
        ]
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def _write_invalid_funnel_csv(path: str) -> None:
    rows = [
        ["bad", "shape", "only"],
        ["x", "y", "z"],
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def test_funnel_engine_summary_from_uploaded_csv(tmp_path):
    csv_path = str(tmp_path / "Recruiting Funnel Enriched.csv")
    _write_funnel_csv(csv_path)
    old = os.environ.get("TAAIP_FUNNEL_DATASET_PATH")
    os.environ["TAAIP_FUNNEL_DATASET_PATH"] = csv_path
    try:
        out = funnel_engine.summarize_funnel_engine(
            db=None,
            scope_type="USAREC",
            scope_value="USAREC",
            actor_scope_type="USAREC",
            actor_scope_value="USAREC",
            top_n=10,
        )
    finally:
        if old is None:
            os.environ.pop("TAAIP_FUNNEL_DATASET_PATH", None)
        else:
            os.environ["TAAIP_FUNNEL_DATASET_PATH"] = old

    assert out.get("status") == "ok"
    summary = (out.get("funnel_engine") or {}).get("summary") or {}
    assert summary.get("total_leads", 0) >= 4
    assert "lead_to_contract_rate" in summary
    assert "largest_dropoff_stage" in summary
    assert isinstance((out.get("funnel_engine") or {}).get("prioritized_funnel_gaps"), list)


def test_funnel_engine_repairs_headerless_real_mapping_path(tmp_path):
    csv_path = str(tmp_path / "Recruiting Funnel Enriched.csv")
    _write_headerless_realish_funnel_csv(csv_path)
    old = os.environ.get("TAAIP_FUNNEL_DATASET_PATH")
    os.environ["TAAIP_FUNNEL_DATASET_PATH"] = csv_path
    try:
        out = funnel_engine.summarize_funnel_engine(
            db=None,
            scope_type="USAREC",
            scope_value="USAREC",
            actor_scope_type="USAREC",
            actor_scope_value="USAREC",
            top_n=10,
        )
    finally:
        if old is None:
            os.environ.pop("TAAIP_FUNNEL_DATASET_PATH", None)
        else:
            os.environ["TAAIP_FUNNEL_DATASET_PATH"] = old

    assert out.get("status") == "ok"
    summary = (out.get("funnel_engine") or {}).get("summary") or {}
    assert summary.get("total_leads") == 3
    assert summary.get("total_contracts", 0) >= 1
    assert len((out.get("funnel_engine") or {}).get("prioritized_funnel_gaps") or []) >= 1


def test_funnel_engine_invalid_schema_when_required_fields_cannot_be_derived(tmp_path):
    csv_path = str(tmp_path / "Recruiting Funnel Enriched.csv")
    _write_invalid_funnel_csv(csv_path)
    old = os.environ.get("TAAIP_FUNNEL_DATASET_PATH")
    os.environ["TAAIP_FUNNEL_DATASET_PATH"] = csv_path
    try:
        out = funnel_engine.summarize_funnel_engine(
            db=None,
            scope_type="USAREC",
            scope_value="USAREC",
            actor_scope_type="USAREC",
            actor_scope_value="USAREC",
            top_n=10,
        )
    finally:
        if old is None:
            os.environ.pop("TAAIP_FUNNEL_DATASET_PATH", None)
        else:
            os.environ["TAAIP_FUNNEL_DATASET_PATH"] = old

    assert out.get("status") == "invalid_dataset_schema"
    assert (out.get("funnel_engine") or {}).get("schema_error")


def test_powerbi_operational_dataset_includes_funnel_summary(monkeypatch):
    monkeypatch.setattr(
        powerbi_feed.funnel_engine,
        "summarize_funnel_engine",
        lambda *args, **kwargs: {"status": "ok", "funnel_engine": {"summary": {"overall_funnel_status": "watch", "total_leads": 10}}},
    )

    r = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("status") == "ok"
    data = payload.get("data") or {}
    assert "funnel_engine_summary" in data
    assert data.get("funnel_engine_summary", {}).get("total_leads") == 10


def test_command_center_phase2_includes_funnel_engine(monkeypatch):
    monkeypatch.setattr(command_center.loe_engine, "summarize_loes", lambda *a, **k: {"rag": "amber", "status_counts": {}, "total_metrics": 0})
    monkeypatch.setattr(command_center.targeting_expansion, "recommendations_for_scope", lambda *a, **k: {"recommendations": []})
    monkeypatch.setattr(command_center.accountability_engine, "classify_scope", lambda *a, **k: {"classification": "balanced"})
    monkeypatch.setattr(command_center.market_engine, "summarize_market_engine", lambda *a, **k: {"status": "ok", "market_engine": {"summary": {}}})
    monkeypatch.setattr(command_center.school_access, "summarize_school_access", lambda *a, **k: {"status": "ok", "school_access": {"summary": {}}})
    monkeypatch.setattr(command_center.execution_quality, "summarize_execution_quality", lambda *a, **k: {"status": "ok", "execution_quality": {"summary": {}}})
    monkeypatch.setattr(command_center.ai_recommendation_engine, "generate_recommendation_bundle", lambda *a, **k: {"recommendations": []})
    monkeypatch.setattr(
        command_center.funnel_engine,
        "summarize_funnel_engine",
        lambda *a, **k: {"status": "ok", "funnel_engine": {"summary": {"overall_funnel_status": "critical"}}},
    )

    r = client.get("/api/command-center/overview?scope_type=USAREC&scope_value=USAREC")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("status") == "ok"
    phase2 = (payload.get("summary") or {}).get("phase2") or {}
    assert "funnel_engine" in phase2
    assert (phase2.get("funnel_engine") or {}).get("status") == "ok"
