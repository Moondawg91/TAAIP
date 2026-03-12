TAAIP BACKEND PATCH — ROI + DATA HUB INGEST + RBAC AUTH + USAREC ASSETS SEED
DO NOT DELETE EXISTING ENDPOINTS. ADD/EXTEND ONLY.

BACKUPS (MUST DO FIRST):
1) git status
2) git checkout -b feature/backend-roi-ingest-auth
3) git tag taaip_pre_backend_roi_ingest_auth_$(date +%Y%m%d_%H%M%S) || true
4) Create docs/BACKEND_CHANGELOG.md entry describing new tables/endpoints.

ASSUMPTIONS:
- Backend is FastAPI (services/api/app/main.py or services/api/app/app/main.py style).
- There is an existing DB layer. If none, implement SQLModel + SQLAlchemy + Alembic.
- If Alembic already exists, add a new migration. If not, scaffold minimal migrations.
- SQLite for dev is okay; must be Postgres-ready.

PRIMARY GOALS:
A) Implement backend models + endpoints for ROI:
   - /api/v2/roi/overview
   - /api/v2/roi/events
   - /api/v2/roi/events/{event_id}
   - /api/v2/funnel/summary  (supports ROI detail)
   - include summary/breakdown/funnel/event-detail outputs as defined below

B) Implement Data Hub ingestion registry + run tracking + storage:
   - dataset_registry
   - import_run
   - import_run_errors
   - file_object (storage index)
   - endpoints:
     - GET /api/v2/datahub/registry
     - POST /api/v2/datahub/upload
     - GET /api/v2/datahub/runs/{run_id}
     - GET /api/v2/datahub/runs?limit=&offset=&status=
     - GET /api/v2/datahub/storage/coverage?dataset_key=&start=&end=

C) Implement role-based auth (RBAC) + route enforcement:
   - POST /api/auth/login
   - POST /api/auth/logout (optional but stub ok)
   - GET /api/auth/me
   - Roles: ADMIN, TAAIP_420T, COMMAND
   - Enforce on all endpoints above:
     - ADMIN: full access
     - TAAIP_420T: access ROI + planning + datahub (upload allowed)
     - COMMAND: read-only ROI + summary endpoints; no uploads; no admin ops
   - Add dependency guards with clear 401/403 behavior.

D) Add USAREC assets seed list matching USAREC naming buckets:
   - asset_catalog seeded with USAREC categories:
     - Grassroots Expansion/Maintenance
     - Venue/Sports Sponsorship/Partnership
     - COI Event Support
     - Locally Tailored Advertising (LAMP)
     - Station Branding
     - Education (Local Conf/Convention Support)
     - TAIR
     - DARASH
     - Battalion Asset Maintenance
     - National Event Support
   - Include “MAC” as an asset type family and typical subtypes.

----------------------------
1) DB MODELS (SQLModel preferred)
----------------------------
Create/extend module:
- services/api/app/db/models.py (or existing equivalent)

Implement tables (minimum viable):

(org/unit tables assumed existing; do not change)

DATA HUB:
1) dataset_registry
   - dataset_key (PK, str)
   - source_system (str)  # VANTAGE_THOR, EMM, AIE, ALRL, USAREC_G2, OTHER
   - file_types (JSON array)
   - required_columns (JSON array)
   - optional_columns (JSON array)
   - detection_keywords (JSON array)
   - target_tables (JSON array)
   - version (int)
   - enabled (bool)
   - created_at, updated_at

2) file_object (storage index for historical data visibility)
   - object_id (PK, uuid/str)
   - dataset_key (FK dataset_registry.dataset_key)
   - filename
   - content_type
   - byte_size (int)
   - sha256 (str)
   - storage_backend (enum str: "local", "s3", "azure", "gdrive")
   - storage_uri (str)  # path or URL
   - uploaded_by (str)
   - uploaded_at (datetime)
   - data_start (date nullable)
   - data_end (date nullable)

3) import_run
   - run_id (PK, str, e.g. run_YYYYMMDD_HHMMSS_xxxx)
   - dataset_key (FK)
   - object_id (FK file_object)
   - filename (dup ok)
   - uploaded_by
   - status (enum: queued, running, success, failed)
   - detected_confidence (float)
   - rows_in (int)
   - rows_loaded (int)
   - warnings (int)
   - error_summary (str nullable)
   - started_at, ended_at

