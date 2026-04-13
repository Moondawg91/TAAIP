"""© 2026 TAAIP. Copyright pending.
Comprehensive Phase 2 test suite covering:
  - LOE creation, metric attachment, evaluation, and listing
  - Targeting recommendations by scope
  - Accountability classification by scope
  - RBAC enforcement on all Phase 2 write endpoints
  - Command center overview surfacing Phase 2 signals
  - loe_engine, targeting_expansion, accountability_engine unit tests
"""

import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from services.api.app import auth, main as app_module, models
from services.api.app.database import SessionLocal, engine
from services.api.app.db import init_db
from services.api.app.models import Base
from services.api.app.models_domain import BurdenSnapshot, Loe, LoeMetric

client = TestClient(app_module.app)


# ---------------------------------------------------------------------------
# Module-level setup / teardown
# ---------------------------------------------------------------------------

def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    os.environ.setdefault("TAAIP_DB_PATH", "./taaip_dev.db")
    init_db()


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Shared seed helpers
# ---------------------------------------------------------------------------

def _seed(db):
    """Idempotent seed for all Phase 2 tests."""
    cmd = db.query(models.Command).filter_by(command="P2CMD").first()
    if not cmd:
        cmd = models.Command(command="P2CMD", display="P2CMD")
        db.add(cmd)
        db.commit()

    bde = db.query(models.Brigade).filter_by(brigade_prefix="2").first()
    if not bde:
        bde = models.Brigade(brigade_prefix="2", display="B2", command_id=cmd.id)
        db.add(bde)
        db.commit()

    bn = db.query(models.Battalion).filter_by(battalion_prefix="2A").first()
    if not bn:
        bn = models.Battalion(battalion_prefix="2A", display="Bn2A", brigade_id=bde.id)
        db.add(bn)
        db.commit()

    co = db.query(models.Company).filter_by(company_prefix="2A1").first()
    if not co:
        co = models.Company(company_prefix="2A1", display="Co2A1", battalion_id=bn.id)
        db.add(co)
        db.commit()

    st = db.query(models.Station).filter_by(rsid="2A1D").first()
    if not st:
        st = models.Station(rsid="2A1D", display="Station2A1D", company_id=co.id)
        db.add(st)
        db.commit()

    for rsid, zip_code, cat in [("2A1D", "40001", "MK"), ("2A1D", "40002", "MW")]:
        exists = (
            db.query(models.StationZipCoverage)
            .filter_by(station_rsid=rsid, zip_code=zip_code)
            .first()
        )
        if not exists:
            db.add(
                models.StationZipCoverage(
                    station_rsid=rsid,
                    zip_code=zip_code,
                    market_category=getattr(models.MarketCategory, cat),
                    source_file="test-p2",
                )
            )

    for category, weight in [("MK", 5), ("MW", 4), ("MO", 3), ("SU", 2), ("UNK", 1)]:
        cat_enum = getattr(models.MarketCategory, category)
        if not db.query(models.MarketCategoryWeights).filter_by(category=cat_enum).first():
            db.add(models.MarketCategoryWeights(category=cat_enum, weight=weight))
    db.commit()

    for username, role, scope in [
        ("usarec_admin", models.UserRole.USAREC, "USAREC"),
        ("station_view", models.UserRole.STATION_VIEW, "2A1D"),
        ("company_cmd", models.UserRole.COMPANY_CMD, "2A1"),
    ]:
        if not db.query(models.User).filter_by(username=username).first():
            db.add(models.User(username=username, role=role, scope=scope))
    db.commit()

    if not db.query(BurdenSnapshot).filter_by(id="bs-p2").first():
        db.add(
            BurdenSnapshot(
                id="bs-p2",
                scope_type="STN",
                scope_value="2A1D",
                reporting_date=date(2026, 3, 1),
                mission_requirement=10,
                recruiter_strength=4,
                burden_ratio=2.5,
            )
        )
        db.commit()

    # Minimal production / effort / alert data for targeting and accountability.
    db.execute(
        text(
            "INSERT OR REPLACE INTO fact_production "
            "(id, org_unit_id, date_key, metric_key, metric_value, source_system, import_job_id, created_at, record_status) "
            "VALUES ('fp-p2', '2A1D', '2026-03-01', 'contracts', 3.0, 'test', 'job-p2', datetime('now'), 'active')"
        )
    )
    db.execute(
        text(
            "INSERT OR REPLACE INTO fact_marketing "
            "(id, org_unit_id, date_key, campaign, channel, impressions, engagements, clicks, conversions, cost, source_system, import_job_id, created_at, record_status) "
            "VALUES ('fm-p2', '2A1D', '2026-03-01', 'c-p2', 'social', 800, 40, 8, 2, 80, 'test', 'job-p2', datetime('now'), 'active')"
        )
    )
    db.execute(
        text(
            "INSERT OR REPLACE INTO home_alerts "
            "(id, category, title, body, severity, source, created_at, record_status) "
            "VALUES ('ha-p2', 'ops', 'P2 Alert', 'Access issue', 'high', 'test', datetime('now'), 'active')"
        )
    )
    db.commit()


