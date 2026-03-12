TAAIP MASTER SPEC PATCH — TOR-ALIGNED ROUTES + API CONTRACTS + DATA MODEL — DO NOT DELETE PAGES

BACKUPS FIRST (MUST):
1) git status
2) git checkout -b feature/taaip-master-spec-tor
3) git tag taaip_pre_master_spec_$(date +%Y%m%d_%H%M%S) || true
4) Add docs/ROUTES_SNAPSHOT.before.json listing current routes + nav
5) Add docs/API_CONTRACTS.before.md listing current backend endpoints

NON-NEGOTIABLE RULES:
- DO NOT remove any important pages (Planning, TWG, Fusion Cell, QTR calendar, Command Center, Schools, Help Desk, Resources/Training, Budget, ROI, Data Hub).
- Uploads/import buttons must exist ONLY in Data Hub.
- Unit cascade picker must appear ONLY on dashboard pages that filter/visualize analytics (Command Center, Market Intel, Operations dashboards, ROI dashboards).
- Home/Command Center must not have “Post Item” buttons. Posting belongs ONLY in Admin (ADMIN-only) and should be subtle.
- Fix UnitCascadePicker dropdowns so BDE/BN/CO/STN actually populate; shrink control sizing.

FRONTEND ROUTES — IMPLEMENT EXACTLY:
App Shell:
- Top header appears only on dashboard pages (where unit cascade is needed)
- Left nav is role-based
- Main canvas full height
- Bottom drilldown panel opens on click from charts/cards

Routes:

Core
- /  → Command Center (default landing)
- /command-center → Command Center (same as /)

Intelligence & Operations
- /market-intel → Market Intelligence
- /operations/funnel → Recruiting Funnel
- /operations/productivity → Productivity / Contact Activity
- /operations/processing → Processing / Conversion / Attrition

Events, Marketing, ROI (Planning + Execution)
- /planning → Planning & Sync (TWG/Fusion/QTR)
- /planning/calendar → Calendar view (events + milestones)
- /roi → ROI Overview
- /roi/events → Event ROI
- /roi/marketing → Marketing/Advertising ROI
- /roi/mac → MAC Utilization & ROI

School Recruiting (NO uploads)
- /schools → School Recruiting Overview
- /schools/contacts → School Contacts & Coverage
- /schools/alrl → ALRL outcomes
- /schools/roi → School ROI

Budget / Resources
- /budget → Budget Overview
- /budget/execution → Execution + burn rate
- /budget/roi → Spend → ROI mapping

Data Hub (ONLY place for uploads)
- /data-hub → Upload Center + Import History
- /data-hub/registry → Dataset Registry (supported formats/specs)
- /data-hub/history → Run history + errors + row counts
- /data-hub/storage → Historical storage view (coverage by date)

Resources & Training
- /resources → Resources library
- /training → Training modules

Help Desk + System Status
- /helpdesk/new → Submit ticket form
- /helpdesk/status → Ticket status + comment trail only
- /system-status → System status + updates only

Admin (role-gated)
- /admin → Admin home
- /admin/users → user + roles
- /admin/thresholds → KPI thresholds (USAREC + unit comparisons)
- /admin/datasets → dataset registry management
- /admin/audit → audit logs

ROLE ACCESS:
- Roles: ADMIN, TAAIP_420T, COMMAND
- Admin sees entire app
- 420T: full operational pages if granted
- Command: limited pages (Command Center, dashboards, status pages, planning read-only as granted)
- Implement route guards and hide nav by role
- Roles come from GET /api/auth/me or /api/v2/auth/me (standardize to ONE and update frontend)

BACKEND API CONTRACTS — IMPLEMENT EXACTLY (v2):
ORG:
- GET /api/v2/org/units-summary
- GET /api/v2/org/children?parent_rsid={RSID}&echelon={BDE|BN|CO}

Command Center:
- GET /api/v2/command/summary?unit_rsid={RSID}&start={YYYY-MM-DD}&end={YYYY-MM-DD}
Response:
{
 "unit_rsid":"USAREC",
 "date_range":{"start":"2026-01-01","end":"2026-01-31"},
 "kpis":{"contracts":0,"mission_attainment_pct":0,"hq_pct":0,"leads":0,"cpl":0,"cpc":0,"flash_to_bang_days_median":0},
 "alerts":[{"code":"CPC_HIGH","severity":"RED","message":"..."}],
 "recommendations":[{"id":"rec_001","type":"MAC_REALLOC","text":"..."}]
}

Funnel:
- GET /api/v2/funnel/summary?unit_rsid={RSID}&start=&end=
Response:
{
 "stages":[{"stage":"LEAD","count":0},{"stage":"CONTACTED","count":0},{"stage":"APPT","count":0},{"stage":"PROCESSING","count":0},{"stage":"CONTRACT","count":0}],
 "conversion_rates":{"lead_to_contacted":0,"lead_to_contract":0},
 "flash_to_bang":{"median_days":0,"p75_days":0}
}

