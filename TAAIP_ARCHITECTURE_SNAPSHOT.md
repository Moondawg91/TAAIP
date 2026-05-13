# TAAIP — Full Architecture Snapshot
> **Purpose:** Feed this document into a new Copilot session so it can analyze the current application build and help plan the next development phase.
> **Generated from live workspace on:** macOS (iCloud Drive / TAAIP)

---

## 1. Monorepo Root Layout

```
TAAIP/
├── services/
│   └── api/
│       └── app/          ← FastAPI backend (Python 3.10)
├── taaip-dashboard/      ← React 18 + TypeScript + Vite 5 frontend
├── data/
│   └── taaip.sqlite3     ← SQLite3 production database
├── docker-compose.yml
├── ecosystem.config.cjs  ← PM2 process manager config
├── requirements.txt      ← Python deps
├── run-dev.sh            ← Local dev startup script
├── start-taaip.sh        ← Production startup script
└── deploy-*.sh           ← Various DigitalOcean deploy scripts
```

---

## 2. Backend — FastAPI (Python)

### Entry Point
- `services/api/app/main.py` — FastAPI app init, router registration, CORS, static file mount (`dist/static/`)
- `services/api/app/db.py` — SQLite3 connection (`data/taaip.sqlite3`), schema bootstrap with `safe_add_column()` runtime migration helper
- `services/api/app/auth.py` + `api_auth.py` — JWT validation; `LOCAL_DEV_AUTH_BYPASS=1` env var skips auth in local dev
- `services/api/app/rbac.py` + `seed_rbac.py` — role-based access control

### Models / Schemas
- `models.py` — core SQLAlchemy/Pydantic models
- `models_domain.py` — domain-specific models
- `models_ingest.py` — data import models
- `models_refresh.py` — data refresh models
- `schemas.py`, `schemas_domain.py`, `schemas_decision_output.py` — Pydantic V2 schemas
- All models use Pydantic V2 (`model_config = ConfigDict(from_attributes=True)`)

### CRUD Layer
- `crud.py` — core CRUD operations
- `crud_domain.py` — domain CRUD

### Services Layer (`services/api/app/services/`)
| Service File | Purpose |
|---|---|
| `targeting_operation_linker.py` | Auto-creates an `operations_records` row when a `targeting_board_decisions` row is Approved/Modified |
| `targeting_board_engine.py` | Board session scoring and decision logic |
| `targeting_engine.py` | Nomination scoring and pipeline state machine |
| `targeting_expansion.py` | Market target expansion |
| `targeting_execution_tracker.py` | Execution status tracking |
| `fusion_engine.py` | Fusion cell process engine |
| `twg_engine.py` | TWG processing engine |
| `market_engine.py` + `market_engine_contract.py` | Market health and opportunity scoring |
| `market_health_engine.py` | Market health scoring |
| `market_qma.py` + `market_qma_contract.py` | QMA (Qualified Military Available) computations |
| `market_targeting.py` | Market-to-target linkage |
| `funnel_engine.py` + `funnel_engine_contract.py` | Recruiting funnel analytics |
| `coa_engine.py` | Course of Action recommendation engine |
| `mission_allocation_engine.py` | Mission allocation optimization |
| `mission_risk_engine.py` | Risk scoring |
| `mission_decrease_justification.py` | Justification builder for decreasing targets |
| `roi_engine.py` | ROI computation |
| `loe_engine.py` | Line of Effort scoring |
| `asset_engine.py` | Recruiting asset tracking |
| `school_targeting.py` + `school_plan_engine.py` | School program planning |
| `school_access.py` + `school_access_contract.py` | School access evaluation |
| `lead_line.py` | Lead pipeline processing |
| `forecasting.py` | Mission forecast modeling |
| `what_if.py` | What-if scenario analysis |
| `confidence.py` | Confidence scoring |
| `ai_lms.py` | LMS AI bridge |
| `ai_recommendation_engine.py` | AI-driven recommendation service |
| `accountability_engine.py` | Accountability tracking |
| `adaptive_update_engine.py` | Adaptive data update processing |
| `live_context_engine.py` | Live context data provider |
| `lms_performance_bridge.py` | LMS-to-performance data bridge |
| `outcome_learning_engine.py` | Outcome capture and learning |
| `execution_quality.py` + `execution_quality_contract.py` | Execution quality scoring |
| `flash_to_bang_processing_engine.py` | Flash-to-bang metric computation |
| `dataset_orchestrator.py` | Data pipeline orchestrator |
| `ingest_contracts.py` | Data ingest contracts/interfaces |
| `decision_writeback.py` | Write board decisions back to source tables |
| `doctrine.py` | Doctrine-based rule evaluation |
| `refresh_admin.py` | Data refresh administration |

