from importlib import util
from pathlib import Path
import base64
import json


def _load_runtime_preflight_module():
    root = Path(__file__).resolve().parents[3]
    script_path = root / "services" / "api" / "scripts" / "runtime_preflight.py"
    spec = util.spec_from_file_location("runtime_preflight_script", script_path)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_demo_preflight_reports_not_ready_when_blockers(monkeypatch):
    module = _load_runtime_preflight_module()

    def _fake_request(url, method="GET", headers=None, payload=None, timeout=6.0):
        return {"ok": False, "status_code": 500, "elapsed_seconds": 7.5, "body": {"error": "boom"}}

    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8000")
    monkeypatch.setenv("LOCAL_DEV_AUTH_BYPASS", "1")
    monkeypatch.setenv("TAAIP_MASTER_MODE", "1")
    monkeypatch.setattr(module, "_request_json", _fake_request)

    result = module._demo_readiness({"status": "ok", "checks": []})
    assert result["status"] == "not_ready"
    assert result["blocking_issues"]


def test_demo_preflight_reports_ready_when_checks_pass(monkeypatch):
    module = _load_runtime_preflight_module()

    def _decode_roles(authorization: str):
        token = authorization.split(" ", 1)[1]
        parts = token.split(".")
        if len(parts) < 2:
            return []
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
        roles = payload.get("roles") or []
        if isinstance(roles, str):
            return [roles]
        return roles

    def _fake_request(url, method="GET", headers=None, payload=None, timeout=6.0):
        if "/api/me" in url and method == "GET":
            return {"ok": False, "status_code": 401, "elapsed_seconds": 0.1, "body": {"detail": "Authorization required"}}
        if "/api/refresh/sources" in url and headers and "Authorization" in headers:
            roles = _decode_roles(headers["Authorization"])
            if "system_admin" in roles:
                return {"ok": True, "status_code": 200, "elapsed_seconds": 0.2, "body": {"status": "ok"}}
            if "co_cmd" in roles or "420t_admin" in roles:
                return {"ok": False, "status_code": 403, "elapsed_seconds": 0.2, "body": {"detail": "Forbidden"}}
        if "/api/refresh/sources" in url:
            return {"ok": False, "status_code": 401, "elapsed_seconds": 0.1, "body": {"detail": "Unauthorized"}}
        if "/api/command-center/overview" in url:
            return {"ok": True, "status_code": 200, "elapsed_seconds": 0.8, "body": {"status": "ok"}}
        if "/api/v2/decision-output/mission-decrease-justification" in url:
            return {"ok": True, "status_code": 200, "elapsed_seconds": 1.1, "body": {"status": "ok", "data": {}}}
        if "/api/powerbi/coverage/summary" in url:
            return {"ok": True, "status_code": 200, "elapsed_seconds": 0.3, "body": {"status": "no_data", "rows": []}}
        return {"ok": True, "status_code": 200, "elapsed_seconds": 0.1, "body": {"status": "ok"}}

    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8000")
    monkeypatch.setenv("LOCAL_DEV_AUTH_BYPASS", "0")
    monkeypatch.setenv("TAAIP_MASTER_MODE", "0")
    monkeypatch.setattr(module, "_request_json", _fake_request)

    result = module._demo_readiness({"status": "ok", "checks": []})
    assert result["status"] == "ready"
    assert not result["blocking_issues"]
