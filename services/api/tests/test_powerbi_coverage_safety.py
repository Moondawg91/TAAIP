import base64
import json

from fastapi.testclient import TestClient

from services.api.app.db import connect
from services.api.app.main import app


client = TestClient(app)


def _jwt_like(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}.signature"


def _admin_headers():
    token = _jwt_like({"sub": "admin", "roles": ["system_admin"], "permissions": ["admin.permissions.manage"], "scopes": []})
    return {"Authorization": f"Bearer {token}"}


def test_powerbi_coverage_summary_missing_table_returns_controlled_no_data():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS coverage_summary")
    conn.commit()
    conn.close()

    r = client.get("/api/powerbi/coverage/summary", headers=_admin_headers())
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert body == []


def test_powerbi_coverage_summary_with_table_returns_rows():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS coverage_summary")
    cur.execute(
        """
        CREATE TABLE coverage_summary(
            id INTEGER PRIMARY KEY,
            scope TEXT,
            as_of TEXT,
            category TEXT,
            count INTEGER,
            source TEXT,
            notes TEXT
        )
        """
    )
    cur.execute(
        "INSERT INTO coverage_summary(scope, as_of, category, count, source, notes) VALUES (?,?,?,?,?,?)",
        ("USAREC", "2026-04-14", "schools", 10, "test", "ok"),
    )
    conn.commit()
    conn.close()

    r = client.get("/api/powerbi/coverage/summary?scope=USAREC", headers=_admin_headers())
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0].get("scope") == "USAREC"