### Automation
- `automation/engine.py` — background task / automation rules engine

### Data Layer (`services/api/app/data/`)
- `asset_registry.py` — asset catalog
- `commander_intent_store.py` — commander intent persistence
- `context_provider.py` — live context aggregator
- `funnel_loader.py` — funnel data loader
- `mission_alignment_registry.py` — mission alignment data

### Importers (`services/api/app/importers/`)
- `detect.py` — file format detection (CSV/Excel/JSON)
- `parse.py` — generic parser
- `validate.py` — schema validation
- `registry.py` — importer registry
- `unit_mapping.py` — unit/org hierarchy mapping
- `emm_portal.py` — EMM portal import
- `usarec_g2_enlistments_by_bn.py` — USAREC G2 enlistments importer
- `usarec_org_hierarchy.py` — org hierarchy importer
- `loaders/load_emm.py`, `loaders/load_enlistments.py` — specialized loaders

### AI Layer (`services/api/app/ai/`)
| File | Purpose |
|---|---|
| `orchestrator.py` | Routes AI tasks to appropriate workflow/provider |
| `prompt_registry.py` | Central prompt library |
| `task_classifier.py` | Intent classification for incoming AI requests |
| `policy_guardrails.py` | Content safety / policy enforcement |
| `audit_logger.py` | AI decision audit trail |
| `response_normalizer.py` | Normalize multi-provider responses to common schema |
| `feasibility_narrative.py` | Generate mission feasibility narratives |
| `router.py` | FastAPI AI endpoints |

**AI Providers** (`services/api/app/ai/providers/`):
- `openai_provider.py`, `anthropic_provider.py`, `gemini_provider.py`, `groq_provider.py`, `perplexity_provider.py`

**AI Workflows** (`services/api/app/ai/workflows/`):
- `mdmp_workflow.py` — Military Decision Making Process AI workflow
- `mipoe_workflow.py` — MIPOE (market/environmental intel) AI workflow
- `commander_summary_workflow.py` — Commander decision summary generation
- `lms_tutor_workflow.py` — LMS AI tutor (quiz gen, feedback, personalization)
- `recommendation_workflow.py` — AI recommendation generation

**Knowledge Pipeline** (`services/api/app/ai/knowledge/`):
- `document_ingest.py` — Document ingestion pipeline
- `chunking.py` — Text chunking for RAG
- `embeddings.py` — Vector embedding generation
- `indexing.py` — Vector index management
- `citations.py` — Citation tracking for RAG answers

### Routers (`services/api/app/routers/`)
All registered in `main.py`. Complete list:

**Core / Auth / Admin:**
`auth_status.py`, `me.py`, `rbac.py`, `admin_v2.py`, `system.py`, `health.py`, `meta.py`, `maintenance.py`, `governance.py`

**Home / Feed:**
`home.py`, `home_feed.py`

**Targeting Pipeline (the primary workflow):**
- `targeting_pipeline.py` — nomination CRUD, board decision recording; triggers `targeting_operation_linker` to auto-create operations on Approved/Modified decisions
- `twg_workspace.py` — TWG agenda, items, tasks, minutes
- `board_workspace.py` — targeting board session workspace
- `boards.py` — board management
- `mission_to_targeting.py` — mission → targeting transition

**Fusion Cell:**
- `fusion_process.py` — Fusion process CRUD
- `fusion_workspace.py` — Fusion workspace

**Operations / Execution:**
- `operations.py` — operations CRUD
- `operations_market.py` — operations market linkage
- `operations_summary.py` — operations rollup summary
- `compat_shell.py` (**KEY — 6000+ lines**) — "locked view" aggregated endpoints:
  - `GET /v2/operations/locked` — operations list with linked field activities + rollup metrics
  - `POST /v2/operations/{id}/field-activities` — create field activity linked to operation
  - `GET /v2/field-activities/locked` — field activities with operation name resolution + filter by `linked_operation_id`
  - `GET /v2/market-intel/locked`, `GET /v2/roi/locked`, `GET /v2/budget/locked`