4) import_run_errors
   - id (PK int)
   - run_id (FK import_run)
   - row_num (int nullable)
   - column (str nullable)
   - error_code (str)
   - message (str)

ANALYTICS FACTS (minimum for ROI):
5) fact_lead_activity
   - lead_id (PK str stable hash)
   - unit_rsid (str)
   - cbsa (str nullable)
   - zip (str nullable)
   - source_channel (str)  # goarmy, event, mac, walk_in, phone, text, email, hs_alrl, ad, other
   - created_dt (datetime)
   - first_contact_dt (datetime nullable)
   - last_activity_dt (datetime nullable)
   - stage (str)  # lead/contact/appt/processing/contract
   - contract_dt (datetime nullable)
   - contract_flag (bool)
   - hq_flag (bool)
   - event_id (str nullable)  # if directly tied from import/source
   - mac_id (str nullable)    # if provided by EMM

6) fact_event  (EMM)
   - event_id (PK str)
   - unit_rsid (str)
   - cbsa (str nullable)
   - zip (str nullable)
   - event_dt (date/datetime)
   - event_type (str)
   - macs_requested (int default 0)
   - macs_assigned (int default 0)
   - macs_used (int default 0)
   - cost_event (float default 0)
   - cost_marketing (float default 0)
   - cost_travel (float default 0)
   - cost_total (computed or stored)
   - notes (str nullable)

7) bridge_event_attribution
   - id (PK int)
   - event_id (FK fact_event)
   - lead_id (FK fact_lead_activity)
   - attribution_rule (str)  # hybrid_last_touch_30d, etc.
   - attributed_flag (bool)
   - attributed_dt (datetime)

DERIVED/MATERIALIZED:
8) roi_event_summary
   - event_id (PK str)
   - unit_rsid (str)
   - spend_total (float)
   - leads_attributed (int)
   - contacts_attributed (int)
   - appts_attributed (int)
   - processing_attributed (int)
   - contracts_attributed (int)
   - hq_contracts_attributed (int)
   - cpl (float nullable)
   - cpc (float nullable)
   - roi_score_A (float nullable)
   - roi_score_B (float nullable)
   - roi_score_C (float nullable)
   - status_color (str)  # GREEN/AMBER/RED
   - computed_at (datetime)

ASSETS:
9) asset_catalog
   - asset_id (PK str/uuid)
   - asset_name (str)
   - asset_family (str)  # MAC, MEB, ASB, TAIR, DARASH, LAMP, COI_EVENT_SUPPORT, STATION_BRANDING, EDU_SUPPORT, NATIONAL_EVENT_SUPPORT, BATTALION_ASSET_MAINT
   - asset_type (str)    # e.g. DIGITAL, OOH, RADIO, PRINT, CINEMA, EVENT_KIT, SIGNAGE, LEAD_CAPTURE, STAFF_SUPPORT, OTHER
   - category (str)      # USAREC spend plan bucket (Grassroots, Sponsorship, etc.)
   - supported_objectives (JSON array) # awareness/engagement/activation
   - supported_tactics (JSON array)    # exhibit/web/ooh/radio/tv/digital/direct_funded/etc
   - approval_level (str) # STN/CO/BN/BDE/AEMO/G7_9
   - enabled (bool)
   - description (str nullable)
   - constraints (JSON obj nullable)
   - created_at, updated_at

MIGRATIONS:
- If alembic exists: add new revision for these tables.
- If not: implement minimal create_all in startup for dev ONLY, but provide alembic scaffold notes in docs.

----------------------------
2) AUTH + RBAC
----------------------------
Create:
- services/api/app/auth/security.py
- services/api/app/auth/router.py

Implement:
- POST /api/auth/login
  - Accept JSON: {"username": "...", "password":"..."}
  - For now: allow env-based dev login OR existing user DB if present.
  - Return: {"access_token":"...","token_type":"bearer"}
  - Use JWT (HS256) with secret from env JWT_SECRET.
  - Include claims: sub, roles[], exp.

- GET /api/auth/me
  - Requires bearer token
  - Return:
    {
      "user_id":"...",
      "username":"...",
      "roles":["ADMIN"],
      "permissions":["...optional..."]
    }

