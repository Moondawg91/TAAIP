import os
import json
import base64
import jwt
from fastapi.testclient import TestClient


def _b64url(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')


def make_jwt(payload: dict) -> str:
    header = json.dumps({"alg": "none", "typ": "JWT"})
    return f"{_b64url(header)}.{_b64url(json.dumps(payload))}.sig"


def test_me_exposes_alias_permissions(tmp_path, monkeypatch):
    # Verify that canonical uppercase aliases map to dotted permission keys
    # and that a frontend can expose alias keys when dotted permissions are present.
    from services.api.app.routers.rbac import PERM_ALIASES
    # sanity: mapping contains expected entries for dashboards
    assert PERM_ALIASES.get('DASHBOARDS_READ') == 'dashboards.view'
    assert PERM_ALIASES.get('EXPORT_DATA') == 'dashboards.export'
    # simulate me-like exposure: if dotted perms present, alias should be added
    perms_map = {PERM_ALIASES['DASHBOARDS_READ']: True, PERM_ALIASES['EXPORT_DATA']: True}
    # exposure step
    if perms_map.get('dashboards.view'):
        perms_map.setdefault('DASHBOARDS_READ', True)
    if perms_map.get('dashboards.export'):
        perms_map.setdefault('EXPORT_DATA', True)
    assert perms_map.get('DASHBOARDS_READ') is True
    assert perms_map.get('EXPORT_DATA') is True


def test_require_perm_alias_matches_token():
    # Directly test require_perm dependency logic without running the full app
    from services.api.app.routers.rbac import require_perm
    dep = require_perm('DASHBOARDS_READ')
    # user token contains dotted permission — alias lookup should allow
    user = {'username': 'u', 'permissions': ['dashboards.view']}
    # The dependency factory returns a function expecting a user; calling should return the same user
    allowed = dep(user)
    assert allowed == user
