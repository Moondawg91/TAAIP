Data Hub: Supported Imports & Contracts
=====================================

This document describes the v1 Data Hub import capabilities added to the API.

APIs
- POST /api/v2/datahub/uploads?dry_run=0|1
  - multipart file upload (xlsx or csv)
  - response contains `import_run_id`, `detection`, `result` and `preview` for dry-run

- GET /api/v2/datahub/supported
  - returns importer registry specs (friendly name, dataset_key)

- GET /api/v2/datahub/imports
  - list recent import runs

- GET /api/v2/datahub/imports/{id}
  - import run detail including row errors

- GET /api/v2/datahub/imports/{id}/preview
  - preview normalized rows (first 50)

Design notes
- Raw uploads are deduped by SHA256 and stored under `TAAIP_DOCUMENTS_PATH` (default `./data/documents/datahub_uploads`).
- Each upload creates an `import_run` record. Dry-runs validate and return previews without committing normalized rows.
- The importer registry detects source/dataset via filename patterns and header signatures. It supports multiple shapes per dataset.
- Unit RSID mapping attempts direct `rsid` fields then name-based lookup in the `org_unit` table.

Tables added
- `import_file`, `import_run`, `import_row_error`
- Normalized tables: `emm_event`, `emm_mac`, `g2_market_metric`, `alrl_school`, `fstsm_metric`, `aie_lead_stub`

Notes
- This initial implementation provides robust detection, dry-run validation and simple normalized ingestion.
- It is idempotent: the same file uploaded again will create a new `import_run` but will reuse stored file bytes by SHA256.
- Size limits, additional importer specs, and more advanced unit mapping (ZIP/CBSA) can be added later.