- Add dependency:
  - require_auth()
  - require_roles(*roles)
  - require_any_role()

RBAC rules to enforce:
- ROI endpoints: ADMIN, TAAIP_420T, COMMAND (read)
- DataHub upload: ADMIN, TAAIP_420T only
- DataHub registry/runs: ADMIN, TAAIP_420T read; COMMAND read-only registry & run status ok (NO upload)
- Any admin-only ops (if present): ADMIN only

----------------------------
3) ROI ENDPOINTS (HYBRID ATTRIBUTION)
----------------------------
Create:
- services/api/app/roi/router.py
- services/api/app/roi/service.py
- services/api/app/funnel/router.py

HYBRID ATTRIBUTION:
- query param: attribution_mode=hybrid (required default)
- ruleset: hybrid_last_touch_within_days (default 30)
- attribution mechanics (minimum viable):
  - If lead has event_id directly matching the event: attribute
  - Else if lead.source_channel in ("event","mac","ad","goarmy","walk_in","phone","text","email","hs_alrl") and lead.created_dt within window of event_dt AND same zip/cbsa OR same unit_rsid: attribute with lower confidence
  - Record bridge_event_attribution rows for attributed leads
  - compute outputs counts by stage:
    - leads = count distinct lead_id
    - contacts = stage>=contact (or first_contact_dt not null)
    - appts = stage==appt
    - processing = stage==processing
    - contracts = contract_flag true and contract_dt within window
    - hq_contracts = contract_flag and hq_flag

USAREC THRESHOLDS:
- implement constants:
  - CPL_THRESHOLD = 100.0
  - CPC_THRESHOLD = 2500.0
(Keep configurable later; do not overcomplicate now.)

COMPARE MODES:
- compare=A|B|C
A: thresholds only
B: thresholds + unit historical average
C: thresholds + unit + brigade average
Implement by computing historical averages from roi_event_summary (or facts) for the requested unit, and brigade as parent echelon if org table exists; if not available, return nulls but keep schema.

ENDPOINTS:

1) GET /api/v2/roi/overview?unit_rsid=&start=&end=&compare=A|B|C&attribution_mode=hybrid
Return:
{
 "unit_rsid": "...",
 "date_range": {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"},
 "totals": {
   "spend_total": 0,
   "leads": 0,
   "contacts": 0,
   "appointments": 0,
   "processing": 0,
   "contracts": 0,
   "hq_contracts": 0
 },
 "kpis": { "cpl": 0, "cpc": 0, "flash_to_bang_days_median": 0 },
 "status": { "overall":"GREEN|AMBER|RED", "reasons":[...] },
 "benchmarks": {
   "usarec_thresholds": {"cpl":100,"cpc":2500},
   "unit_avg": {"roi_score": null, "cpl": null, "cpc": null},
   "bde_avg": {"roi_score": null, "cpl": null, "cpc": null}
 }
}

2) GET /api/v2/roi/events?unit_rsid=&start=&end=&compare=&attribution_mode=hybrid
Return list of event rollups:
{
 "events":[
   {
     "event_id":"...",
     "name":"...",
     "event_dt":"YYYY-MM-DD",
     "unit_rsid":"...",
     "spend_total":0,
     "leads":0,
     "contracts":0,
     "cpl":0,
     "cpc":0,
     "roi_score_A":0,
     "roi_score_B":null,
     "roi_score_C":null,
     "status_color":"GREEN|AMBER|RED"
   }
 ]
}

3) GET /api/v2/roi/events/{event_id}?unit_rsid=&compare=&attribution_mode=hybrid
Return DETAIL schema exactly:
{
 "event": {"event_id":"...","name":"...","date":"YYYY-MM-DD","location":{"cbsa":"...","zip":"..."},"owning_unit_rsid":"..."},
 "inputs": {
   "spend_total":0,
   "spend_breakdown":{"marketing_ads":0,"event_costs":0,"travel_misc":0},
   "macs_used":0,
   "hours_spent_total":0
 },
 "outputs": {"leads":0,"contacts":0,"appointments":0,"processing":0,"contracts":0,"hq_contracts":0},
 "attribution": {"ruleset":"hybrid_last_touch_within_days","window_days":30,"contracts_attributed":0,"leads_attributed":0},
 "kpis": {"cpl":0,"cpc":0,"roi_score_threshold":0,"roi_score_unit_avg":null,"roi_score_bde_avg":null},
 "status": {"overall":"GREEN|AMBER|RED","reasons":[{"metric":"CPC","comparison":"USAREC_THRESHOLD","result":"PASS|FAIL"}]},
 "recommendations": [{"type":"REPEAT_EVENT|DO_NOT_REPEAT|SCALE_MARKETING|REALLOCATE_MAC","text":"..."}]
}