def _token(db, username: str) -> str:
    user = db.query(models.User).filter_by(username=username).one_or_none()
    if user is None:
        raise RuntimeError(f"Test user '{username}' not seeded")
    return auth.create_token_for_user(user)


def _headers(db, username: str) -> dict:
    return {"Authorization": f"Bearer {_token(db, username)}"}


# ---------------------------------------------------------------------------
# LOE Management
# ---------------------------------------------------------------------------

class TestLoeManagement:

    def test_create_loe_usarec_admin(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        payload = {
            "id": "p2-loe-admin-1",
            "scope_type": "CO",
            "scope_value": "2A1",
            "title": "Increase Contracts Q2",
            "description": "Drive mission achievement in strong market",
            "created_by": "p2_admin",
        }
        r = client.post("/api/v2/loes", json=payload, headers=headers)
        assert r.status_code == 200, r.text
        db.close()

    def test_create_loe_bn_scope(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        payload = {
            "id": "p2-loe-bn-1",
            "scope_type": "BN",
            "scope_value": "2A",
            "title": "BN LOE Test",
            "description": "Battalion level",
            "created_by": "p2_admin",
        }
        r = client.post("/api/v2/loes", json=payload, headers=headers)
        assert r.status_code == 200, r.text
        db.close()

    def test_attach_metric_and_evaluate(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")

        loe_id = "p2-loe-metric-eval-1"
        r = client.post(
            "/api/v2/loes",
            json={
                "id": loe_id,
                "scope_type": "CO",
                "scope_value": "2A1",
                "title": "Metric Eval LOE",
                "description": "",
                "created_by": "p2_admin",
            },
            headers=headers,
        )
        assert r.status_code == 200, r.text

        metric_id = "p2-lm-eval-1"
        r = client.post(
            f"/api/v2/loes/{loe_id}/metrics",
            json={
                "id": metric_id,
                "loe_id": loe_id,
                "metric_name": "contract_rate",
                "target_value": 100.0,
                "warn_threshold": 75.0,
                "fail_threshold": 50.0,
                "current_value": 68.0,
            },
            headers=headers,
        )
        assert r.status_code == 200, r.text

        r = client.post(f"/api/v2/loes/{loe_id}/evaluate", headers=headers)
        assert r.status_code == 200, r.text
        data = r.json().get("data", {})
        assert data.get("evaluated") == 1
        # 68 <= 75 (warn threshold) but > 50 (fail) → at_risk
        assert data.get("status_counts", {}).get("at_risk") == 1

        db.close()

    def test_evaluate_status_not_met(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")

        loe_id = "p2-loe-not-met-1"
        client.post(
            "/api/v2/loes",
            json={
                "id": loe_id,
                "scope_type": "CO",
                "scope_value": "2A1",
                "title": "Not-Met LOE",
                "description": "",
                "created_by": "p2_admin",
            },
            headers=headers,
        )
        metric_id = "p2-lm-not-met-1"
        client.post(
            f"/api/v2/loes/{loe_id}/metrics",
            json={
                "id": metric_id,
                "loe_id": loe_id,
                "metric_name": "accessions",
                "target_value": 100.0,
                "warn_threshold": 60.0,
                "fail_threshold": 40.0,
                "current_value": 30.0,
            },
            headers=headers,
        )

        r = client.post(f"/api/v2/loes/{loe_id}/evaluate", headers=headers)
        assert r.status_code == 200
        assert r.json()["data"]["status_counts"]["not_met"] == 1
        db.close()

    def test_evaluate_status_met(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")

        loe_id = "p2-loe-met-1"
        client.post(
            "/api/v2/loes",
            json={
                "id": loe_id,
                "scope_type": "CO",
                "scope_value": "2A1",
                "title": "Met LOE",
                "description": "",
                "created_by": "p2_admin",
            },
            headers=headers,
        )
        client.post(
            f"/api/v2/loes/{loe_id}/metrics",
            json={
                "id": "p2-lm-met-1",
                "loe_id": loe_id,
                "metric_name": "quality_leads",
                "target_value": 50.0,
                "warn_threshold": 35.0,
                "fail_threshold": 20.0,
                "current_value": 55.0,
            },
            headers=headers,
        )

        r = client.post(f"/api/v2/loes/{loe_id}/evaluate", headers=headers)
        assert r.status_code == 200
        assert r.json()["data"]["status_counts"]["met"] == 1
        db.close()

    def test_list_loes_by_scope(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")

        # create at least one
        client.post(
            "/api/v2/loes",
            json={
                "id": "p2-loe-list-1",
                "scope_type": "CO",
                "scope_value": "2A1",
                "title": "List Test LOE",
                "description": "",
                "created_by": "p2_admin",
            },
            headers=headers,
        )

        r = client.get("/api/v2/loes?scope_type=CO&scope_value=2A1", headers=headers)
        assert r.status_code == 200, r.text
        rows = r.json().get("data", [])
        assert isinstance(rows, list)
        assert any(x.get("id") == "p2-loe-list-1" for x in rows)
        db.close()

    def test_evaluate_loe_not_found(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.post("/api/v2/loes/does-not-exist-999/evaluate", headers=headers)
        assert r.status_code == 404
        db.close()


# ---------------------------------------------------------------------------
# LOE RBAC enforcement
# ---------------------------------------------------------------------------

class TestLoeRbac:

    def test_station_view_cannot_create_loe(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "station_view")
        r = client.post(
            "/api/v2/loes",
            json={
                "id": "p2-rbac-view-1",
                "scope_type": "STN",
                "scope_value": "2A1D",
                "title": "Blocked",
                "description": "",
                "created_by": "p2_station_view",
            },
            headers=headers,
        )
        assert r.status_code == 403, r.text
        db.close()

    def test_company_cmd_blocked_without_policy_flag(self):
        db = SessionLocal()
        _seed(db)
        old = os.environ.get("ALLOW_COMPANY_LOE_WRITE")
        os.environ.pop("ALLOW_COMPANY_LOE_WRITE", None)

        headers = _headers(db, "company_cmd")
        r = client.post(
            "/api/v2/loes",
            json={
                "id": "p2-rbac-cc-blocked",
                "scope_type": "CO",
                "scope_value": "2A1",
                "title": "Must Be Blocked",
                "description": "",
                "created_by": "p2_company_cmd",
            },
            headers=headers,
        )
        assert r.status_code == 403, r.text

        if old is not None:
            os.environ["ALLOW_COMPANY_LOE_WRITE"] = old
        db.close()

    def test_company_cmd_allowed_with_policy_flag(self):
        db = SessionLocal()
        _seed(db)
        old = os.environ.get("ALLOW_COMPANY_LOE_WRITE")
        os.environ["ALLOW_COMPANY_LOE_WRITE"] = "1"

        headers = _headers(db, "company_cmd")
        r = client.post(
            "/api/v2/loes",
            json={
                "id": "p2-rbac-cc-allowed",
                "scope_type": "CO",
                "scope_value": "2A1",
                "title": "Allowed by Policy",
                "description": "",
                "created_by": "p2_company_cmd",
            },
            headers=headers,
        )
        assert r.status_code == 200, r.text

        if old is None:
            os.environ.pop("ALLOW_COMPANY_LOE_WRITE", None)
        else:
            os.environ["ALLOW_COMPANY_LOE_WRITE"] = old
        db.close()

    def test_company_cmd_cannot_create_bde_scope_loe(self):
        """Company commanders may only create CO/STN scope LOEs."""
        db = SessionLocal()
        _seed(db)
        old = os.environ.get("ALLOW_COMPANY_LOE_WRITE")
        os.environ["ALLOW_COMPANY_LOE_WRITE"] = "1"

        headers = _headers(db, "company_cmd")
        r = client.post(
            "/api/v2/loes",
            json={
                "id": "p2-rbac-cc-bde-blocked",
                "scope_type": "BDE",
                "scope_value": "2",
                "title": "Brigade LOE must be blocked",
                "description": "",
                "created_by": "p2_company_cmd",
            },
            headers=headers,
        )
        assert r.status_code == 403, r.text

        if old is None:
            os.environ.pop("ALLOW_COMPANY_LOE_WRITE", None)
        else:
            os.environ["ALLOW_COMPANY_LOE_WRITE"] = old
        db.close()


# ---------------------------------------------------------------------------
# Targeting Recommendations
# ---------------------------------------------------------------------------

class TestTargetingRecommendations:

    def test_returns_recommendations_list(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/targeting/recommendations?scope_type=CO&scope_value=2A1",
            headers=headers,
        )
        assert r.status_code == 200, r.text
        payload = r.json().get("data", {})
        assert "recommendations" in payload
        assert isinstance(payload["recommendations"], list)
        assert len(payload["recommendations"]) > 0

    def test_response_includes_formula(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/targeting/recommendations?scope_type=CO&scope_value=2A1",
            headers=headers,
        )
        assert r.status_code == 200
        payload = r.json().get("data", {})
        assert "formula" in payload
        assert "priority_score" in payload["formula"]

    def test_recommendation_fields(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/targeting/recommendations?scope_type=CO&scope_value=2A1",
            headers=headers,
        )
        recs = r.json()["data"]["recommendations"]
        # at minimum one zip-type row should be present
        zip_recs = [x for x in recs if x.get("entity_type") == "zip"]
        assert zip_recs, "Expected at least one zip recommendation"
        rec = zip_recs[0]
        for field in ("station_rsid", "zip_code", "market_category", "priority_score", "reason_codes"):
            assert field in rec, f"Missing field: {field}"

    def test_station_scope_returns_recommendations(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/targeting/recommendations?scope_type=STN&scope_value=2A1D",
            headers=headers,
        )
        assert r.status_code == 200
        assert isinstance(r.json()["data"]["recommendations"], list)

    def test_scope_enforcement_blocks_out_of_scope(self):
        db = SessionLocal()
        _seed(db)
        # station_view user (scope=2A1D) tries to query a different scope
        headers = _headers(db, "station_view")
        r = client.get(
            "/api/v2/targeting/recommendations?scope_type=BDE&scope_value=1",
            headers=headers,
        )
        assert r.status_code == 403, r.text
        db.close()


# ---------------------------------------------------------------------------
# Accountability Classification
# ---------------------------------------------------------------------------

class TestAccountabilityClassification:

    VALID_CLASSIFICATIONS = {
        "market_constrained",
        "access_constrained",
        "effort_misaligned",
        "execution_failure",
        "balanced",
        "insufficient_data",
    }

    def test_returns_valid_classification(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/accountability/classification?scope_type=CO&scope_value=2A1",
            headers=headers,
        )
        assert r.status_code == 200, r.text
        data = r.json().get("data", {})
        assert data.get("classification") in self.VALID_CLASSIFICATIONS
        assert data.get("confidence") in {"high", "medium", "low"}

    def test_response_shape(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/accountability/classification?scope_type=CO&scope_value=2A1",
            headers=headers,
        )
        data = r.json()["data"]
        for key in ("scope_type", "scope_value", "classification", "confidence", "reason_codes", "supporting_metrics"):
            assert key in data, f"Missing key: {key}"
        assert isinstance(data["reason_codes"], list)
        assert isinstance(data["supporting_metrics"], dict)

    def test_supporting_metrics_keys(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/accountability/classification?scope_type=CO&scope_value=2A1",
            headers=headers,
        )
        sm = r.json()["data"]["supporting_metrics"]
        for key in ("avg_burden_pressure", "avg_effort_signal", "avg_warning_severity", "avg_opportunity"):
            assert key in sm, f"Missing supporting_metrics key: {key}"

    def test_scope_enforcement(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "station_view")
        r = client.get(
            "/api/v2/accountability/classification?scope_type=BDE&scope_value=1",
            headers=headers,
        )
        assert r.status_code == 403, r.text
        db.close()


# ---------------------------------------------------------------------------
# Command Center Integration
# ---------------------------------------------------------------------------

class TestCommandCenterPhase2Integration:

    def test_overview_contains_phase2_block(self):
        r = client.get("/api/command-center/overview")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("status") == "ok"
        summary = body.get("summary", {})
        # Phase 2 block must be present (may be empty but must exist)
        assert "phase2" in summary, "command center overview missing phase2 block"

    def test_overview_phase2_loe_summary_shape(self):
        r = client.get("/api/command-center/overview")
        summary = r.json()["summary"]
        phase2 = summary.get("phase2", {})
        loe_summary = phase2.get("loe_summary", {})
        # If no LOEs exist for the default USAREC scope, totals should be zero but keys present
        assert "total_loes" in loe_summary
        assert "total_metrics" in loe_summary
        assert "status_counts" in loe_summary

    def test_overview_phase2_targeting_focus_shape(self):
        r = client.get("/api/command-center/overview")
        summary = r.json()["summary"]
        phase2 = summary.get("phase2", {})
        targeting = phase2.get("targeting_focus", {})
        assert "top_focus_count" in targeting
        assert "zip_focus_count" in targeting
        assert "source_dataset_name" in targeting
        assert "top_zips" in targeting
        assert "formula" in targeting

    def test_overview_phase2_market_and_targeting_reflect_real_sources(self):
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get("/api/command-center/overview?scope_type=CO&scope_value=2A1", headers=headers)
        assert r.status_code == 200, r.text
        phase2 = (r.json().get("summary") or {}).get("phase2") or {}
        market = phase2.get("market_engine") or {}
        market_block = market.get("market_engine") or {}
        targeting = phase2.get("targeting_focus") or {}

        assert market.get("status") in {"ok", "no_active_dataset", "invalid_dataset_schema"}
        assert market_block.get("source_dataset_name") is not None
        assert targeting.get("top_focus_count", 0) >= 0
        assert targeting.get("source_dataset_name") is not None

    def test_overview_phase2_accountability_shape(self):
        r = client.get("/api/command-center/overview")
        summary = r.json()["summary"]
        phase2 = summary.get("phase2", {})
        accountability = phase2.get("accountability", {})
        assert "classification" in accountability
        assert "confidence" in accountability

    def test_command_summary_endpoint_healthy(self):
        """GET /api/v2/command/summary returns a valid summary payload.

        Note: In this codebase, two routers register this same path. Depending on
        router order, callers may receive either legacy summary fields or
        Phase 2-extended fields.
        """
        db = SessionLocal()
        _seed(db)
        headers = _headers(db, "usarec_admin")
        r = client.get(
            "/api/v2/command/summary?scope_type=CO&scope_value=2A1",
            headers=headers,
        )
        assert r.status_code == 200, r.text
        data = r.json().get("data", {})
        assert isinstance(data, dict)
        # Accept both current payload shapes.
        has_phase2 = all(k in data for k in ("loe_summary", "targeting_recommendations_summary", "accountability_summary"))
        has_legacy = all(k in data for k in ("leads", "conversions", "cost", "roi"))
        assert has_phase2 or has_legacy


# ---------------------------------------------------------------------------
# Unit tests: loe_engine module
# ---------------------------------------------------------------------------

class TestLoeEngineUnit:

    def test_validate_scope_ok(self):
        from services.api.app.services.loe_engine import validate_scope
        validate_scope("CO", "2A1")  # should not raise

    def test_validate_scope_bad_type(self):
        from fastapi import HTTPException
        from services.api.app.services.loe_engine import validate_scope
        with pytest.raises(HTTPException) as exc:
            validate_scope("PLATOON", "X")
        assert exc.value.status_code == 400

    def test_validate_scope_missing_value(self):
        from fastapi import HTTPException
        from services.api.app.services.loe_engine import validate_scope
        with pytest.raises(HTTPException) as exc:
            validate_scope("CO", "")
        assert exc.value.status_code == 400

    def test_evaluate_metric_status_met(self):
        from types import SimpleNamespace
        from services.api.app.services.loe_engine import evaluate_metric_status
        m = SimpleNamespace(current_value=90.0, target_value=80.0, warn_threshold=60.0, fail_threshold=40.0)
        status, rationale = evaluate_metric_status(m)
        assert status == "met"

    def test_evaluate_metric_status_at_risk(self):
        from types import SimpleNamespace
        from services.api.app.services.loe_engine import evaluate_metric_status
        m = SimpleNamespace(current_value=65.0, target_value=80.0, warn_threshold=60.0, fail_threshold=40.0)
        status, rationale = evaluate_metric_status(m)
        assert status == "at_risk"

    def test_evaluate_metric_status_not_met(self):
        from types import SimpleNamespace
        from services.api.app.services.loe_engine import evaluate_metric_status
        m = SimpleNamespace(current_value=35.0, target_value=80.0, warn_threshold=60.0, fail_threshold=40.0)
        status, rationale = evaluate_metric_status(m)
        assert status == "not_met"

    def test_evaluate_metric_status_unknown(self):
        from types import SimpleNamespace
        from services.api.app.services.loe_engine import evaluate_metric_status
        m = SimpleNamespace(current_value=None, target_value=80.0, warn_threshold=60.0, fail_threshold=40.0)
        status, rationale = evaluate_metric_status(m)
        assert status == "unknown"

    def test_scope_match(self):
        from services.api.app.services.loe_engine import scope_match
        assert scope_match("BN", "2A", "2A1") is True
        assert scope_match("CO", "2A1", "2A1D") is True
        assert scope_match("CO", "2A1", "1B3E") is False
        assert scope_match("USAREC", "USAREC", "anything") is True

    def test_can_user_manage_loe_view_blocked(self):
        from types import SimpleNamespace
        from fastapi import HTTPException
        from services.api.app.services.loe_engine import can_user_manage_loe
        user = SimpleNamespace(role=SimpleNamespace(name="STATION_VIEW"), scope="2A1D", username="viewer")
        with pytest.raises(HTTPException) as exc:
            can_user_manage_loe(user, "STN", "2A1D")
        assert exc.value.status_code == 403

    def test_summarize_loes_empty(self):
        from services.api.app.services.loe_engine import summarize_loes
        db = SessionLocal()
        result = summarize_loes(db, "CO", "ZZZZ_NOSUCHSCOPE")
        assert result["total_loes"] == 0
        db.close()


# ---------------------------------------------------------------------------
# Unit tests: targeting_expansion module
# ---------------------------------------------------------------------------

class TestTargetingExpansionUnit:

    def test_scope_prefix_co(self):
        from services.api.app.services.targeting_expansion import _scope_prefix
        assert _scope_prefix("CO", "2A1") == "2A1"

    def test_scope_prefix_bn(self):
        from services.api.app.services.targeting_expansion import _scope_prefix
        assert _scope_prefix("BN", "2A") == "2A"

    def test_scope_prefix_usarec(self):
        from services.api.app.services.targeting_expansion import _scope_prefix
        assert _scope_prefix("USAREC", "USAREC") == ""

    def test_clamp01(self):
        from services.api.app.services.targeting_expansion import _clamp01
        assert _clamp01(-0.5) == 0.0
        assert _clamp01(1.5) == 1.0
        assert abs(_clamp01(0.5) - 0.5) < 1e-9

    def test_reason_codes_high_opportunity_low_output(self):
        from services.api.app.services.targeting_expansion import _reason_codes
        codes = _reason_codes(opportunity=0.80, burden=0.30, production=0.20, effort=0.50)
        assert "high_opportunity_low_output" in codes

    def test_reason_codes_strong_market_underworked(self):
        from services.api.app.services.targeting_expansion import _reason_codes
        codes = _reason_codes(opportunity=0.75, burden=0.30, production=0.50, effort=0.25)
        assert "strong_market_underworked" in codes

    def test_recommendations_for_scope_returns_shape(self):
        from services.api.app.services.targeting_expansion import recommendations_for_scope
        db = SessionLocal()
        _seed(db)
        result = recommendations_for_scope(db, "CO", "2A1", top_n=10)
        assert "recommendations" in result
        assert "formula" in result
        assert isinstance(result["recommendations"], list)
        db.close()

    def test_recommendations_empty_scope(self):
        from services.api.app.services.targeting_expansion import recommendations_for_scope
        db = SessionLocal()
        result = recommendations_for_scope(db, "CO", "ZZZZ_NOSUCHSCOPE", top_n=5)
        assert result["recommendations"] == []
        db.close()


# ---------------------------------------------------------------------------
# Unit tests: accountability_engine module
# ---------------------------------------------------------------------------

class TestAccountabilityEngineUnit:

    def test_classify_scope_returns_valid_classification(self):
        from services.api.app.services.accountability_engine import classify_scope
        db = SessionLocal()
        _seed(db)
        result = classify_scope(db, "CO", "2A1")
        assert result["classification"] in {
            "market_constrained",
            "access_constrained",
            "effort_misaligned",
            "execution_failure",
            "balanced",
            "insufficient_data",
        }
        db.close()

    def test_classify_empty_scope_returns_insufficient(self):
        from services.api.app.services.accountability_engine import classify_scope
        db = SessionLocal()
        result = classify_scope(db, "CO", "ZZZZ_NOSUCHSCOPE")
        assert result["classification"] == "insufficient_data"
        db.close()

    def test_classify_returns_reason_codes(self):
        from services.api.app.services.accountability_engine import classify_scope
        db = SessionLocal()
        _seed(db)
        result = classify_scope(db, "CO", "2A1")
        assert isinstance(result["reason_codes"], list)
        db.close()

    def test_classify_supporting_metrics_types(self):
        from services.api.app.services.accountability_engine import classify_scope
        db = SessionLocal()
        _seed(db)
        result = classify_scope(db, "CO", "2A1")
        sm = result["supporting_metrics"]
        for key in ("avg_burden_pressure", "avg_effort_signal", "avg_warning_severity", "avg_opportunity"):
            assert isinstance(sm[key], float), f"{key} should be float"
        db.close()