**Market Intelligence:**
`market_core.py`, `market_engine.py`, `market_intel.py`, `ops_market_intel.py`

**Mission:**
`mission_pipeline.py`, `mission_alignment.py`, `mission_alignment_scoring.py`, `mission_assessments.py`, `mission_bundle.py`, `mission_bundle_pipeline.py`, `mission_documents.py`, `mission_extraction.py`, `mission_upload_pipeline.py`, `mission_uploads.py`, `mission_uploads_real.py`

**Planning:**
`coa.py`, `budgets.py`, `budget_dashboard.py`, `budget_summary.py`, `roi.py`, `compat_roi.py`, `planning_summary.py`, `command_priorities.py`

**School Recruiting:**
`school.py`, `school_recruiting.py`, `school_program.py`

**Lead / Funnel:**
`funnel.py`, `events.py`, `events_dashboard.py`, `event_ops.py`, `fs_loss.py`

**Analytics / Reporting:**
`analytics.py`, `performance_dashboard.py`, `performance_summary.py`, `tactical_dashboards.py`, `tactical_rollups.py`, `rollups.py`, `scoring.py`, `benchmarks.py`, `metrics.py`

**Calendar:**
`calendar.py`

**Assets / Resources:**
`assets.py`, `asset_recommendations.py`, `ref_assets.py`, `resources.py`

**Data Ingestion:**
`imports.py`, `imports_compat.py`, `imports_foundation.py`, `imports_mi.py`, `import_templates.py`, `datahub.py`, `uploads.py`, `ingest.py` (root-level), `storage.py`

**Documents:**
`docs.py`, `documents.py`

**AI / LMS:**
`ai_opportunity.py`, `training.py`

**Org / Commander:**
`commander_intent.py`, `commander_intent_ingest.py`, `compat_org.py`, `debug_org.py`

**Working Groups:**
`working_groups.py`

**Integrations:**
`emm_integration.py`, `emm_sync.py`, `phonetics.py`, `powerbi_feed.py`

**Other:**
`projects.py`, `projects_dashboard.py`, `tasks.py`, `tasks_compat.py`, `meetings.py`, `regulatory.py`, `exports.py`, `exports_dashboards.py`, `helpdesk.py`, `automation.py`, `refresh.py`, `dashboards.py`

**V2 Routers:**
`v2.py`, `v2_ai_lms.py`, `v2_analytics.py`, `v2_coa_compare.py`, `v2_datahub.py`, `v2_fusion.py`, `v2_home.py`, `v2_mission_allocation.py`, `v2_mission_feasibility.py`, `v2_mission_leadline.py`, `v2_org.py`, `v2_station_dashboard.py`, `v2_station_ingest.py`

**Legacy:**
`v1.py`, `compat_helpers.py`, `compat_importers.py`, `compat_roi.py`

---

## 3. Database — SQLite3

**Location:** `data/taaip.sqlite3`
**Migration strategy:** No Alembic on startup; `safe_add_column()` helper in `db.py` adds columns idempotently at boot.

### Key Tables (complete list from `.tables`):

**Targeting / Operations Pipeline:**
- `targeting_pipeline_records` — nominations (source records entering the targeting pipeline)
- `targeting_board_decisions` — board decisions per nomination; columns include `operation_id`, `operation_created_at` (added by bootstrap)
- `targeting_pipeline_history` — state change history
- `targeting_pipeline_comments` — comments on pipeline records
- `targeting_follow_on_actions` — follow-on action items from board
- `operations_records` — execution operations; columns include `source_nomination_id`, `source_board_decision_id`, `origin_title`, `origin_type`, `approved_budget`, `fund_source` (added by bootstrap)
- `field_activity_records` — field activities linked to operations; columns include `linked_operation_id`, `source_nomination_id`, `source_board_decision_id` (added by bootstrap)

**Fusion / TWG:**
- `fusion_process`, `fusion_agenda_items`, `fusion_evidence`, `fusion_findings`, `fusion_notes`, `fusion_recommendations`
- `twg_agenda_items`, `twg_board_items`, `twg_items`, `twg_minutes`, `twg_tasks`
- `working_group`

**Board:**
- `board`, `board_decisions`, `board_session`, `board_execution_items`, `board_resource_allocations`, `board_metric_snapshot`