ROI SCORE IMPLEMENTATION (minimal, can refine later):
- roi_score_threshold = BenchmarkIndexOptionA
  - Compute normalized score from CPL and CPC vs thresholds:
    - cpl_score = clamp(0..100, 100 * (CPL_THRESHOLD / max(cpl, small)))
    - cpc_score = clamp(0..100, 100 * (CPC_THRESHOLD / max(cpc, small)))
    - roi_score_A = round( (0.5*cpl_score + 0.5*cpc_score), 1 )
- For compare B and C:
  - roi_score_B = combine vs thresholds + unit average (if available)
  - roi_score_C = combine vs thresholds + unit avg + bde avg (if available)
If averages unavailable, return nulls but keep fields.

STATUS COLOR RULES:
- GREEN if cpl<=threshold AND cpc<=threshold
- AMBER if only one passes
- RED if both fail OR contracts==0 with spend>0

Also implement:
- GET /api/v2/funnel/summary?unit_rsid=&start=&end=
Using fact_lead_activity stage counts and conversion rates + flash-to-bang (median days from created_dt to contract_dt for contract_flag true)

----------------------------
4) DATA HUB ENDPOINTS (registry/upload/runs/storage)
----------------------------
Create:
- services/api/app/datahub/router.py
- services/api/app/datahub/service.py
- services/api/app/datahub/detect.py
- services/api/app/datahub/storage.py

KEY RULE:
- Data Hub is the ONLY place that supports uploads.
- Upload stores file to local ./data/uploads (dev) and writes file_object row.
- Detection:
  - Match dataset_registry.detection_keywords against filename + first row headers (csv/xlsx) if possible.
  - Return detected_confidence 0..1
- Validation:
  - Ensure required_columns exist in file headers
- Normalization/load:
  - For this patch: implement pipeline skeleton:
    - create import_run status queued -> running -> success/failed
    - store row counts, errors
  - Implement at least one "no-op loader" that just records rows_in and marks success, so UI can integrate.
  - Do NOT block future real loaders.

ENDPOINTS:
- GET /api/v2/datahub/registry
Return:
{ "datasets":[ {dataset_key, source_system, file_types, required_columns, optional_columns, detection_keywords, target_tables, enabled, version} ] }

- POST /api/v2/datahub/upload
multipart form:
  - file: UploadFile
  - optional dataset_hint: str
Return:
{ "run_id":"...", "status":"queued", "dataset_key":"...", "detected_confidence":0.0 }

- GET /api/v2/datahub/runs/{run_id}
Return:
{ "run_id":"...", "status":"success|failed|running|queued", "dataset_key":"...", "rows_in":0,"rows_loaded":0,"warnings":0,"errors":[...] }

- GET /api/v2/datahub/storage/coverage?dataset_key=&start=&end=
Return:
{ "dataset_key":"...", "objects":[ {"object_id":"...","filename":"...","data_start":"...","data_end":"...","uploaded_at":"...","byte_size":123} ] }

SEED DATASETS (dataset_registry seed):
Add seed registry entries for:
- VANTAGE_THOR_LEADS (lead funnel feed)
- AIE_LEADS (AIE exported leads/processing)
- EMM_EVENTS_MAC (events + MAC assignments/cost)
- ALRL_SCHOOLS (school contacts/outcomes)
Include required columns list placeholders; keep editable.

----------------------------
5) USAREC ASSETS SEED LIST (TAILORED)
----------------------------
Create file:
- services/api/app/seed/assets_usarec_master_v1.json
Seed asset_catalog with these naming conventions (use these strings exactly so frontend can map):

