import base64
import json

from fastapi.testclient import TestClient

from services.api.app import auth
from services.api.app.main import app


client = TestClient(app)


def _jwt_like(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}.signature"


def test_demo_mode_rejects_no_token_on_protected_endpoints(monkeypatch):
    monkeypatch.setenv("TAAIP_DEMO_MODE", "1")
    monkeypatch.setattr(auth, "LOCAL_DEV_AUTH_BYPASS", False)
    monkeypatch.setattr(auth, "TAAIP_MASTER_MODE", False)

    me = client.get("/api/me")
    refresh = client.get("/api/refresh/sources")

    assert me.status_code == 401
    assert refresh.status_code in {401, 403}


def test_refresh_sources_role_enforcement_in_demo_mode(monkeypatch):
    monkeypatch.setenv("TAAIP_DEMO_MODE", "1")
    monkeypatch.setenv("LOCAL_DEV_AUTH_BYPASS", "0")
    monkeypatch.setenv("TAAIP_MASTER_MODE", "0")

    admin_token = _jwt_like({"sub": "admin", "roles": ["system_admin"], "permissions": ["admin.permissions.manage"], "scopes": []})
    commander_token = _jwt_like({"sub": "commander", "roles": ["co_cmd"], "permissions": [], "scopes": []})
    operator_token = _jwt_like({"sub": "operator420t", "roles": ["420t_admin"], "permissions": [], "scopes": []})

    admin_response = client.get("/api/refresh/sources", headers={"Authorization": f"Bearer {admin_token}"})
    commander_response = client.get("/api/refresh/sources", headers={"Authorization": f"Bearer {commander_token}"})
    operator_response = client.get("/api/refresh/sources", headers={"Authorization": f"Bearer {operator_token}"})

    assert admin_response.status_code == 200
    assert commander_response.status_code == 403
    assert operator_response.status_code == 403
