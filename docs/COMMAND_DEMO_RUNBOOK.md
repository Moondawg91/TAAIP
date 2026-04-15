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