ASSET FAMILIES + EXAMPLES:
1) MAC (Mobile Asset Capability)
   - "MAC - Lead Capture Team"
   - "MAC - Event Engagement Team"
   - "MAC - Digital Engagement Support"
   - "MAC - Community Outreach Support"
   Supported objectives: awareness, engagement, activation
   Tactics: exhibit, web, digital, direct_funded, community_event

2) TAIR (Targeted Advertising / Investment Request)
   - "TAIR - Digital Paid Media Buy"
   - "TAIR - Programmatic Display"
   - "TAIR - Social Paid Campaign"
   - "TAIR - Search (SEM) Campaign"
   Category: Locally Tailored Advertising (LAMP)
   Approval: AEMO/G7_9 (config via constraints)

3) DARASH (Digital/Advertising Related Support)
   - "DARASH - Creative Production"
   - "DARASH - Landing Page / Web Support"
   - "DARASH - Tracking/Pixel Setup"
   Category: Locally Tailored Advertising (LAMP)

4) MEB / ASB / Branding
   - "MEB - Recruiter Booth Kit (Table/Backdrop)"
   - "MEB - Signage Kit (Banners/QR)"
   - "ASB - Station Branding Package"
   - "ASB - Vehicle Wrap / Branded Display"
   Category: Station Branding / Battalion Asset Maintenance

5) COI Event Support
   - "COI - Career Fair Support Package"
   - "COI - High School Event Support Package"
   - "COI - Community Festival Support Package"

6) Venue/Sports Sponsorship/Partnership
   - "Sponsorship - Venue Partnership Package"
   - "Sponsorship - Sports Activation Package"

7) Education (Local Conf/Convention Support)
   - "Education - School Access Support (ESS)"
   - "Education - Postsecondary Outreach Support"
   - "Education - Convention/Conference Support"

8) National Event Support
   - "National - National Event Support Package"
   - "National - National Asset Deployment"

Each asset record must include:
- asset_name
- asset_family
- asset_type
- category (use one of the USAREC spend plan buckets)
- supported_objectives
- supported_tactics
- approval_level
- constraints with example lead times + spend bands where relevant.

Add a seed loader:
- services/api/app/seed/load_seeds.py
- called on startup only in DEV if env SEED_ON_STARTUP=true
- idempotent upsert by asset_name + version.

----------------------------
6) WIRING INTO MAIN APP
----------------------------
- Mount routers:
  - /api/auth (auth router)
  - /api/v2/roi (roi router)
  - /api/v2/funnel (funnel router)
  - /api/v2/datahub (datahub router)
- Add CORS if needed.
- Ensure all endpoints return stable JSON schemas even if DB empty (zeros/empty arrays).

TESTS (MINIMUM):
Add pytest tests:
- test_auth_me_requires_token
- test_command_role_cannot_upload
- test_roi_endpoints_return_schema_when_empty
- test_datahub_registry_returns_seed

DOCUMENTATION:
Create docs/API_CONTRACTS.after.md with examples for:
- /api/auth/login, /api/auth/me
- /api/v2/roi/overview, /api/v2/roi/events, /api/v2/roi/events/{id}
- /api/v2/datahub/registry, /api/v2/datahub/upload, /api/v2/datahub/runs/{id}

DO NOT CHANGE FRONTEND IN THIS PATCH.
DO NOT REMOVE ANY EXISTING BACKEND ROUTES; ONLY ADD/EXTEND.


⸻

✅ What you’ll get after this patch (so you can sanity-check quickly)

Auth verification (fast)
	•	Login → get token
	•	Me → confirm roles
	•	Hit upload endpoint as COMMAND → should return 403 ✅

ROI detail will include real detail, not colors
	•	leads / contacts / appts / processing / contracts / HQ
	•	CPL / CPC
	•	flash-to-bang (lead→contract time) (median)
	•	recommendations array (first-pass rules)

Data Hub will show where historical data is stored
	•	file_object + /storage/coverage makes historical visibility explicit ✅

⸻

Assets seed list note (honest + practical)

USAREC naming conventions vary by brigade/battalion, but the seed I specified uses the language you already referenced (TAIR/DARASH, Station Branding, Local Conf support, COI Event Support, etc.). This gives you a clean master list you can refine without changing schema.