**Market Intelligence:**
- `market_capacity`, `market_category_rule`, `market_category_weights`, `market_cbsa_fact`, `market_cbsa_metrics`, `market_demographics`, `market_demographics_fact`, `market_geotarget_zone`, `market_health_evidence`, `market_health_scores`, `market_rules`, `market_sama_zip_fact`, `market_target_list`, `market_targets`, `market_taxonomy`, `market_zip_fact`, `market_zip_metrics`
- `mi_cbsa_fact`, `mi_demo_fact`, `mi_dataset_registry`, `mi_enlistments_bde`, `mi_enlistments_bn`, `mi_import_template`, `mi_mission_category_ref`, `mi_school_fact`, `mi_zip_fact`
- `g2_market_metric`

**Mission / Allocation:**
- `mission_target`, `mission_assessments`, `mission_feasibility_narrative`, `mission_allocation_runs`, `mission_allocation_company_scores`, `mission_allocation_evidence`, `mission_allocation_inputs`, `mission_allocation_recommendations`, `mission_risk_evidence`, `mission_risk_scores`, `agg_mission_feasibility`, `feasibility_snapshot`

**Planning:**
- `coa_recommendations`, `budgets`, `budget_line_item`, `fy_budget`, `funding_sources`, `loe`, `loes`, `loe_metrics`, `roi_thresholds`

**School / Recruiting:**
- `schools`, `school_contacts`, `school_accounts`, `school_activities`, `school_fact`, `school_milestones`, `school_program_fact`, `school_program_leads`, `school_zone_assignments`, `alrl_school`, `dim_school_contact`, `fact_school_contacts`, `fact_school_contracts`, `fact_alrl`, `fact_alrl_outcomes`

**Leads / Funnel:**
- `leads`, `funnel_stages`, `funnel_transitions`, `lead_journey_fact`, `fact_lead_journey`, `fact_funnel`, `processing_metrics`

**Events / Field Activities:**
- `events`, `calendar_events`, `calendar_event`, `event`, `event_aar`, `event_fact`, `event_metrics`, `event_plan`, `event_risk`, `event_roi`, `emm_event`, `emm_mac`, `geo_campaign_fact`

**Analytics / Reporting:**
- `fact_enlistments`, `fact_enlistments_bn`, `fact_production`, `fact_productivity`, `fact_marketing`, `fact_market_share_contracts`, `fact_emm`, `fact_emm_activity`, `fact_emm_events`, `fact_mission_category`, `fact_dep_loss`, `fact_zip_potential`, `cep_fact`, `spend_fact`
- `recruiter_strength`, `burden_inputs`, `burden_snapshots`, `fstsm_metric`

**Org / Units:**
- `companies`, `stations`, `battalions`, `brigades`, `commands`, `units`, `org_unit`, `dim_org_unit`, `station_zip_coverage`
- `dim_time`, `external_census`, `external_social`

**Users / Auth / RBAC:**
- `users`, `user_account`, `user_role`, `user_roles`, `user_permission`, `user_permission_override`, `user_preferences`, `user_decisions`, `role`, `roles`, `role_permission`, `role_template`, `role_template_permission`, `permission`, `security_roles`, `invite_token`

**AI / LMS:**
- `lms_courses`, `lms_enrollments`, `module_registry`, `controlled_learning_config_version`, `controlled_learning_context_signals`, `controlled_learning_outcomes`, `controlled_learning_adaptive_proposals`
- `outcome_records`, `recommendation_explanations`

**Data Ingestion:**
- `import_job`, `import_job_preview`, `import_job_v3`, `import_file`, `import_column_map`, `import_mapping_template`, `import_error`, `import_row_error`, `import_run`, `import_run_v2`, `import_run_error_v2`
- `ingest_file`, `ingest_run`, `ingest_runs`, `ingest_row_error`, `ingested_files`, `imported_rows`
- `dataset_registry`, `dataset_active`, `dataset_versions`, `mi_dataset_registry`, `phonetic_dataset_registry`
- `stg_raw_dataset`, `stg_raw_dataset_profile`, `raw_file_storage`, `staging_uploads`, `refresh_staging_rows`
- `refresh_jobs`, `refresh_history`, `refresh_sources`, `refresh_dataset_rows`
- `data_upload`, `doc_blob`, `doc_library`, `doc_library_item`, `documents`, `transform_recipes`, `export_job`, `export_file`, `export_audit`

**Home / Feed:**
- `home_flash_items`, `home_flashes`, `home_alerts`, `home_messages`, `home_recognition`, `home_reference_rails`, `home_references`, `home_upcoming`, `announcement`, `release_notes`

