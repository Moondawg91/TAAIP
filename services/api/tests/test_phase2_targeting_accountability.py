import os
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import text

from services.api.app import auth, main as app_module, models
from services.api.app.database import SessionLocal, engine
from services.api.app.db import init_db
from services.api.app.models import Base
from services.api.app.models_domain import BurdenSnapshot

client = TestClient(app_module.app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    os.environ.setdefault("TAAIP_DB_PATH", "./taaip_dev.db")
    init_db()


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def _seed_org_and_users(db):
    cmd = db.query(models.Command).filter_by(command="CMD1").first()
    if not cmd:
        cmd = models.Command(command="CMD1", display="CMD1")
        db.add(cmd)
        db.commit()

    bde = db.query(models.Brigade).filter_by(brigade_prefix="1").first()
    if not bde:
        bde = models.Brigade(brigade_prefix="1", display="B1", command_id=cmd.id)
        db.add(bde)
        db.commit()

    bn = db.query(models.Battalion).filter_by(battalion_prefix="1A").first()
    if not bn:
        bn = models.Battalion(battalion_prefix="1A", display="Bn1A", brigade_id=bde.id)
        db.add(bn)
        db.commit()

    co = db.query(models.Company).filter_by(company_prefix="1A1").first()
    if not co:
        co = models.Company(company_prefix="1A1", display="Co1A1", battalion_id=bn.id)
        db.add(co)
        db.commit()

    st = db.query(models.Station).filter_by(rsid="1A1D").first()
    if not st:
        st = models.Station(rsid="1A1D", display="Station1A1D", company_id=co.id)
        db.add(st)
        db.commit()

    zip_rows = [
        ("1A1D", "37011", "MK"),
        ("1A1D", "37012", "MW"),
    ]
    for rsid, zip_code, cat in zip_rows:
        existing = (
            db.query(models.StationZipCoverage)
            .filter(models.StationZipCoverage.station_rsid == rsid, models.StationZipCoverage.zip_code == zip_code)
            .first()
        )
        if not existing:
            db.add(
                models.StationZipCoverage(
                    station_rsid=rsid,
                    zip_code=zip_code,
                    market_category=getattr(models.MarketCategory, cat),
                    source_file="test",
                )
            )
    db.commit()

    for category, weight in [("MK", 5), ("MW", 4), ("MO", 3), ("SU", 2), ("UNK", 1)]:
        existing = db.query(models.MarketCategoryWeights).filter(models.MarketCategoryWeights.category == getattr(models.MarketCategory, category)).first()
        if not existing:
            db.add(models.MarketCategoryWeights(category=getattr(models.MarketCategory, category), weight=weight))
    db.commit()

    users = [
        models.User(username="usarec_admin", role=models.UserRole.USAREC, scope="USAREC"),
        models.User(username="station_view", role=models.UserRole.STATION_VIEW, scope="1A1D"),
        models.User(username="company_cmd", role=models.UserRole.COMPANY_CMD, scope="1A1"),
    ]
    for user in users:
        if not db.query(models.User).filter(models.User.username == user.username).first():
            db.add(user)
    db.commit()

    # Seed burden snapshot and effort/production fact tables.
    if not db.query(BurdenSnapshot).filter(BurdenSnapshot.id == "bs-1").first():
        db.add(
            BurdenSnapshot(
                id="bs-1",
                scope_type="STN",
                scope_value="1A1D",
                reporting_date=date(2026, 1, 1),
                mission_requirement=12,
                recruiter_strength=6,
                burden_ratio=2.0,
            )
        )
        db.commit()

    db.execute(
        text(
            "INSERT OR REPLACE INTO fact_production (id, org_unit_id, date_key, metric_key, metric_value, source_system, import_job_id, created_at, record_status) "
            "VALUES ('fp-1', '1A1D', '2026-01-01', 'contracts', 2.0, 'test', 'job-1', datetime('now'), 'active')"
        )
    )
    db.execute(
        text(
            "INSERT OR REPLACE INTO fact_marketing (id, org_unit_id, date_key, campaign, channel, impressions, engagements, clicks, conversions, cost, source_system, import_job_id, created_at, record_status) "
            "VALUES ('fm-1', '1A1D', '2026-01-01', 'c1', 'social', 1000, 50, 10, 1, 100, 'test', 'job-1', datetime('now'), 'active')"
        )
    )
    db.execute(
        text(
            "INSERT OR REPLACE INTO home_alerts (id, category, title, body, severity, source, created_at, record_status) "
            "VALUES ('ha-1', 'ops', 'Alert', 'Access issue', 'high', 'test', datetime('now'), 'active')"
        )
    )
    db.commit()


def _token_for(db, username):
    user = db.query(models.User).filter(models.User.username == username).one()
    return auth.create_token_for_user(user)


def test_phase2_loe_create_list_and_evaluate():
    db = SessionLocal()
    _seed_org_and_users(db)

    token = _token_for(db, "usarec_admin")
    headers = {"Authorization": f"Bearer {token}"}

    loe = {
        "id": "phase2-loe-1",
        "scope_type": "CO",
        "scope_value": "1A1",
        "title": "Increase Contracts",
        "description": "Improve output in strong market",
        "created_by": "usarec_admin",
    }
    r = client.post("/api/v2/loes", json=loe, headers=headers)
    assert r.status_code == 200

    metric = {
        "id": "phase2-lm-1",
        "loe_id": "phase2-loe-1",
        "metric_name": "contracts",
        "target_value": 100,
        "warn_threshold": 80,
        "fail_threshold": 60,
        "current_value": 72,
    }
    r = client.post("/api/v2/loes/phase2-loe-1/metrics", json=metric, headers=headers)
    assert r.status_code == 200

    r = client.post("/api/v2/loes/phase2-loe-1/evaluate", headers=headers)
    assert r.status_code == 200
    data = r.json().get("data", {})
    assert data.get("evaluated") == 1
    assert data.get("status_counts", {}).get("at_risk") == 1

    r = client.get("/api/v2/loes?scope_type=CO&scope_value=1A1", headers=headers)
    assert r.status_code == 200
    rows = r.json().get("data", [])
    assert any(x.get("id") == "phase2-loe-1" for x in rows)


def test_phase2_targeting_recommendations():
    db = SessionLocal()
    _seed_org_and_users(db)

    token = _token_for(db, "usarec_admin")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v2/targeting/recommendations?scope_type=CO&scope_value=1A1", headers=headers)
    assert r.status_code == 200
    payload = r.json().get("data", {})
    recs = payload.get("recommendations", [])
    assert isinstance(recs, list)
    assert len(recs) > 0


def test_phase2_accountability_classification():
    db = SessionLocal()
    _seed_org_and_users(db)

    token = _token_for(db, "usarec_admin")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v2/accountability/classification?scope_type=CO&scope_value=1A1", headers=headers)
    assert r.status_code == 200
    data = r.json().get("data", {})
    assert data.get("classification") in {
        "market_constrained",
        "access_constrained",
        "effort_misaligned",
        "execution_failure",
        "balanced",
        "insufficient_data",
    }
    assert "supporting_metrics" in data


def test_phase2_loe_rbac_enforcement():
    db = SessionLocal()
    _seed_org_and_users(db)

    station_view_token = _token_for(db, "station_view")
    headers_station = {"Authorization": f"Bearer {station_view_token}"}

    payload = {
        "id": "phase2-loe-rbac-1",
        "scope_type": "STN",
        "scope_value": "1A1D",
        "title": "Blocked for view role",
        "description": "Should be denied",
        "created_by": "station_view",
    }
    r = client.post("/api/v2/loes", json=payload, headers=headers_station)
    assert r.status_code == 403

    company_cmd_token = _token_for(db, "company_cmd")
    headers_company = {"Authorization": f"Bearer {company_cmd_token}"}

    old_policy = os.environ.get("ALLOW_COMPANY_LOE_WRITE")
    if "ALLOW_COMPANY_LOE_WRITE" in os.environ:
        del os.environ["ALLOW_COMPANY_LOE_WRITE"]

    blocked_payload = {
        "id": "phase2-loe-rbac-2",
        "scope_type": "CO",
        "scope_value": "1A1",
        "title": "Blocked by policy",
        "description": "Should be denied",
        "created_by": "company_cmd",
    }
    r = client.post("/api/v2/loes", json=blocked_payload, headers=headers_company)
    assert r.status_code == 403

    os.environ["ALLOW_COMPANY_LOE_WRITE"] = "1"
    allowed_payload = {
        "id": "phase2-loe-rbac-3",
        "scope_type": "CO",
        "scope_value": "1A1",
        "title": "Allowed by policy",
        "description": "Should pass",
        "created_by": "company_cmd",
    }
    r = client.post("/api/v2/loes", json=allowed_payload, headers=headers_company)
    assert r.status_code == 200

    if old_policy is None:
        if "ALLOW_COMPANY_LOE_WRITE" in os.environ:
            del os.environ["ALLOW_COMPANY_LOE_WRITE"]
    else:
        os.environ["ALLOW_COMPANY_LOE_WRITE"] = old_policy
