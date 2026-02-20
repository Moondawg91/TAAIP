# USAREC Completion Gate

This document describes the `/api/system/usarec-gate` endpoint and the completion workflow used to mark USAREC scope readiness.

Endpoints

- `GET /api/system/usarec-gate`
  - Returns a readiness summary indicating whether core tables and minimal row counts exist.
  - Response shape: `{ status: 'ok', ready: bool, checks: { <table>: { exists: bool, rows?: number } }, last_completion: {...} }`.

- `POST /api/system/usarec-gate/complete`
  - Marks a USAREC completion record and stores a provenance entry in `usarec_completion`.
  - Protected by RBAC: requires `USAREC_ADMIN` role or `LOCAL_DEV_AUTH_BYPASS`.
  - Payload: `{ scope_type?: string, scope_value?: string, details?: object }`.
  - Response: `{ status: 'ok', id: '<record id>', completed_at: '<ISO timestamp>' }`.

Notes

- The endpoints are intentionally defensive and perform best-effort checks.
- The `usarec_completion` table is created idempotently when the POST is invoked if it does not already exist.
- Recommended next steps: wire a simple admin UI page at `/system/usarec-gate` to view readiness and trigger completion when appropriate.
