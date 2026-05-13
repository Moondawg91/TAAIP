#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import os
import time
import base64
from datetime import datetime, timedelta
from urllib import request as urllib_request
from urllib import error as urllib_error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / 'services' / 'api'
for candidate in (str(ROOT), str(API_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

try:
    from services.api.app.runtime_env import runtime_preflight
    try:
        from services.api.app.db import init_schema
    except ImportError:
        # Backward compatibility: db module now exposes init_db.
        from services.api.app.db import init_db as init_schema
    from services.api.app.database import reload_engine_if_needed
except ModuleNotFoundError:
    from app.runtime_env import runtime_preflight
    try:
        from app.db import init_schema
    except ImportError:
        # Backward compatibility: db module now exposes init_db.
        from app.db import init_db as init_schema
    from app.database import reload_engine_if_needed


def main() -> int:
    ensure_schema = '--ensure-schema' in sys.argv
    demo_readiness = '--demo-readiness' in sys.argv
    status = runtime_preflight()

    if ensure_schema:
        reload_engine_if_needed()
        init_schema()
        status['schema_bootstrap'] = 'completed'

    if demo_readiness:
        result = _demo_readiness(status)
        print(json.dumps(result, indent=2))
        return 0 if result.get('status') == 'ready' else 1

    print(json.dumps(status, indent=2))
    return 0 if status.get('status') == 'ok' else 1


def _jwt_like(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}.signature"


def _jwt_hs256(payload: dict) -> str:
    import jwt  # lazy import to keep script lightweight for non-demo mode

    secret = os.getenv('JWT_SECRET', 'devsecret')
    claims = dict(payload)
    claims.setdefault('exp', datetime.utcnow() + timedelta(minutes=30))
    return jwt.encode(claims, secret, algorithm='HS256')


def _request_json(url: str, method: str = 'GET', headers: dict | None = None, payload: dict | None = None, timeout: float = 6.0):
    data = None
    req_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        req_headers.setdefault('Content-Type', 'application/json')

    req = urllib_request.Request(url, method=method, headers=req_headers, data=data)
    started = time.perf_counter()
    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.perf_counter() - started
            raw = resp.read().decode('utf-8', errors='replace')
            body = None
            if raw:
                try:
                    body = json.loads(raw)
                except Exception:
                    body = raw
            return {'ok': True, 'status_code': resp.getcode(), 'elapsed_seconds': round(elapsed, 3), 'body': body}
    except urllib_error.HTTPError as e:
        elapsed = time.perf_counter() - started
        raw = e.read().decode('utf-8', errors='replace') if getattr(e, 'fp', None) else ''
        body = None
        if raw:
            try:
                body = json.loads(raw)
            except Exception:
                body = raw
        return {'ok': False, 'status_code': e.code, 'elapsed_seconds': round(elapsed, 3), 'body': body}
    except Exception as e:
        elapsed = time.perf_counter() - started
        return {'ok': False, 'status_code': 0, 'elapsed_seconds': round(elapsed, 3), 'error': str(e), 'body': None}


def _demo_readiness(runtime_status: dict) -> dict:
    host = os.getenv('HOST', '127.0.0.1')
    port = os.getenv('PORT', '8000')
    base = f"http://{host}:{port}"
    checks = []
    blockers = []

    def add_check(name: str, ok: bool, detail: str, data: dict | None = None):
        item = {'name': name, 'status': 'ok' if ok else 'error', 'detail': detail}
        if data is not None:
            item['data'] = data
        checks.append(item)
        if not ok:
            blockers.append(f"{name}: {detail}")

    bypass_on = os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true')
    master_on = os.getenv('TAAIP_MASTER_MODE', '0').lower() in ('1', 'true')
    add_check('auth_posture_flags', not (bypass_on or master_on), 'LOCAL_DEV_AUTH_BYPASS and TAAIP_MASTER_MODE must be disabled', {
        'LOCAL_DEV_AUTH_BYPASS': os.getenv('LOCAL_DEV_AUTH_BYPASS', 'unset'),
        'TAAIP_MASTER_MODE': os.getenv('TAAIP_MASTER_MODE', 'unset'),
    })

    no_token_me = _request_json(f"{base}/api/me", timeout=4.0)
    add_check('auth_no_token_me', no_token_me.get('status_code') == 401, f"expected 401, got {no_token_me.get('status_code')}", no_token_me)

    no_token_refresh = _request_json(f"{base}/api/refresh/sources", timeout=4.0)
    add_check('auth_no_token_refresh', no_token_refresh.get('status_code') in {401, 403}, f"expected 401/403, got {no_token_refresh.get('status_code')}", no_token_refresh)

    admin_token = _jwt_like({'sub': 'admin', 'roles': ['system_admin'], 'permissions': ['admin.permissions.manage'], 'scopes': []})
    commander_token = _jwt_like({'sub': 'commander', 'roles': ['co_cmd'], 'permissions': [], 'scopes': []})
    operator_token = _jwt_like({'sub': 'operator420t', 'roles': ['420t_admin'], 'permissions': [], 'scopes': []})

    admin_refresh = _request_json(f"{base}/api/refresh/sources", headers={'Authorization': f'Bearer {admin_token}'}, timeout=4.0)
    commander_refresh = _request_json(f"{base}/api/refresh/sources", headers={'Authorization': f'Bearer {commander_token}'}, timeout=4.0)
    operator_refresh = _request_json(f"{base}/api/refresh/sources", headers={'Authorization': f'Bearer {operator_token}'}, timeout=4.0)
    add_check('auth_role_admin_refresh', admin_refresh.get('status_code') == 200, f"expected 200, got {admin_refresh.get('status_code')}", admin_refresh)
    add_check('auth_role_commander_refresh', commander_refresh.get('status_code') == 403, f"expected 403, got {commander_refresh.get('status_code')}", commander_refresh)
    add_check('auth_role_operator_refresh', operator_refresh.get('status_code') == 403, f"expected 403, got {operator_refresh.get('status_code')}", operator_refresh)

    cc = _request_json(f"{base}/api/command-center/overview?scope_type=USAREC&scope_value=USAREC", timeout=6.0)
    add_check('command_center_latency', cc.get('status_code') == 200 and float(cc.get('elapsed_seconds') or 999) < 5.0, f"status={cc.get('status_code')} elapsed={cc.get('elapsed_seconds')}s", cc)

    mission_token = _jwt_hs256({'sub': 'usarec_admin', 'role': 'USAREC_ADMIN', 'scope': 'USAREC'})
    mission = _request_json(
        f"{base}/api/v2/decision-output/mission-decrease-justification",
        method='POST',
        headers={'Authorization': f'Bearer {mission_token}'},
        payload={
            'org_id': '1A1',
            'period_start': '2026-01-01',
            'period_end': '2026-01-31',
            'baseline_start': '2025-12-01',
            'baseline_end': '2025-12-31',
            'include_evidence': False,
            'force_refresh': False,
        },
        timeout=6.0,
    )
    add_check('mission_adjustment_latency', mission.get('status_code') == 200 and float(mission.get('elapsed_seconds') or 999) < 5.0, f"status={mission.get('status_code')} elapsed={mission.get('elapsed_seconds')}s", mission)

    coverage = _request_json(f"{base}/api/powerbi/coverage/summary", headers={'Authorization': f'Bearer {admin_token}'}, timeout=4.0)
    coverage_ok = coverage.get('status_code') != 500
    mode = 'unknown'
    body = coverage.get('body')
    if isinstance(body, dict):
        mode = body.get('status') or body.get('reason') or 'dict'
    elif isinstance(body, list):
        mode = 'rows'
    add_check('powerbi_coverage_safety', coverage_ok, f"status={coverage.get('status_code')} mode={mode}", coverage)

    status = 'ready' if not blockers and runtime_status.get('status') == 'ok' else 'not_ready'
    return {
        'status': status,
        'runtime_preflight': runtime_status,
        'checks': checks,
        'blocking_issues': blockers,
    }


if __name__ == '__main__':
    raise SystemExit(main())
