# Command Demo Runbook (Concise)

Use this runbook for controlled command demonstrations of the completed system.

## Pre-Demo Checks

Run from repository root:

```bash
./.venv/bin/python services/api/scripts/runtime_preflight.py --ensure-schema
./.venv/bin/python -m pytest -q services/api/tests/test_refresh_admin_workflow.py services/api/tests/test_runtime_preflight_contract.py
cd taaip-dashboard && npm test && npm run build
```

Confirm:
- runtime preflight `status: ok`
- role/admin safety regressions pass
- frontend tests and build pass

## Demo Readiness Stabilization Checks

Run with secure demo posture enabled:

```bash
export TAAIP_DEMO_MODE=1
export LOCAL_DEV_AUTH_BYPASS=0
export TAAIP_MASTER_MODE=0
```

Focused backend regression checks:

```bash
./.venv/bin/python -m pytest -q \
	services/api/tests/test_demo_security_posture.py \
	services/api/tests/test_demo_runtime_stabilization.py \
	services/api/tests/test_powerbi_coverage_safety.py \
	services/api/tests/test_demo_readiness_preflight.py
```

Live readiness check against running API:

```bash
HOST=127.0.0.1 PORT=8000 LOCAL_DEV_AUTH_BYPASS=0 TAAIP_MASTER_MODE=0 \
	./.venv/bin/python services/api/scripts/runtime_preflight.py --demo-readiness
```

Required outcomes:
- unauthenticated `/api/me` returns `401`
- unauthenticated `/api/refresh/sources` returns `401` or `403`
- admin token on `/api/refresh/sources` returns `200`
- commander/operator tokens on `/api/refresh/sources` return `403`
- `/api/command-center/overview` returns `200` in `< 5s`
- `/api/v2/decision-output/mission-decrease-justification` returns `200` in `< 5s`
- `/api/powerbi/coverage/summary` never returns `500` when `coverage_summary` is missing
- demo readiness script returns `status: ready`

## Startup Sequence

## Option A: Local process startup

```bash
zsh scripts/taaip_preflight.sh
./start-taaip-local.sh
```

## Option B: PM2 startup

```bash
./start-taaip.sh
```

Expected endpoints:
- backend docs: `http://127.0.0.1:8000/docs`
- frontend shell: `http://127.0.0.1:5173`

## Demo Sequence

1. Commander perspective (`?role=commander`)
- Command Center -> Mission Adjustment -> Diagnostics -> TWG/Board -> Execution/Processing -> Power BI

2. 420T operator perspective (`?role=operator420t`)
- Command Center -> Diagnostics -> Decision Sync -> Execution/Processing -> Power BI

3. Admin perspective (`?role=admin`)
- Confirm admin console visibility
- Confirm refresh path protection and structured failures

## Known Fallback Paths

- If scope has no active data, continue with no-data explanation points (do not fabricate results).
- If refresh upload fails `invalid_schema`, explain required column contract and retry with corrected source.
- If refresh upload fails `no_data`, explain zero-row source extraction and retry with corrected extract.
- If startup path check fails, run preflight again and fix directory permissions/env values.

## No-Data Explanation Points

- No-data is an intentional, honest operational outcome.
- The system preserves command integrity by returning neutral/no-data shapes rather than synthetic defaults.
- Failed/empty refresh uploads do not replace active authoritative dataset versions.

## Demo Safety Boundaries

- Do not run ad-hoc data mutation scripts during demo.
- Do not introduce synthetic demo records.
- Keep all explanations tied to currently surfaced authoritative outputs.
