# Admin Refresh and Troubleshooting Guide

Purpose:
- Run controlled refresh and maintenance without leaking controls into command/operator workflows.

## Access Requirement

Refresh endpoints require admin manage privilege:
- permission: `admin.permissions.manage`
- non-admin access returns `403`

## Admin Refresh Workflow

## 1) Create or Update Refresh Source

- `POST /api/refresh/sources`
- include canonical target and merge keys as needed

## 2) Upload Authoritative File

- `POST /api/refresh/sources/{source_id}/upload`

Expected behavior:
- file profile + validation produced
- valid uploads are staged
- invalid uploads fail with structured error

## 3) Commit Validated Job

- `POST /api/refresh/jobs/{job_id}/commit`

Expected behavior:
- dataset version created
- active dataset pointer updated only on valid commit

## Structured Failure Modes

## `invalid_schema`

Meaning:
- required authoritative columns are missing.

Response details include:
- error code
- message
- missing columns
- lineage metadata

Action:
- correct source schema and re-upload.

## `no_data`

Meaning:
- uploaded dataset has zero usable rows.

Response details include:
- error code
- message
- lineage metadata

Action:
- verify extract criteria and regenerate source file.

Safety:
- `dataset_active` remains unchanged.

## Runtime and Startup Troubleshooting

## Preflight Check

```bash
./.venv/bin/python services/api/scripts/runtime_preflight.py --ensure-schema
```

Expected:
- `status: ok`
- writable path checks are `ok`

## Script Syntax Check

```bash
zsh -n start-taaip.sh start-taaip-local.sh run-dev.sh scripts/taaip_preflight.sh
```

## Common Issues

1. Permission denied on data paths
- Fix ownership/permissions for DB, uploads, refresh uploads, exports, documents.

2. Migration mismatch
- Run Alembic upgrade using `services/api/alembic.ini`.

3. Refresh rejected for non-admin user
- Confirm token has `admin.permissions.manage`.

4. Command view changed after refresh attempt
- Check if commit actually succeeded; failed validation should not rebind active dataset.

## Safety Rules

- Do not bypass validation for production refresh.
- Do not stage synthetic/demo-marked data.
- Keep refresh operations scoped to authoritative sources only.