ROI:
- GET /api/v2/roi/overview?unit_rsid=&start=&end=&compare={A|B|C}&attribution_mode=hybrid
- GET /api/v2/roi/events?unit_rsid=&start=&end=&compare={A|B|C}&attribution_mode=hybrid
- GET /api/v2/roi/events/{event_id}?unit_rsid=&compare={A|B|C}&attribution_mode=hybrid
Return the “detail” schema exactly as provided in the spec with inputs/outputs/attribution/kpis/status/recommendations.

Planning:
- GET  /api/v2/planning/qtr-plan?unit_rsid={RSID}&fy=2026&qtr=2
- POST /api/v2/planning/qtr-plan
- GET  /api/v2/planning/twg/issues?unit_rsid={RSID}&status=open
- POST /api/v2/planning/twg/issues
- PATCH /api/v2/planning/twg/issues/{id}

Schools (NO uploads):
- GET /api/v2/schools/summary?unit_rsid=&start=&end=
- GET /api/v2/schools/schools?unit_rsid=&cbsa=
- GET /api/v2/schools/alrl?unit_rsid=&start=&end=
- GET /api/v2/schools/roi?unit_rsid=&start=&end=

Budget:
- GET /api/v2/budget/summary?unit_rsid=&fy=
- GET /api/v2/budget/execution?unit_rsid=&fy=
- GET /api/v2/budget/roi?unit_rsid=&start=&end=

Help Desk:
- POST /api/v2/helpdesk/tickets
- GET  /api/v2/helpdesk/tickets/{ticket_id}
- GET  /api/v2/helpdesk/tickets?requester={user_id}&role_view=
- POST /api/v2/helpdesk/tickets/{ticket_id}/comments

System Status:
- GET /api/v2/system/status
- GET /api/v2/system/updates

Auth:
- GET /api/auth/me OR GET /api/v2/auth/me (pick one, standardize)
- POST /api/auth/login
- POST /api/auth/logout
RULE: If /api/auth/me returns 401, auth isn’t wired for the UI session. If it returns user+roles, auth is live.

DATA HUB (ONLY upload center):
- GET  /api/v2/datahub/registry  (canonical registry response with datasets[])
- POST /api/v2/datahub/upload    (multipart, detect→validate→normalize→load→aggregate)
- GET  /api/v2/datahub/runs/{run_id}

DATA MODEL TABLES — IMPLEMENT MINIMUM VIABLE:
Reference:
- org_unit (rsid PK, display_name, echelon, parent_rsid, uic, unit_key optional)

Ingestion:
- dataset_registry (dataset_key PK, source_system, file_types, required_columns json, optional_columns json, detection_keywords json, target_tables json, version, enabled)
- import_run (run_id PK, dataset_key, filename, uploaded_by, status, row_count_in/out, error_summary, started_at, ended_at)
- import_run_errors (run_id FK, row_num, column, error_code, message)

TOR analytics:
- fact_lead_activity (lead_id stable hash, unit_rsid, cbsa, zip, source_channel, created_dt, first_contact_dt, last_activity_dt, stage, contract_dt nullable, contract_flag bool, hq_flag bool)
- fact_event (event_id, unit_rsid, cbsa, zip, event_dt, event_type, macs_requested, macs_assigned, macs_used, cost_event, cost_marketing, cost_travel, notes)
- bridge_event_attribution (event_id, lead_id, attribution_rule, attributed_flag, attributed_dt)
- fact_budget_spend (spend_id, unit_rsid, category, amount, spend_dt, vendor, notes)
- fact_school_engagement (school_id, unit_rsid, cbsa, zip, engagement_dt, type, leads_generated, contacts, contracts_attributed)

Derived:
- mv_kpis_daily OR agg_kpis_period (unit_rsid, date/period, leads, contacts, contracts, hq, conversion, flash_to_bang, CPL, CPC)
- roi_event_summary (event_id, unit_rsid, spend_total, leads_attributed, contracts_attributed, cpl, cpc, roi_score_A, roi_score_B, roi_score_C, status_color)

HYBRID ATTRIBUTION REQUIREMENT:
- Use hybrid attribution because contracts may come from events, MACs, advertising, goarmy.com, phone/text/email, walk-ins, ALRL, etc.
- Do NOT force single-touch.
- Implement attribution_mode=hybrid param and ensure ROI endpoints output detailed counts (leads, contacts, appts, processing, contracts) and flash-to-bang metrics in detail.

OUTPUT DOCUMENTATION:
- docs/ROUTES_SNAPSHOT.after.json
- docs/API_CONTRACTS.after.md with sample requests/responses

NO DEMO DATA:
Return empty arrays + zeros cleanly if tables are empty.

DO NOT DELETE ROUTES. If merging redundancy, keep old route and redirect.