**System / Admin:**
- `audit_log`, `audit_logs`, `api_error_log`, `system_observations`, `system_settings`, `system_update`, `maintenance_flags`, `maintenance_runs`, `maintenance_schedules`
- `tasks`, `task`, `task_assignment`, `task_comment`, `action_items`, `tickets`
- `projects`, `project`, `project_event_link`, `meetings_minutes` (meeting_minutes), `surveys`
- `change_proposals`, `change_reviews`, `decisions`, `user_decisions`
- `regulatory_references`, `regulatory_traceability`

**Assets / Resources:**
- `asset_catalog`, `asset_inventory`, `asset_assignments`, `asset_capabilities`, `asset_requests`
- `geo_target_zones`, `geo_target_zone_members`, `geo_planning_container`
- `priority_loe`, `resource_link`, `loe_metrics`

---

## 4. Frontend — React 18 + TypeScript + Vite 5

### Tech Stack
- **Framework:** React 18, TypeScript
- **Build:** Vite 5.4.21 — outputs to `taaip-dashboard/dist/`
- **CSS:** TailwindCSS
- **Charts:** Recharts
- **Icons:** lucide-react
- **HTTP:** axios + native fetch (both used)
- **Date:** date-fns
- **CSV:** papaparse
- **BI:** powerbi-client, powerbi-client-react

### Configuration
- `taaip-dashboard/src/config/api.ts` — exports `API_BASE` (e.g. `http://localhost:8010`)
- `taaip-dashboard/src/lib/authSession.ts` — auth session helpers
- `taaip-dashboard/src/types/auth.ts` — auth types

### Routing
Single-page app with tab-based navigation in `App.tsx`. URL query params `?activeTab=<id>&?operation_id=<id>` support deep-linking.

### Tab → Component Map

| Tab ID | Label | Component |
|---|---|---|
| `home` | Home | `HomeScreen` |
| `command-center` | Dashboard | `CommandCenterDashboard` |
| `scoreboard` | Scoreboard | `ScoreboardPage` |
| `school-recruiting` | School Recruiting | `TalentAcquisitionTechnicianDashboard` |
| `lead-generation` | Lead Generation | `LeadStatusReport` |
| `funnel-processing` | Funnel / Processing | `RecruitingFunnelDashboard` |
| `future-soldier-management` | Future Soldier Management | `FutureSoldierManagementDashboard` |
| `training-lms` | Training / LMS | `LMSHub` |
| `analytics` | Analytics | `AnalyticsDashboard` |
| `market-intelligence` | Market Intelligence | `MarketIntelligencePage` |
| `mission-analysis` | Mission Analysis | `MissionAnalysisDashboard` |
| `mission-feasibility` | Mission Feasibility | `MissionAdjustmentDashboard` |
| `fusion-cell` | Fusion Cell | `FusionTeamDashboard` |
| `twg` | TWG | `TargetingWorkingGroup` |
| `targeting-board` | Targeting Board | `TargetingBoard` |
| `planning-coa` | COA Alignment | `ProjectManagement` |
| `planning-budget` | Budget Alignment | `BudgetTracker` |
| `planning-roi` | ROI Alignment | `EventPerformanceDashboard` |
| `execution-calendar` | Calendar | `CalendarSchedulerDashboard` |
| `execution-operations` | Operations | `ExecutionOperationsPage` |
| `execution-events` | Events (Field Activities) | `FieldActivitiesDashboard` |
| `document-data-hub` | Data Hub | `UniversalDataUpload` |
| `document-sharepoint` | SharePoint Integration | `SharePointIntegration` |
| `admin-roles` | Role Management | `UserManagement` |
| `admin-help-tickets` | Help Tickets | `HelpDeskPortal` |
| `admin-work-management` | Work Management | `AdminConsole` |

### Component Inventory (`taaip-dashboard/src/components/`)

**Home / Shell:**
- `HomeScreen.tsx` — 4 sections: Flash Updates, TAWO of the Month (photo block), WOPD Updates, Proponent Updates
- `CommandCenterDashboard.tsx` — primary commander dashboard with KPI rollups
- `ScoreboardPage.tsx`

**Recruiting Pipeline:**
- `TalentAcquisitionTechnicianDashboard.tsx` — school recruiting
- `LeadStatusReport.tsx` — lead generation
- `RecruitingFunnelDashboard.tsx` — funnel stages and processing
- `FutureSoldierManagementDashboard.tsx` — DEP/FS management
- `LMSHub.tsx` — learning management system hub
- `AnalyticsDashboard.tsx`

