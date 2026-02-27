TAAIP — USAREC ASSETS MASTER LIST (BACKUPS FIRST) — DO NOT REMOVE ANY PAGES

BACKUPS FIRST (MUST):
1) git status
2) git checkout -b feature/taaip-usarec-assets-master
3) git tag taaip_pre_assets_master_$(date +%Y%m%d_%H%M%S) || true
4) Save current DB schema snapshot if available:
   - add docs/SCHEMA_SNAPSHOT.before.md with existing relevant tables.

OBJECTIVE:
Implement a canonical USAREC assets master list used for:
- Planning (TWG/Fusion/QTR)
- Event/MAC recommendations
- Asset schedule visibility
- Capability coverage by unit and time

SCOPE:
Backend:
- Create tables: asset_catalog, asset_inventory, asset_requests, asset_assignments, asset_capabilities
- Create API endpoints to query assets and generate recommendations
Frontend:
- Show USAREC assets within Planning (TWG + QTR calendar)
- Provide asset recommendation panel for events based on objective + tactic + unit history

DATA MODEL (Postgres/SQLite depending on current backend):
1) asset_catalog (master list)
   - asset_id (PK, string/uuid)
   - asset_name (string)
   - asset_type (enum: "MAC", "MEB", "ASB", "TAIR", "DASH", "DIR", "EQUIPMENT", "VENUE_SUPPORT", "DIGITAL", "OOH", "RADIO", "PRINT", "SPONSORSHIP", "EDU_SUPPORT", "OTHER")
   - category (string)  # e.g. "Lead Gen", "Awareness", "Engagement", "Activation", "Processing Support"
   - supported_objectives (json array) # Awareness/Engagement/Activation etc
   - supported_tactics (json array) # exhibit, web, ooh, radio, tv, digital, direct funded, etc
   - description (text)
   - constraints (json) # lead time, approvals, min/max spend, capacity notes
   - requires_approval_level (enum: "STN", "CO", "BN", "BDE", "AEMO", "G7_9")
   - enabled (bool)
   - version (int)
   - created_at, updated_at

2) asset_inventory (where assets “live” / availability)
   - inventory_id (PK)
   - asset_id (FK asset_catalog)
   - owning_unit_rsid (string)
   - holding_unit_rsid (string nullable)
   - status (enum: available, reserved, assigned, maintenance, retired)
   - available_from_dt, available_to_dt
   - notes

3) asset_requests (what units request for QTR events)
   - request_id (PK)
   - unit_rsid
   - event_id (nullable if planning stage)
   - requested_asset_type (string)
   - requested_asset_ids (json array nullable)
   - priority (enum: low/med/high)
   - needed_start_dt, needed_end_dt
   - justification (text)
   - approval_status (enum: draft, submitted, approved, denied)
   - approval_chain (json array of roles/units)
   - created_by, created_at, updated_at

4) asset_assignments (what gets approved + scheduled)
   - assignment_id (PK)
   - request_id (FK)
   - asset_id (FK)
   - assigned_unit_rsid
   - assigned_start_dt, assigned_end_dt
   - assignment_status (enum: scheduled, active, complete, canceled)
   - notes

5) asset_capabilities (optional mapping)
   - asset_id (FK)
   - capability_key (string) # e.g. "lead_capture", "digital_boost", "school_access", "processing_support"
   - weight (float)

SEED DATA:
- Add a seed file in backend (json/yaml) with a broad “USAREC assets” list, even if not perfect:
  include at minimum these families:
  - MAC (mobile asset capability)
  - MEB assets (marketing engagement/branding)
  - TAIR assets
  - ASB/brand assets
  - Station branding/locally tailored advertising
  - Education support / school access support (ESS-aligned)
  - Digital ad support, OOH, Print, Radio, Cinema, Direct funded
  - Event support: exhibit kits, table/booth kits, signage, lead capture tools
- Ensure the seed is idempotent and does not overwrite local edits unless version changes.

RECOMMENDATION ENGINE (backend):
Create endpoint that returns recommended assets based on:
- desired_effect (awareness|engagement|activation)
- tactic (exhibit/web/ooh/radio/tv/digital/direct funded/etc)
- unit_rsid
- optional: historical performance (if present) from ROI tables (CPL/CPC, conversions)
Algorithm:
- filter enabled assets that support desired_effect and tactic
- score = capability weights + match strength + (optional) boost if historically successful for unit or brigade
- return top N with reasons (plain language)

API ENDPOINTS (v2):
- GET  /api/v2/assets/catalog
- GET  /api/v2/assets/catalog/{asset_id}
- GET  /api/v2/assets/inventory?unit_rsid=&status=
- POST /api/v2/assets/requests
- GET  /api/v2/assets/requests?unit_rsid=&fy=&qtr=
- PATCH /api/v2/assets/requests/{request_id}
- POST /api/v2/assets/assignments
- GET  /api/v2/assets/assignments?unit_rsid=&start=&end=
- GET  /api/v2/assets/recommendations?unit_rsid=&desired_effect=&tactic=&start=&end=&event_type=

FRONTEND INTEGRATION:
- On Planning → TWG page:
  add “USAREC Assets” panel:
  - search/filter assets by desired effect + tactic
  - show recommended assets list with reasons
- On Planning → QTR Calendar:
  when creating/editing an event placeholder:
  - show recommended assets
  - allow creating asset_requests
  - show assigned assets as calendar badges

RBAC:
- Admin: full CRUD
- 420T: create requests, view catalog and assignments
- Command: view only (no create unless granted)

DELIVERABLES:
- docs/ASSETS_MASTERLIST.after.md includes:
  - all endpoint contracts
  - example seed records
  - recommendation scoring explanation

DO NOT CHANGE any existing ROI or Data Hub logic in this patch.
Implement assets master list cleanly and self-contained.
