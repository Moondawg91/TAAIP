#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / 'services' / 'api'
for candidate in (str(ROOT), str(API_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

try:
    from services.api.app.runtime_env import runtime_preflight
    from services.api.app.db import init_schema
    from services.api.app.database import reload_engine_if_needed
except ModuleNotFoundError:
    from app.runtime_env import runtime_preflight
    from app.db import init_schema
    from app.database import reload_engine_if_needed


def main() -> int:
    ensure_schema = '--ensure-schema' in sys.argv
    status = runtime_preflight()

    if ensure_schema:
        reload_engine_if_needed()
        init_schema()
        status['schema_bootstrap'] = 'completed'

    print(json.dumps(status, indent=2))
    return 0 if status.get('status') == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