**Market Intelligence / Mission:**
- `MarketIntelligencePage.tsx` — market targets, QMA, health scores
- `MissionAnalysisDashboard.tsx` — mission analysis (uses `API_BASE` directly)
- `MissionAdjustmentDashboard.tsx` — mission feasibility and adjustments

**Targeting Pipeline (Fusion → TWG → Board → Ops):**
- `FusionTeamDashboard.tsx` — Fusion cell workspace
- `TargetingWorkingGroup.tsx` — TWG workflow
- `TargetingBoard.tsx` — targeting board with nomination scoring
- `TargetingDecisionBoard.tsx` — board decision recording UI

**Planning:**
- `ProjectManagement.tsx` — COA alignment
- `BudgetTracker.tsx` — budget alignment and tracking
- `EventPerformanceDashboard.tsx` — ROI alignment

**Execution:**
- `CalendarSchedulerDashboard.tsx` — calendar events
- `ExecutionOperationsPage.tsx` (**NEW**) — operations execution tracking with:
  - Deep-link via `?operation_id=` URL param
  - Detail panel with "Add Field Activity" modal
  - Linked activity list with leads/engagements/contracts rollup
  - `execution_status_from_activities` display
- `FieldActivitiesDashboard.tsx` (**UPDATED**) — field activities table with:
  - Operation linkage column (clickable name or "Unlinked Activity" badge)
  - `openLinkedOperation()` deep-link to Operations tab

**Data / Documents:**
- `UniversalDataUpload.tsx` — wrapper for `DataKnowledgeDashboard`
- `DataKnowledgeDashboard.tsx` — full data upload and knowledge pipeline UI
- `SharePointIntegration.tsx`

**Admin:**
- `UserManagement.tsx` — RBAC role management
- `HelpDeskPortal.tsx` — help ticket system
- `AdminConsole.tsx` — work management / task admin

**Other Components (partial list):**
- `MarketTargetMap.tsx`, `MarketHealthScorecard.tsx`, `MarketDemographicAnalysis.tsx`
- `MissionAllocationDashboard.tsx`, `MissionRiskDashboard.tsx`
- `ROIDashboard.tsx`, `BudgetDashboard.tsx`
- `OperationsManagementDashboard.tsx` (legacy operations view)
- `EventManagementDashboard.tsx`
- `SchoolContactsDashboard.tsx`, `SchoolProgramDashboard.tsx`
- `TrainingCenterDashboard.tsx`, `TrainingModuleViewer.tsx`
- `AIAssistantPanel.tsx`, `AIRecommendationEngine.tsx`
- `ComplianceTracker.tsx`, `RegulatoryDashboard.tsx`
- `RecruiterPerformanceDashboard.tsx`
- `ForecastDashboard.tsx`, `WhatIfAnalysis.tsx`
- `GeoTargetingMap.tsx`, `StationDashboard.tsx`
- `PowerBIDashboard.tsx` — embedded Power BI reports
- `NotificationCenter.tsx`, `SystemHealthDashboard.tsx`

---

## 5. Targeting → Operations → Field Activities Linkage (Recently Completed)

This is the primary new feature pipeline, fully wired end-to-end:

```
MarketIntelligencePage
    → identifies target (zip/school/CBSA)
    → creates targeting_pipeline_records row (nomination)

TargetingWorkingGroup (TWG)
    → reviews nominations, adds agenda items
    → promotes nominations up to board

TargetingDecisionBoard / TargetingBoard
    → board members vote / record decision
    → POST /v2/targeting-pipeline/board-decision
        → saves targeting_board_decisions row
        → triggers targeting_operation_linker.create_operation_from_board_decision()
            → if status == "Approved" or "Modified"
            → auto-creates operations_records row
            → de-dupes by source_board_decision_id then source_nomination_id
        → response includes { operation_linkage: { operation_id, created } }

ExecutionOperationsPage
    → lists operations_records
    → deep-link: ?activeTab=execution-operations&operation_id=<id>
    → "Add Field Activity" modal → POST /v2/operations/{id}/field-activities
        → creates field_activity_records row
        → de-dupes by (op_id, name, date, time, location)
    → shows rollup: linked_activity_count, activity_results (leads/engagements/contracts)
    → shows execution_status_from_activities

FieldActivitiesDashboard
    → GET /v2/field-activities/locked (filter: linked_operation_id)
    → shows linked operation name (clickable)
    → "Open Linked Operation" → navigates to ExecutionOperationsPage with deep-link
```

### Key API Endpoints (new/updated):
- `POST /v2/targeting-pipeline/board-decision` — record board decision, auto-links operation
- `GET /v2/operations/locked` — operations with `linked_activities[]`, `linked_activity_count`, `activity_results`, `execution_status_from_activities`
- `POST /v2/operations/{operation_id}/field-activities` — create field activity linked to operation
- `GET /v2/field-activities/locked?linked_operation_id=X` — field activities with operation name, filter support

---

## 6. AI / LMS Capabilities

### AI Engine
- Multi-provider: OpenAI, Anthropic (Claude), Google Gemini, Groq, Perplexity
- Orchestrator routes tasks based on `task_classifier.py` intent detection
- `policy_guardrails.py` enforces content safety
- All AI calls logged via `audit_logger.py`

### Workflows
| Workflow | Trigger | Output |
|---|---|---|
| MDMP | Mission analysis request | Military Decision Making Process narrative |
| MIPOE | Market intel analysis | Intel prep / environmental analysis |
| Commander Summary | Board decision event | Plain-language commander decision brief |
| LMS Tutor | Training module request | Personalized lessons, quizzes, feedback |
| Recommendation | COA / resource request | Ranked recommendations with rationale |

### Knowledge / RAG Pipeline
- Documents ingested via `document_ingest.py`
- Chunked → embedded → indexed for vector retrieval
- Citations tracked for RAG answers
- Accessible via `DataKnowledgeDashboard` → `UniversalDataUpload`

### LMS
- Courses: `lms_courses`, enrollments: `lms_enrollments`
- Controlled learning with adaptive proposals (`controlled_learning_*` tables)
- Performance bridge to operations data (`lms_performance_bridge.py`)
- Frontend: `LMSHub.tsx`, `TrainingCenterDashboard.tsx`, `TrainingModuleViewer.tsx`
- Backend: `v2_ai_lms.py`, `services/ai_lms.py`, `ai/workflows/lms_tutor_workflow.py`

---

## 7. Infrastructure

### Local Development
- Backend: `uvicorn services.api.app.main:app --reload --port 8010`
- Frontend: `cd taaip-dashboard && npm run dev` (Vite dev server, port 5173)
- Auth bypass: `LOCAL_DEV_AUTH_BYPASS=1`
- DB: SQLite at `data/taaip.sqlite3`

### Production
- Process manager: PM2 (`ecosystem.config.cjs`)
- Platform: DigitalOcean Droplet
- Backend production build: backend serves static from `dist/static/` (post-build: `mv dist/assets dist/static`)
- Deploy scripts: `deploy-to-droplet.sh`, `deploy-digitalocean.sh`, etc.

### Key Environment Variables
- `LOCAL_DEV_AUTH_BYPASS=1` — skip JWT auth in dev
- `DATABASE_URL` — overrides SQLite path (for PostgreSQL in prod)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `PERPLEXITY_API_KEY` — AI providers

### Python Dependencies
```
fastapi>=0.104.0, uvicorn>=0.24.0, pydantic>=2.0.0
sqlalchemy>=2.0.0, alembic>=1.11.1
pandas>=2.0.0, openpyxl>=3.1.0, papaparse (frontend)
PyJWT>=2.0.0, python-dotenv>=1.0.0
aiohttp>=3.9.0, httpx>=0.25.0, requests>=2.31.0
apscheduler>=3.10.0, celery>=5.3.0, redis>=5.0.0
python-multipart>=0.0.6, email-validator>=2.1.0
python-json-logger>=2.0.0, rq>=1.2.0
joblib>=1.3.0
```

---

## 8. Known Issues / Tech Debt

1. **`safe_add_column()` runtime migrations** — schema changes applied at startup via individual `ALTER TABLE` calls. Works but fragile; proper Alembic migration files not created for each change.

2. **`compat_shell.py` is 6000+ lines** — monolithic router file combining locked views for operations, field activities, market intel, ROI, and budget. Should be split into separate domain routers.

3. **SQLite in production** — requirements.txt includes `psycopg2-binary` but SQLite is used. PostgreSQL migration path exists but not activated.

4. **Celery/Redis declared but not active** — `requirements.txt` lists celery/redis but no broker is running locally. Background tasks use APScheduler instead.

5. **`dist/static` vs `dist/assets`** — Vite outputs to `assets/`; backend mounts `dist/static/`. Post-build rename required for production static serving. Dev server is unaffected.

---

## 9. Development Backlog (Next Steps)

### High Priority
1. **Fusion Cell CRUD completeness** — `FusionTeamDashboard.tsx` exists but backend endpoints in `v2_fusion.py` / `fusion_process.py` may be incomplete. Need: create/edit fusion process, add evidence, record findings.

2. **TWG input flows** — `TargetingWorkingGroup.tsx` is partially read-only. Need: add agenda item modal, vote/promote nomination action, record TWG minutes.

3. **Operations CRUD** — `ExecutionOperationsPage.tsx` reads from `GET /v2/operations/locked` but cannot create operations manually (only auto-created from board decisions). Need: manual operation create form.

4. **Field Activity edit/delete** — currently only create. Need edit (update leads/contracts/outcomes) and soft-delete.

5. **HomeScreen live data** — Flash Updates, WOPD, Proponent Updates sections show placeholder text. Need endpoints wired to `home_flash_items`, `home_alerts`, `home_messages` tables.

### Medium Priority
6. **Mission feasibility → COA promotion** — `MissionAdjustmentDashboard` computes feasibility scores. Pipeline to promote feasible missions into COA recommendations (`coa_recommendations` table) not fully wired.

7. **Market Intel → TWG feed** — Market health scores should auto-populate TWG nomination queue. `market_targeting.py` service exists but frontend linkage unclear.

8. **Budget → Operation linkage** — `approved_budget` and `fund_source` columns exist on `operations_records` (added by bootstrap) but not yet surfaced in `ExecutionOperationsPage`.

9. **LMS completion → Performance metrics** — `lms_performance_bridge.py` exists but the data flow from LMS completions into `fstsm_metric` / `fact_production` tables needs validation.

10. **Power BI feed** — `powerbi_feed.py` router and `PowerBIDashboard.tsx` component exist. Need verification that the feed endpoints match what the embedded reports expect.

### Lower Priority
11. **Alembic migration files** — create proper migration history for all `safe_add_column` calls.
12. **Split `compat_shell.py`** — refactor into domain-specific routers.
13. **PostgreSQL switch** — activate `DATABASE_URL` env var and test all queries with psycopg2.
14. **E2E test suite** — `services/api/app/tests/` has smoke tests; full workflow tests (Market Intel → Board Decision → Operation → Field Activity) not yet written.
15. **SharePoint integration** — `SharePointIntegration.tsx` exists; backend endpoint unclear.

---

## 10. File Quick Reference

| What | Path |
|---|---|
| FastAPI entry point | `services/api/app/main.py` |
| DB connection + bootstrap | `services/api/app/db.py` |
| Locked view mega-router | `services/api/app/routers/compat_shell.py` |
| Targeting board decision + auto-link | `services/api/app/routers/targeting_pipeline.py` |
| Operation auto-create service | `services/api/app/services/targeting_operation_linker.py` |
| AI orchestrator | `services/api/app/ai/orchestrator.py` |
| LMS tutor workflow | `services/api/app/ai/workflows/lms_tutor_workflow.py` |
| React app root + routing | `taaip-dashboard/src/App.tsx` |
| API base config | `taaip-dashboard/src/config/api.ts` |
| HomeScreen | `taaip-dashboard/src/components/HomeScreen.tsx` |
| Operations execution page | `taaip-dashboard/src/components/ExecutionOperationsPage.tsx` |
| Field activities dashboard | `taaip-dashboard/src/components/FieldActivitiesDashboard.tsx` |
| Targeting board | `taaip-dashboard/src/components/TargetingBoard.tsx` |
| Fusion cell | `taaip-dashboard/src/components/FusionTeamDashboard.tsx` |
| TWG | `taaip-dashboard/src/components/TargetingWorkingGroup.tsx` |
| Budget tracker | `taaip-dashboard/src/components/BudgetTracker.tsx` |
| LMS hub | `taaip-dashboard/src/components/LMSHub.tsx` |
| Data hub upload | `taaip-dashboard/src/components/DataKnowledgeDashboard.tsx` |
| SQLite database | `data/taaip.sqlite3` |
| Python requirements | `requirements.txt` |
| Frontend package.json | `taaip-dashboard/package.json` |
