-- Generated from SQLite catalog for TAAIP
BEGIN;
CREATE TABLE "action_items" (
    "action_id" TEXT,
    "minute_id" TEXT,
    "title" TEXT,
    "owner" TEXT,
    "due_date" TEXT,
    "status" TEXT,
    "created_at" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "keep_until" TEXT,
    "archived_at" TEXT,
    PRIMARY KEY ("action_id")
);

CREATE TABLE "agg_mission_feasibility" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "start_date" TEXT,
    "end_date" TEXT,
    "fy" BIGINT,
    "compare_mode" TEXT,
    "mission_annual" BIGINT,
    "recruiters_avg" DOUBLE PRECISION,
    "wr_required" DOUBLE PRECISION,
    "wr_actual" DOUBLE PRECISION,
    "market_capacity_est" DOUBLE PRECISION,
    "market_support_index" DOUBLE PRECISION,
    "market_burden_ratio" DOUBLE PRECISION,
    "recruiters_needed" DOUBLE PRECISION,
    "recruiter_delta" DOUBLE PRECISION,
    "status" TEXT,
    "drivers" TEXT,
    "narrative" TEXT,
    "recommendations" TEXT,
    "computed_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "aie_lead_stub" (
    "id" BIGINT,
    "aie_person_key" TEXT,
    "created_at" TEXT,
    "lead_source" TEXT,
    "unit_rsid" TEXT,
    "cbsa_code" TEXT,
    "source_import_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "alrl_school" (
    "id" BIGINT,
    "school_id" TEXT,
    "school_name" TEXT,
    "district" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip" TEXT,
    "unit_rsid" TEXT,
    "contact_name" TEXT,
    "contact_email" TEXT,
    "contact_phone" TEXT,
    "contract_status" TEXT,
    "contract_date" TEXT,
    "source_import_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "announcement" (
    "id" BIGINT,
    "org_unit_id" BIGINT,
    "category" TEXT,
    "title" TEXT,
    "body" TEXT,
    "effective_dt" TEXT,
    "expires_dt" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "api_error_log" (
    "id" TEXT,
    "endpoint" TEXT,
    "message" TEXT,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "asset_assignments" (
    "id" BIGINT,
    "assignment_id" TEXT,
    "request_id" TEXT,
    "asset_id" TEXT,
    "assigned_unit_rsid" TEXT,
    "assigned_start_dt" TEXT,
    "assigned_end_dt" TEXT,
    "assignment_status" TEXT,
    "notes" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_asset_assignments_1" UNIQUE ("assignment_id")
);

CREATE TABLE "asset_capabilities" (
    "id" BIGINT,
    "asset_id" TEXT,
    "capability_key" TEXT,
    "weight" DOUBLE PRECISION DEFAULT 1.0,
    PRIMARY KEY ("id")
);

CREATE TABLE "asset_catalog" (
    "id" BIGINT,
    "asset_id" TEXT,
    "asset_name" TEXT,
    "asset_type" TEXT,
    "category" TEXT,
    "supported_objectives" TEXT,
    "supported_tactics" TEXT,
    "description" TEXT,
    "constraints" TEXT,
    "requires_approval_level" TEXT,
    "enabled" BIGINT DEFAULT 1,
    "version" BIGINT DEFAULT 1,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_asset_catalog_1" UNIQUE ("asset_id")
);

CREATE TABLE "asset_inventory" (
    "id" BIGINT,
    "inventory_id" TEXT,
    "asset_id" TEXT,
    "owning_unit_rsid" TEXT,
    "holding_unit_rsid" TEXT,
    "status" TEXT,
    "available_from_dt" TEXT,
    "available_to_dt" TEXT,
    "notes" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_asset_inventory_1" UNIQUE ("inventory_id")
);

CREATE TABLE "asset_requests" (
    "id" BIGINT,
    "request_id" TEXT,
    "unit_rsid" TEXT,
    "event_id" TEXT,
    "requested_asset_type" TEXT,
    "requested_asset_ids" TEXT,
    "priority" TEXT,
    "needed_start_dt" TEXT,
    "needed_end_dt" TEXT,
    "justification" TEXT,
    "approval_status" TEXT,
    "approval_chain" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_asset_requests_1" UNIQUE ("request_id")
);

CREATE TABLE "audit_log" (
    "id" BIGINT,
    "who" TEXT,
    "action" TEXT,
    "entity" TEXT,
    "entity_id" BIGINT,
    "meta_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "audit_logs" (
    "id" VARCHAR NOT NULL,
    "actor" VARCHAR NOT NULL,
    "action" VARCHAR NOT NULL,
    "entity_type" VARCHAR NOT NULL,
    "entity_id" VARCHAR,
    "scope_type" VARCHAR,
    "scope_value" VARCHAR,
    "before_json" JSONB,
    "after_json" JSONB,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "automation_job" (
    "id" TEXT,
    "job_type" TEXT,
    "status" TEXT,
    "input_json" TEXT,
    "output_json" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "battalions" (
    "id" BIGINT NOT NULL,
    "battalion_prefix" VARCHAR(2) NOT NULL,
    "display" VARCHAR,
    "brigade_id" BIGINT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_battalions_1" UNIQUE ("battalion_prefix", "brigade_id"),
    CONSTRAINT "fk_battalions_0" FOREIGN KEY ("brigade_id") REFERENCES "brigades" ("id")
);

CREATE TABLE "board" (
    "id" BIGINT,
    "name" TEXT,
    "org_unit_id" BIGINT,
    "description" TEXT,
    "created_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "board_decisions" (
    "id" BIGINT,
    "board_id" TEXT NOT NULL,
    "decision_text" TEXT,
    "status" TEXT DEFAULT 'pending',
    "decided_at" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "board_execution_items" (
    "id" BIGINT,
    "board_id" TEXT NOT NULL,
    "title" TEXT,
    "details" TEXT,
    "status" TEXT DEFAULT 'open',
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "board_metric_snapshot" (
    "id" BIGINT,
    "board_session_id" BIGINT,
    "metric_key" TEXT,
    "metric_value" DOUBLE PRECISION,
    "captured_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "board_resource_allocations" (
    "id" BIGINT,
    "board_id" TEXT NOT NULL,
    "resource_type" TEXT,
    "quantity" BIGINT,
    "notes" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "board_session" (
    "id" BIGINT,
    "board_id" BIGINT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "session_dt" TEXT,
    "notes" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "brigades" (
    "id" BIGINT NOT NULL,
    "brigade_prefix" VARCHAR(1) NOT NULL,
    "display" VARCHAR,
    "command_id" BIGINT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_brigades_1" UNIQUE ("brigade_prefix", "command_id"),
    CONSTRAINT "fk_brigades_0" FOREIGN KEY ("command_id") REFERENCES "commands" ("id")
);

CREATE TABLE "budget_line_item" (
    "id" BIGINT,
    "fy_budget_id" BIGINT,
    "qtr" BIGINT,
    "event_id" BIGINT,
    "category" TEXT,
    "vendor" TEXT,
    "description" TEXT,
    "amount" DOUBLE PRECISION DEFAULT 0,
    "appropriation_type" TEXT DEFAULT 'OMA',
    "funding_source" TEXT,
    "sag_code" TEXT,
    "amsco_code" TEXT,
    "mdep_code" TEXT,
    "eor_code" TEXT,
    "is_under_cr" BIGINT DEFAULT 0,
    "status" TEXT,
    "obligation_date" TEXT,
    "notes" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "fy" BIGINT,
    "month" BIGINT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "funding_line" TEXT,
    "allocated_amount" DOUBLE PRECISION DEFAULT 0,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "station_rsid" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "ingested_at" TEXT,
    "project_id" TEXT,
    "obligated_amount" DOUBLE PRECISION DEFAULT 0,
    "expended_amount" DOUBLE PRECISION DEFAULT 0,
    PRIMARY KEY ("id")
);

CREATE TABLE "budgets" (
    "budget_id" TEXT,
    "event_id" TEXT,
    "campaign_name" TEXT,
    "allocated_amount" DOUBLE PRECISION,
    "start_date" TEXT,
    "end_date" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "keep_until" TEXT,
    "archived_at" TEXT,
    PRIMARY KEY ("budget_id")
);

CREATE TABLE "burden_inputs" (
    "id" VARCHAR NOT NULL,
    "scope_type" VARCHAR NOT NULL,
    "scope_value" VARCHAR NOT NULL,
    "mission_requirement" BIGINT NOT NULL,
    "recruiter_strength" BIGINT NOT NULL,
    "reporting_date" DATE NOT NULL,
    "source_system" VARCHAR,
    "reported_at" TIMESTAMP WITH TIME ZONE,
    "ingested_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "burden_snapshots" (
    "id" VARCHAR NOT NULL,
    "scope_type" VARCHAR NOT NULL,
    "scope_value" VARCHAR NOT NULL,
    "reporting_date" DATE NOT NULL,
    "mission_requirement" BIGINT NOT NULL,
    "recruiter_strength" BIGINT NOT NULL,
    "burden_ratio" DOUBLE PRECISION NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "calendar_event" (
    "id" BIGINT,
    "linked_type" TEXT,
    "linked_id" TEXT,
    "org_unit_id" TEXT,
    "title" TEXT,
    "start_dt" TEXT,
    "end_dt" TEXT,
    "location" TEXT,
    "notes" TEXT,
    "status" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "import_job_id" TEXT,
    "tags" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "calendar_events" (
    "event_id" TEXT,
    "org_unit_id" TEXT,
    "title" TEXT,
    "start_dt" TEXT,
    "end_dt" TEXT,
    "location" TEXT,
    "created_at" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "keep_until" TEXT,
    PRIMARY KEY ("event_id")
);

CREATE TABLE "cep_fact" (
    "id" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "rsid_prefix" TEXT,
    "school_id" TEXT,
    "asvab_tests" BIGINT,
    "asvab_high_score" BIGINT,
    "cep_events" BIGINT,
    "cep_participants" BIGINT,
    "leads_from_cep" BIGINT,
    "contracts_from_cep" BIGINT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "change_proposals" (
    "id" TEXT,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "rationale" TEXT,
    "impact_area" TEXT,
    "risk_level" TEXT,
    "status" TEXT NOT NULL,
    "created_by" TEXT,
    "created_at" TEXT NOT NULL,
    "reviewed_by" TEXT,
    "reviewed_at" TEXT,
    "decision_note" TEXT,
    "proposed_changes_json" TEXT NOT NULL,
    "submitted_by" TEXT,
    "updated_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "change_reviews" (
    "id" BIGINT,
    "proposal_id" BIGINT,
    "reviewer" TEXT,
    "decision" TEXT,
    "note" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "coa_recommendations" (
    "id" BIGINT NOT NULL,
    "coa_run_id" VARCHAR NOT NULL,
    "unit_rsid" VARCHAR(4) NOT NULL,
    "coa_type" VARCHAR NOT NULL,
    "coa_title" VARCHAR NOT NULL,
    "coa_summary" TEXT,
    "recommended_actions_json" JSONB,
    "expected_benefit" VARCHAR,
    "risk_level" VARCHAR,
    "assumptions_json" JSONB,
    "doctrine_refs_json" JSONB,
    "supporting_evidence_json" JSONB,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "command_priorities" (
    "id" BIGINT,
    "org_unit_id" BIGINT,
    "title" TEXT,
    "description" TEXT,
    "rank" BIGINT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "commands" (
    "id" BIGINT NOT NULL,
    "command" VARCHAR NOT NULL,
    "display" VARCHAR,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_commands_1" UNIQUE ("command")
);

CREATE TABLE "companies" (
    "id" BIGINT NOT NULL,
    "company_prefix" VARCHAR(3) NOT NULL,
    "display" VARCHAR,
    "battalion_id" BIGINT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_companies_1" UNIQUE ("company_prefix", "battalion_id"),
    CONSTRAINT "fk_companies_0" FOREIGN KEY ("battalion_id") REFERENCES "battalions" ("id")
);

CREATE TABLE "controlled_learning_adaptive_proposals" (
    "id" BIGINT,
    "proposal_id" TEXT NOT NULL,
    "proposal_type" TEXT NOT NULL,
    "target_engine" TEXT NOT NULL,
    "target_rule" TEXT,
    "scope_type" TEXT NOT NULL,
    "scope_value" TEXT NOT NULL,
    "current_state_json" TEXT,
    "proposed_state_json" TEXT,
    "reason" TEXT,
    "evidence_refs_json" TEXT,
    "risk_level" TEXT,
    "approval_required" BIGINT NOT NULL,
    "approval_state" TEXT NOT NULL,
    "rollback_plan" TEXT,
    "config_version_from" TEXT,
    "config_version_to" TEXT,
    "trace_id" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "controlled_learning_config_version" (
    "id" BIGINT,
    "config_version" TEXT NOT NULL,
    "state" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "controlled_learning_context_signals" (
    "id" BIGINT,
    "signal_id" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "subcategory" TEXT,
    "scope_hint" TEXT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "source" TEXT NOT NULL,
    "source_type" TEXT,
    "published_at" TEXT,
    "ingested_at" TEXT NOT NULL,
    "confidence" DOUBLE PRECISION,
    "trust_label" TEXT,
    "signal_summary" TEXT,
    "operational_implication" TEXT,
    "recommended_modifier_json" TEXT,
    "approval_required" BIGINT NOT NULL,
    "trace_id" TEXT,
    "stale_after_hours" BIGINT DEFAULT 72,
    PRIMARY KEY ("id")
);

CREATE TABLE "controlled_learning_outcomes" (
    "id" BIGINT,
    "recommendation_id" TEXT NOT NULL,
    "source_engine" TEXT NOT NULL,
    "scope_type" TEXT NOT NULL,
    "scope_value" TEXT NOT NULL,
    "target_object" TEXT,
    "recommendation_kind" TEXT,
    "rationale_snapshot" TEXT,
    "expected_kpi_json" TEXT,
    "expected_effect" TEXT,
    "expected_horizon" TEXT,
    "actual_kpi_json" TEXT,
    "actual_effect" TEXT,
    "observed_state" TEXT,
    "pattern_type" TEXT,
    "pattern_value" TEXT,
    "period_start" TEXT,
    "period_end" TEXT,
    "generated_at" TEXT,
    "measured_at" TEXT,
    "trace_id" TEXT,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "data_upload" (
    "id" BIGINT,
    "dataset_key" TEXT,
    "source_system" TEXT,
    "filename" TEXT,
    "file_hash" TEXT,
    "uploaded_by" TEXT,
    "uploaded_at" TEXT,
    "status" TEXT DEFAULT 'received',
    "row_count" BIGINT DEFAULT 0,
    "error_json" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "dataset_active" (
    "id" BIGINT NOT NULL,
    "source_id" BIGINT,
    "version_id" BIGINT,
    "bound_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "bound_by" VARCHAR,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_dataset_active_1" UNIQUE ("source_id"),
    CONSTRAINT "fk_dataset_active_0" FOREIGN KEY ("version_id") REFERENCES "dataset_versions" ("id"),
    CONSTRAINT "fk_dataset_active_1" FOREIGN KEY ("source_id") REFERENCES "refresh_sources" ("id")
);

CREATE TABLE "dataset_registry" (
    "dataset_key" TEXT,
    "source_system" TEXT,
    "display_name" TEXT,
    "enabled" BIGINT DEFAULT 1,
    "file_types" TEXT,
    "sheet_hints" TEXT,
    "detection_keywords" TEXT,
    "required_columns" TEXT,
    "optional_columns" TEXT,
    "primary_date_column" TEXT,
    "unit_columns" TEXT,
    "target_table" TEXT,
    "normalizer_key" TEXT,
    "version" BIGINT DEFAULT 1,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("dataset_key")
);

CREATE TABLE "dataset_versions" (
    "id" BIGINT NOT NULL,
    "source_id" BIGINT,
    "version" VARCHAR NOT NULL,
    "checksum" VARCHAR,
    "created_by" VARCHAR,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "row_count" BIGINT,
    "notes" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_dataset_versions_0" FOREIGN KEY ("source_id") REFERENCES "refresh_sources" ("id")
);

CREATE TABLE "decisions" (
    "id" VARCHAR NOT NULL,
    "scope_type" VARCHAR NOT NULL,
    "scope_value" VARCHAR NOT NULL,
    "decision_type" VARCHAR NOT NULL,
    "summary" VARCHAR NOT NULL,
    "details_json" JSONB,
    "created_by" VARCHAR NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "dim_org_unit" (
    "id" TEXT,
    "name" TEXT,
    "type" TEXT,
    "parent_id" TEXT,
    "rsid" TEXT,
    "uic" TEXT,
    "state" TEXT,
    "city" TEXT,
    "zip" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "dim_school_contact" (
    "school_id" TEXT,
    "school_name" TEXT,
    "address" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip" TEXT,
    "unit_rsid" TEXT,
    "source_system" TEXT,
    PRIMARY KEY ("school_id")
);

CREATE TABLE "dim_time" (
    "date_key" TEXT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "month" BIGINT,
    "recruiting_month" TEXT,
    "week_of_year" BIGINT,
    PRIMARY KEY ("date_key")
);

CREATE TABLE "doc_blob" (
    "id" TEXT,
    "item_id" TEXT,
    "filename" TEXT,
    "content_type" TEXT,
    "size_bytes" BIGINT,
    "sha256" TEXT,
    "path" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "doc_library" (
    "doc_id" TEXT,
    "title" TEXT,
    "description" TEXT,
    "url" TEXT,
    "uploaded_at" TEXT,
    "created_by" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "keep_until" TEXT,
    "archived_at" TEXT,
    PRIMARY KEY ("doc_id")
);

CREATE TABLE "doc_library_item" (
    "id" TEXT,
    "org_unit_id" BIGINT,
    "title" TEXT,
    "doc_type" TEXT,
    "tags_json" TEXT,
    "version" BIGINT DEFAULT 1,
    "effective_dt" TEXT,
    "uploaded_by" TEXT,
    "created_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "source_type" TEXT,
    "classification_confidence" DOUBLE PRECISION,
    "classified_by" TEXT,
    "classified_at" TEXT,
    "document_status" TEXT DEFAULT 'unclassified',
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "documents" (
    "id" TEXT,
    "filename" TEXT NOT NULL,
    "stored_path" TEXT NOT NULL,
    "content_type" TEXT,
    "size" BIGINT,
    "uploaded_by" TEXT,
    "uploaded_at" TEXT NOT NULL,
    "description" TEXT,
    "tags" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "emm_event" (
    "id" BIGINT,
    "event_id" TEXT,
    "mac_id" TEXT,
    "event_name" TEXT,
    "event_type" TEXT,
    "start_date" TEXT,
    "end_date" TEXT,
    "location_name" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip" TEXT,
    "cbsa_code" TEXT,
    "unit_rsid" TEXT,
    "cost_total" DOUBLE PRECISION,
    "notes" TEXT,
    "source_import_run_id" BIGINT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "emm_mac" (
    "mac_id" TEXT,
    "mac_name" TEXT,
    "mac_type" TEXT,
    "unit_rsid" TEXT,
    "status" TEXT,
    "source_import_run_id" BIGINT,
    PRIMARY KEY ("mac_id")
);

CREATE TABLE "event" (
    "id" BIGINT,
    "org_unit_id" BIGINT,
    "name" TEXT,
    "event_type" TEXT,
    "start_dt" TEXT,
    "end_dt" TEXT,
    "location_name" TEXT,
    "location_city" TEXT,
    "location_state" TEXT,
    "location_zip" TEXT,
    "cbsa" TEXT,
    "loe" DOUBLE PRECISION,
    "objective" TEXT,
    "status" TEXT,
    "poc" TEXT,
    "risk_level" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "planned_cost" DOUBLE PRECISION DEFAULT 0,
    "actual_cost" DOUBLE PRECISION DEFAULT 0,
    "fy" BIGINT,
    "qtr" BIGINT,
    "month" BIGINT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "funding_line" TEXT,
    "project_id" BIGINT,
    "station_id" TEXT,
    "category" TEXT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "station_rsid" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "ingested_at" TEXT,
    "event_category" TEXT,
    "school_id" TEXT,
    "planned_outcomes_json" TEXT,
    "actual_outcomes_json" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "event_aar" (
    "id" BIGINT,
    "event_id" BIGINT NOT NULL,
    "org_unit_id" BIGINT,
    "summary" TEXT,
    "lessons_json" TEXT,
    "recommendations" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "event_fact" (
    "event_id" TEXT,
    "unit_rsid" TEXT,
    "event_name" TEXT,
    "event_type" TEXT,
    "start_dt" TEXT,
    "end_dt" TEXT,
    "location" TEXT,
    "mac_id" TEXT,
    "requested_macs" BIGINT,
    "assigned_macs" BIGINT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("event_id")
);

CREATE TABLE "event_metrics" (
    "id" VARCHAR NOT NULL,
    "event_id" VARCHAR NOT NULL,
    "metric_date" DATE NOT NULL,
    "leads_generated" BIGINT,
    "leads_qualified" BIGINT,
    "conversions" BIGINT,
    "cost" DOUBLE PRECISION,
    "cost_per_lead" DOUBLE PRECISION,
    "roi" DOUBLE PRECISION,
    "engagement_rate" DOUBLE PRECISION,
    "reported_at" TIMESTAMP WITH TIME ZONE,
    "ingested_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_event_metrics_0" FOREIGN KEY ("event_id") REFERENCES "events" ("id")
);

CREATE TABLE "event_plan" (
    "id" BIGINT,
    "event_id" BIGINT NOT NULL,
    "org_unit_id" BIGINT,
    "plan_type" TEXT,
    "title" TEXT,
    "description" TEXT,
    "metadata_json" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "event_risk" (
    "id" BIGINT,
    "event_id" BIGINT NOT NULL,
    "org_unit_id" BIGINT,
    "title" TEXT,
    "likelihood" TEXT,
    "impact" TEXT,
    "mitigation" TEXT,
    "metadata_json" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "event_roi" (
    "id" BIGINT,
    "event_id" BIGINT NOT NULL,
    "org_unit_id" BIGINT,
    "metrics_json" TEXT,
    "expected_revenue" DOUBLE PRECISION,
    "expected_cost" DOUBLE PRECISION,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "events" (
    "id" VARCHAR NOT NULL,
    "station_rsid" VARCHAR(4),
    "brigade_prefix" VARCHAR(1),
    "battalion_prefix" VARCHAR(2),
    "company_prefix" VARCHAR(3),
    "name" VARCHAR NOT NULL,
    "event_type" VARCHAR NOT NULL,
    "location" VARCHAR,
    "start_date" TIMESTAMP WITH TIME ZONE,
    "end_date" TIMESTAMP WITH TIME ZONE,
    "budget" DOUBLE PRECISION,
    "status" VARCHAR NOT NULL DEFAULT 'planned',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "planned_cost" DOUBLE PRECISION DEFAULT 0,
    "actual_cost" DOUBLE PRECISION DEFAULT 0,
    "fy" BIGINT,
    "qtr" BIGINT,
    "month" BIGINT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "funding_line" TEXT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "ingested_at" TEXT,
    "event_id" TEXT,
    "type" TEXT,
    "team_size" TEXT,
    "targeting_principles" TEXT,
    "org_unit_id" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_events_0" FOREIGN KEY ("station_rsid") REFERENCES "stations" ("rsid")
);

CREATE TABLE "expenses" (
    "id" BIGINT,
    "project_id" TEXT,
    "event_id" BIGINT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "org_unit_id" BIGINT,
    "station_id" TEXT,
    "funding_line" TEXT,
    "category" TEXT,
    "amount" DOUBLE PRECISION DEFAULT 0,
    "spent_at" TEXT,
    "vendor" TEXT,
    "notes" TEXT,
    "created_at" TEXT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "station_rsid" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "updated_at" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "export_audit" (
    "id" BIGINT,
    "export_id" TEXT,
    "event" TEXT,
    "message" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "export_file" (
    "id" TEXT,
    "export_id" TEXT,
    "kind" TEXT,
    "format" TEXT,
    "filename" TEXT,
    "storage_path" TEXT,
    "size_bytes" BIGINT,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_export_file_0" FOREIGN KEY ("export_id") REFERENCES "export_job" ("id")
);

CREATE TABLE "export_job" (
    "id" TEXT,
    "requested_by" BIGINT,
    "status" TEXT,
    "source_page" TEXT,
    "dashboard_key" TEXT,
    "widget_key" TEXT,
    "query_key" TEXT,
    "scope_json" TEXT,
    "filters_json" TEXT,
    "render_json" TEXT,
    "format_json" TEXT,
    "error_summary" TEXT,
    "created_at" TEXT,
    "started_at" TEXT,
    "ended_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "external_census" (
    "id" BIGINT,
    "geography_code" TEXT,
    "attributes_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "external_social" (
    "id" BIGINT,
    "external_id" TEXT,
    "handle" TEXT,
    "signals_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_alrl" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "period_start" TEXT,
    "period_end" TEXT,
    "metric_name" TEXT,
    "metric_value" DOUBLE PRECISION,
    "source_system" TEXT,
    "ingest_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_alrl_outcomes" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "zip" TEXT,
    "category" TEXT,
    "value" DOUBLE PRECISION,
    "period_date" TEXT,
    "source_system" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_dep_loss" (
    "id" BIGINT,
    "station_rsid" TEXT NOT NULL,
    "time_period" TEXT NOT NULL,
    "cmpnt_cd" TEXT NOT NULL,
    "loss_bucket" TEXT NOT NULL,
    "dep_losses" BIGINT NOT NULL DEFAULT 0,
    "cancellation_rcm_number" TEXT,
    "source_primary_key" TEXT,
    "ingested_at" TEXT NOT NULL DEFAULT datetime('now'),
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_emm" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "period_start" TEXT,
    "period_end" TEXT,
    "metric_name" TEXT,
    "metric_value" DOUBLE PRECISION,
    "source_system" TEXT,
    "ingest_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_emm_activity" (
    "id" BIGINT,
    "activity_id" TEXT,
    "rsid" TEXT,
    "unit_name" TEXT,
    "mac" TEXT,
    "title" TEXT,
    "where_text" TEXT,
    "activity_type" TEXT,
    "activity_status" TEXT,
    "fy" BIGINT,
    "begin_date" TEXT,
    "end_date" TEXT,
    "aar_due" TEXT,
    "controlling_account" TEXT,
    "source_run_id" TEXT,
    "source_system" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_emm_events" (
    "event_id" TEXT,
    "unit_rsid" TEXT,
    "event_dt" TEXT,
    "event_type" TEXT,
    "mecs_requested" BIGINT,
    "mecs_assigned" BIGINT,
    "cost_event" DOUBLE PRECISION,
    "cost_marketing" DOUBLE PRECISION,
    "cost_travel" DOUBLE PRECISION,
    "leads" BIGINT,
    "contacts" BIGINT,
    "contracts" BIGINT,
    "source_system" TEXT,
    PRIMARY KEY ("event_id")
);

CREATE TABLE "fact_enlistments" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "echelon" TEXT,
    "period_date" TEXT,
    "contracts" BIGINT,
    "source_system" TEXT,
    "dataset_key" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_enlistments_bn" (
    "id" BIGINT,
    "as_of_date" TEXT,
    "bn_name" TEXT,
    "rsid" TEXT,
    "enlistments" BIGINT,
    "source_run_id" TEXT,
    "source_system" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_funnel" (
    "id" TEXT,
    "org_unit_id" TEXT NOT NULL,
    "date_key" TEXT NOT NULL,
    "lead_id" TEXT,
    "stage" TEXT NOT NULL,
    "event_type" TEXT,
    "count_value" DOUBLE PRECISION NOT NULL,
    "source_system" TEXT,
    "import_job_id" TEXT,
    "created_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "archived_at" TEXT,
    "keep_until" TEXT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "station_rsid" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "updated_at" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_lead_journey" (
    "lead_id" TEXT,
    "unit_rsid" TEXT,
    "created_dt" TEXT,
    "first_contact_dt" TEXT,
    "contract_dt" TEXT,
    "stage" TEXT,
    "source_channel" TEXT,
    "contract_flag" BIGINT,
    "hq_flag" BIGINT,
    "source_system" TEXT,
    PRIMARY KEY ("lead_id")
);

CREATE TABLE "fact_market_share_contracts" (
    "batch_id" TEXT,
    "fy" BIGINT,
    "per" TEXT,
    "comp" TEXT,
    "mkt" TEXT,
    "bde" TEXT,
    "bn" TEXT,
    "co" TEXT,
    "rsid" TEXT,
    "zip" TEXT,
    "contracts" DOUBLE PRECISION,
    "share" DOUBLE PRECISION,
    "totcontracts" DOUBLE PRECISION,
    "totpop" DOUBLE PRECISION,
    "imported_at" TEXT
);

CREATE TABLE "fact_marketing" (
    "id" TEXT,
    "org_unit_id" TEXT NOT NULL,
    "date_key" TEXT NOT NULL,
    "campaign" TEXT,
    "channel" TEXT,
    "impressions" DOUBLE PRECISION DEFAULT 0,
    "engagements" DOUBLE PRECISION DEFAULT 0,
    "clicks" DOUBLE PRECISION DEFAULT 0,
    "conversions" DOUBLE PRECISION DEFAULT 0,
    "cost" DOUBLE PRECISION DEFAULT 0,
    "source_system" TEXT,
    "import_job_id" TEXT,
    "created_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "archived_at" TEXT,
    "keep_until" TEXT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "station_rsid" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "updated_at" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_mission_category" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "period_start" TEXT,
    "period_end" TEXT,
    "mission_category" TEXT,
    "metric_name" TEXT,
    "metric_value" DOUBLE PRECISION,
    "source_system" TEXT,
    "ingest_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_production" (
    "id" TEXT,
    "org_unit_id" TEXT NOT NULL,
    "date_key" TEXT NOT NULL,
    "metric_key" TEXT NOT NULL,
    "metric_value" DOUBLE PRECISION NOT NULL,
    "source_system" TEXT,
    "import_job_id" TEXT,
    "created_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "archived_at" TEXT,
    "keep_until" TEXT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "station_rsid" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "updated_at" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_productivity" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "period_start" TEXT,
    "period_end" TEXT,
    "metric_name" TEXT,
    "metric_value" DOUBLE PRECISION,
    "recruiter_id" TEXT,
    "source_system" TEXT,
    "ingest_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_school_contacts" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "school_id" TEXT,
    "school_name" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip" TEXT,
    "contact_name" TEXT,
    "contact_type" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "source_system" TEXT,
    "ingest_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_school_contracts" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "school_id" TEXT,
    "school_name" TEXT,
    "contract_type" TEXT,
    "start_date" TEXT,
    "end_date" TEXT,
    "status" TEXT,
    "source_system" TEXT,
    "ingest_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fact_zip_potential" (
    "id" BIGINT,
    "zip" TEXT,
    "unit_rsid" TEXT,
    "cbsa_code" TEXT,
    "category" TEXT,
    "metric_name" TEXT,
    "metric_value" DOUBLE PRECISION,
    "source_system" TEXT,
    "ingest_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "feasibility_snapshot" (
    "id" BIGINT,
    "unit_rsid" TEXT NOT NULL,
    "fy" BIGINT NOT NULL,
    "generated_at" TEXT NOT NULL,
    "payload_json" TEXT NOT NULL,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_feasibility_snapshot_1" UNIQUE ("unit_rsid", "fy")
);

CREATE TABLE "fs_loss_event" (
    "id" VARCHAR NOT NULL,
    "unit_rsid" VARCHAR(4),
    "loss_code" VARCHAR NOT NULL,
    "description" TEXT,
    "reported_at" TIMESTAMP WITH TIME ZONE,
    "source_file" VARCHAR,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_fs_loss_event_0" FOREIGN KEY ("unit_rsid") REFERENCES "stations" ("rsid")
);

CREATE TABLE "fstsm_metric" (
    "id" BIGINT,
    "metric_key" TEXT,
    "value_real" DOUBLE PRECISION,
    "value_text" TEXT,
    "as_of_date" TEXT,
    "unit_rsid" TEXT,
    "source_import_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "funding_sources" (
    "id" BIGINT,
    "key" TEXT,
    "label" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_funding_sources_1" UNIQUE ("key")
);

CREATE TABLE "funnel_stages" (
    "id" VARCHAR NOT NULL,
    "stage_name" VARCHAR NOT NULL,
    "sequence_order" BIGINT NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "funnel_transitions" (
    "id" VARCHAR NOT NULL,
    "lead_key" VARCHAR NOT NULL,
    "station_rsid" VARCHAR(4) NOT NULL,
    "brigade_prefix" VARCHAR(1),
    "battalion_prefix" VARCHAR(2),
    "company_prefix" VARCHAR(3),
    "from_stage" VARCHAR,
    "to_stage" VARCHAR,
    "transition_reason" VARCHAR,
    "technician_user" VARCHAR,
    "transitioned_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "reported_at" TIMESTAMP WITH TIME ZONE,
    "ingested_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "lead_id" TEXT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "month" BIGINT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_funnel_transitions_0" FOREIGN KEY ("to_stage") REFERENCES "funnel_stages" ("id"),
    CONSTRAINT "fk_funnel_transitions_1" FOREIGN KEY ("from_stage") REFERENCES "funnel_stages" ("id"),
    CONSTRAINT "fk_funnel_transitions_2" FOREIGN KEY ("station_rsid") REFERENCES "stations" ("rsid")
);

CREATE TABLE "fusion_agenda_items" (
    "id" BIGINT,
    "fusion_id" TEXT NOT NULL,
    "title" TEXT,
    "description" TEXT,
    "order_idx" BIGINT DEFAULT 0,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fusion_evidence" (
    "id" BIGINT,
    "fusion_run_id" TEXT,
    "source_type" TEXT,
    "source_ref" TEXT,
    "payload_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fusion_findings" (
    "id" BIGINT,
    "fusion_id" TEXT NOT NULL,
    "finding_text" TEXT,
    "severity" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fusion_notes" (
    "id" BIGINT,
    "fusion_id" TEXT NOT NULL,
    "note_text" TEXT,
    "author" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fusion_process" (
    "id" BIGINT,
    "fusion_id" TEXT,
    "session_date" TEXT,
    "participants" TEXT,
    "insights" TEXT,
    "actions" TEXT,
    "status" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "fusion_recommendations" (
    "id" BIGINT,
    "fusion_run_id" TEXT,
    "unit_rsid" TEXT,
    "school_id" TEXT,
    "market_key" TEXT,
    "zip5" TEXT,
    "mission_pressure_score" DOUBLE PRECISION,
    "market_opportunity_score" DOUBLE PRECISION,
    "school_priority_score" DOUBLE PRECISION,
    "fusion_score" DOUBLE PRECISION,
    "recommendation_type" TEXT,
    "recommendation_text" TEXT,
    "evidence_json" TEXT,
    "as_of_date" TEXT,
    "created_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    "linked_to_twg" BIGINT DEFAULT 0,
    PRIMARY KEY ("id")
);

CREATE TABLE "fy_budget" (
    "id" BIGINT,
    "org_unit_id" BIGINT,
    "fy" BIGINT,
    "total_allocated" DOUBLE PRECISION DEFAULT 0,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "g2_market_metric" (
    "id" BIGINT,
    "metric_key" TEXT,
    "value_real" DOUBLE PRECISION,
    "value_text" TEXT,
    "as_of_date" TEXT,
    "cbsa_code" TEXT,
    "zip" TEXT,
    "unit_rsid" TEXT,
    "echelon" TEXT,
    "unit_display" TEXT,
    "source_import_run_id" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "geo_campaign_fact" (
    "id" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "rsid_prefix" TEXT,
    "campaign_id" TEXT,
    "campaign_name" TEXT,
    "geo_type" TEXT,
    "area_label" TEXT,
    "spend" DOUBLE PRECISION,
    "impressions" BIGINT,
    "engagements" BIGINT,
    "activations" BIGINT,
    "leads" BIGINT,
    "contracts" BIGINT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "geo_planning_container" (
    "id" TEXT,
    "fy" BIGINT NOT NULL,
    "qtr" TEXT NOT NULL,
    "rsid_prefix" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "geo_type" TEXT NOT NULL,
    "area_json" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "geo_target_zone_members" (
    "id" TEXT,
    "zone_id" TEXT NOT NULL,
    "member_type" TEXT,
    "member_value" TEXT,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "geo_target_zones" (
    "id" TEXT,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "zone_type" TEXT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "component" TEXT,
    "status" TEXT,
    "geometry_json" TEXT,
    "created_by" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "home_alerts" (
    "id" TEXT,
    "category" TEXT,
    "title" TEXT,
    "body" TEXT,
    "severity" TEXT,
    "source" TEXT,
    "effective_at" TEXT,
    "created_at" TEXT,
    "acked_at" TEXT,
    "acked_by" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "home_flash_items" (
    "id" TEXT,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "source" TEXT,
    "effective_date" TEXT,
    "created_at" TEXT NOT NULL,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "home_flashes" (
    "id" TEXT,
    "tab" TEXT,
    "source" TEXT,
    "title" TEXT,
    "summary" TEXT,
    "effective_at" TEXT,
    "url" TEXT,
    "created_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "home_messages" (
    "id" TEXT,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "priority" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "home_recognition" (
    "id" TEXT,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "person_name" TEXT,
    "unit" TEXT,
    "created_at" TEXT NOT NULL,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "home_reference_rails" (
    "id" TEXT,
    "title" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "target" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "home_references" (
    "id" TEXT,
    "key" TEXT,
    "label" TEXT,
    "type" TEXT,
    "path_or_url" TEXT,
    "available" BIGINT DEFAULT 0,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "home_upcoming" (
    "id" TEXT,
    "title" TEXT NOT NULL,
    "body" TEXT,
    "event_date" TEXT,
    "tag" TEXT,
    "created_at" TEXT NOT NULL,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_column_map" (
    "id" TEXT,
    "import_job_id" TEXT NOT NULL,
    "mapping_json" TEXT NOT NULL,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_error" (
    "id" TEXT,
    "import_job_id" TEXT NOT NULL,
    "row_index" BIGINT,
    "field" TEXT,
    "message" TEXT NOT NULL,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_file" (
    "id" BIGINT,
    "sha256" TEXT,
    "original_filename" TEXT,
    "stored_path" TEXT,
    "content_type" TEXT,
    "byte_size" BIGINT,
    "uploaded_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_import_file_1" UNIQUE ("sha256")
);

CREATE TABLE "import_job" (
    "id" BIGINT,
    "created_at" TEXT,
    "source_system" TEXT,
    "filename" TEXT,
    "file_hash" TEXT,
    "stored_path" TEXT,
    "status" TEXT,
    "preview_json" TEXT,
    "mapping_json" TEXT,
    "commit_result_json" TEXT,
    "row_count_detected" BIGINT DEFAULT 0,
    "filename_original" TEXT,
    "file_type" TEXT,
    "file_size_bytes" BIGINT,
    "sha256_hash" TEXT,
    "uploaded_by_user_id" TEXT,
    "uploaded_at" TEXT,
    "target_domain" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_job_preview" (
    "id" BIGINT,
    "import_job_id" TEXT NOT NULL,
    "preview_json" TEXT,
    "columns_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_job_v3" (
    "id" TEXT,
    "created_at" TEXT,
    "created_by" TEXT,
    "dataset_key" TEXT NOT NULL,
    "source_system" TEXT,
    "filename" TEXT,
    "file_sha256" TEXT,
    "status" TEXT DEFAULT 'uploaded',
    "row_count" BIGINT DEFAULT 0,
    "error_count" BIGINT DEFAULT 0,
    "updated_at" TEXT,
    "notes" TEXT,
    "scope_org_unit_id" TEXT,
    "completed_at" TEXT,
    "summary_json" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_mapping_template" (
    "id" BIGINT,
    "name" TEXT NOT NULL,
    "target_domain" TEXT,
    "mapping_json" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_row_error" (
    "id" BIGINT,
    "import_run_id" BIGINT,
    "row_number" BIGINT,
    "severity" TEXT,
    "message" TEXT,
    "raw_row_json" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_run" (
    "id" BIGINT,
    "import_file_id" BIGINT,
    "source_system" TEXT,
    "dataset_key" TEXT,
    "status" TEXT,
    "started_at" TEXT,
    "finished_at" TEXT,
    "rows_in" BIGINT DEFAULT 0,
    "rows_inserted" BIGINT DEFAULT 0,
    "rows_updated" BIGINT DEFAULT 0,
    "rows_rejected" BIGINT DEFAULT 0,
    "warnings_json" TEXT,
    "errors_json" TEXT,
    "detected_signature_json" TEXT,
    "dry_run" BIGINT DEFAULT 0,
    "initiated_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_run_error_v2" (
    "id" BIGINT,
    "run_id" TEXT,
    "row_num" BIGINT,
    "column_name" TEXT,
    "error_code" TEXT,
    "message" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "import_run_v2" (
    "run_id" TEXT,
    "dataset_key" TEXT,
    "filename" TEXT,
    "uploaded_by" TEXT,
    "status" TEXT,
    "detected_confidence" DOUBLE PRECISION,
    "rows_in" BIGINT,
    "rows_loaded" BIGINT,
    "warnings" BIGINT DEFAULT 0,
    "error_summary" TEXT,
    "storage_path" TEXT,
    "created_at" TEXT,
    "started_at" TEXT,
    "ended_at" TEXT,
    "scope_unit_rsid" TEXT,
    "scope_fy" BIGINT,
    "scope_qtr" BIGINT,
    PRIMARY KEY ("run_id")
);

CREATE TABLE "imported_rows" (
    "id" BIGINT,
    "import_job_id" BIGINT,
    "target_domain" TEXT,
    "row_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "ingest_file" (
    "id" BIGINT,
    "source_system" TEXT,
    "original_filename" TEXT,
    "stored_path" TEXT,
    "file_hash" TEXT,
    "uploaded_by" TEXT,
    "uploaded_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "ingest_row_error" (
    "id" BIGINT,
    "ingest_run_id" BIGINT,
    "row_number" BIGINT,
    "error_code" TEXT,
    "error_message" TEXT,
    "row_json" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "ingest_run" (
    "id" BIGINT,
    "ingest_file_id" BIGINT,
    "importer_id" TEXT,
    "started_at" TEXT,
    "finished_at" TEXT,
    "status" TEXT,
    "row_count_in" BIGINT DEFAULT 0,
    "row_count_loaded" BIGINT DEFAULT 0,
    "errors_json" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "ingest_runs" (
    "id" BIGINT NOT NULL,
    "file_id" BIGINT,
    "recipe_id" BIGINT,
    "status" VARCHAR,
    "report" JSONB,
    "run_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_ingest_runs_0" FOREIGN KEY ("recipe_id") REFERENCES "transform_recipes" ("id"),
    CONSTRAINT "fk_ingest_runs_1" FOREIGN KEY ("file_id") REFERENCES "ingested_files" ("id")
);

CREATE TABLE "ingested_files" (
    "id" BIGINT NOT NULL,
    "filename" VARCHAR NOT NULL,
    "source" VARCHAR,
    "uploaded_by" VARCHAR,
    "uploaded_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "invite_token" (
    "token" TEXT,
    "user_id" BIGINT,
    "email" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "used_at" TEXT,
    "expires_at" TEXT,
    PRIMARY KEY ("token")
);

CREATE TABLE "lead_journey_fact" (
    "lead_id" TEXT,
    "person_key" TEXT,
    "unit_rsid" TEXT,
    "source_type" TEXT,
    "source_detail" TEXT,
    "event_id" TEXT,
    "mac_id" TEXT,
    "lead_created_dt" TEXT,
    "contact_made_dt" TEXT,
    "appointment_dt" TEXT,
    "applicant_dt" TEXT,
    "contract_dt" TEXT,
    "contract_flag" BIGINT DEFAULT 0,
    "contract_type" TEXT,
    "mos" TEXT,
    "afqt_tier" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("lead_id")
);

CREATE TABLE "leads" (
    "lead_id" TEXT,
    "first_name" TEXT,
    "last_name" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "source" TEXT,
    "age" BIGINT,
    "education_level" TEXT,
    "cbsa_code" TEXT,
    "campaign_source" TEXT,
    "school_id" TEXT,
    "zip5" TEXT,
    "created_at" TEXT,
    "notes" TEXT,
    PRIMARY KEY ("lead_id")
);

CREATE TABLE "lms_courses" (
    "course_id" TEXT,
    "title" TEXT,
    "description" TEXT,
    "created_at" TEXT,
    "roles" TEXT,
    "workflow" TEXT,
    PRIMARY KEY ("course_id")
);

CREATE TABLE "lms_enrollments" (
    "enrollment_id" TEXT,
    "user_id" TEXT,
    "course_id" TEXT,
    "progress_percent" BIGINT DEFAULT 0,
    "enrolled_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("enrollment_id")
);

CREATE TABLE "loe" (
    "id" BIGINT,
    "org_unit_id" BIGINT,
    "fy" TEXT,
    "qtr" TEXT,
    "name" TEXT,
    "description" TEXT,
    "created_at" TEXT,
    "status" TEXT,
    "progress" DOUBLE PRECISION,
    "archived" BIGINT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "loe_metrics" (
    "id" VARCHAR NOT NULL,
    "loe_id" VARCHAR NOT NULL,
    "metric_name" VARCHAR NOT NULL,
    "target_value" DOUBLE PRECISION,
    "warn_threshold" DOUBLE PRECISION,
    "fail_threshold" DOUBLE PRECISION,
    "reported_at" TIMESTAMP WITH TIME ZONE,
    "ingested_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "current_value" DOUBLE PRECISION,
    "status" VARCHAR,
    "rationale" VARCHAR,
    "last_evaluated_at" TIMESTAMP WITH TIME ZONE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_loe_metrics_0" FOREIGN KEY ("loe_id") REFERENCES "loes" ("id")
);

CREATE TABLE "loes" (
    "id" VARCHAR NOT NULL,
    "scope_type" VARCHAR NOT NULL,
    "scope_value" VARCHAR NOT NULL,
    "title" VARCHAR NOT NULL,
    "description" TEXT,
    "created_by" VARCHAR NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);

CREATE TABLE "maintenance_flags" (
    "id" TEXT,
    "active" BIGINT NOT NULL DEFAULT 0,
    "message" TEXT,
    "starts_at" TEXT,
    "ends_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "maintenance_runs" (
    "id" BIGINT,
    "schedule_id" BIGINT,
    "run_type" TEXT,
    "params_json" TEXT,
    "result_json" TEXT,
    "started_at" TEXT,
    "finished_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "maintenance_schedules" (
    "id" BIGINT,
    "name" TEXT,
    "enabled" BIGINT DEFAULT 0,
    "interval_minutes" BIGINT,
    "last_run_at" TEXT,
    "next_run_at" TEXT,
    "params_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_capacity" (
    "id" BIGINT,
    "unit_rsid" TEXT NOT NULL,
    "fy" BIGINT NOT NULL,
    "baseline_contract_capacity" BIGINT NOT NULL,
    "market_burden_factor" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    "notes" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_market_capacity_1" UNIQUE ("unit_rsid", "fy")
);

CREATE TABLE "market_category_rule" (
    "id" TEXT,
    "name" TEXT,
    "description" TEXT,
    "rule_json" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_category_weights" (
    "id" BIGINT NOT NULL,
    "category" VARCHAR(3) NOT NULL,
    "weight" BIGINT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_market_category_weights_1" UNIQUE ("category")
);

CREATE TABLE "market_cbsa_fact" (
    "id" TEXT,
    "as_of_date" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "month" BIGINT,
    "component" TEXT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "rsid_prefix" TEXT,
    "cbsa_code" TEXT,
    "cbsa_name" TEXT,
    "dma_name" TEXT,
    "plot_parameter" TEXT,
    "value" DOUBLE PRECISION,
    "p2p" DOUBLE PRECISION,
    "market_category" TEXT,
    "created_at" TEXT,
    "ingested_at" TEXT,
    "youth_pop_17_24" BIGINT,
    "market_potential" BIGINT,
    "army_share_pct" DOUBLE PRECISION,
    "contracts_total" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_cbsa_metrics" (
    "id" TEXT,
    "as_of_date" TEXT,
    "component" TEXT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "cbsa_code" TEXT,
    "cbsa_name" TEXT,
    "plot_parameter" TEXT,
    "segment_code" TEXT,
    "total_population" BIGINT,
    "total_potential" BIGINT,
    "potential_remaining" BIGINT,
    "contracts_total" BIGINT,
    "army_share_of_potential" DOUBLE PRECISION,
    "p2p_band" TEXT,
    "p2p_value" DOUBLE PRECISION,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_demographics" (
    "id" TEXT,
    "as_of_date" TEXT,
    "component" TEXT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "geo_level" TEXT,
    "geo_value" TEXT,
    "race_ethnicity" TEXT,
    "gender" TEXT,
    "fqma_population" BIGINT,
    "youth_population" BIGINT,
    "enlistments" BIGINT,
    "p2p_value" DOUBLE PRECISION,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_demographics_fact" (
    "id" TEXT,
    "as_of_date" TEXT,
    "fy" BIGINT,
    "component" TEXT,
    "geo_type" TEXT,
    "geo_id" TEXT,
    "race_ethnicity" TEXT,
    "gender" TEXT,
    "population_type" TEXT,
    "population_value" DOUBLE PRECISION,
    "production_value" DOUBLE PRECISION,
    "p2p" DOUBLE PRECISION,
    "created_at" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_geotarget_zone" (
    "id" TEXT,
    "name" TEXT,
    "zone_type" TEXT,
    "rsid_prefix" TEXT,
    "component" TEXT,
    "market_category" TEXT,
    "targeted" BIGINT DEFAULT 0,
    "geojson" TEXT,
    "zip_list" TEXT,
    "cbsa_list" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_health_evidence" (
    "id" BIGINT,
    "compute_run_id" TEXT,
    "market_type" TEXT,
    "market_id" TEXT,
    "evidence_type" TEXT,
    "description" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_health_scores" (
    "id" BIGINT,
    "compute_run_id" TEXT,
    "market_type" TEXT,
    "market_id" TEXT,
    "unit_rsid" TEXT,
    "as_of_date" TEXT,
    "supportability_score" DOUBLE PRECISION,
    "confidence_score" DOUBLE PRECISION,
    "burden_index" DOUBLE PRECISION,
    "risk_penalty" DOUBLE PRECISION,
    "historical_trend" DOUBLE PRECISION,
    "recruiter_ratio" DOUBLE PRECISION,
    "market_load" DOUBLE PRECISION,
    "activity_signal" DOUBLE PRECISION,
    "demographic_signal" DOUBLE PRECISION,
    "penetration_signal" DOUBLE PRECISION,
    "market_size_index" DOUBLE PRECISION,
    "components_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_rules" (
    "key" TEXT,
    "value" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("key")
);

CREATE TABLE "market_sama_zip_fact" (
    "id" TEXT,
    "as_of_date" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "month" BIGINT,
    "component" TEXT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "rsid_prefix" TEXT,
    "station_rsid" TEXT,
    "zip_code" TEXT,
    "zip_category" TEXT,
    "targeted" BIGINT DEFAULT 0,
    "army_potential" BIGINT,
    "dod_potential" BIGINT,
    "dod_wtd_avg" DOUBLE PRECISION,
    "army_share_of_potential" DOUBLE PRECISION,
    "army_ga_ach" BIGINT,
    "army_sa_ach" BIGINT,
    "army_vol_ach" BIGINT,
    "contracts" BIGINT,
    "potential_remaining" BIGINT,
    "p2p" DOUBLE PRECISION,
    "created_at" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_target_list" (
    "id" TEXT,
    "fy" BIGINT NOT NULL,
    "qtr" TEXT NOT NULL,
    "rsid_prefix" TEXT NOT NULL,
    "target_type" TEXT NOT NULL,
    "zip5" TEXT,
    "cbsa_code" TEXT,
    "rationale" TEXT,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_targets" (
    "id" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "rsid_prefix" TEXT,
    "target_type" TEXT,
    "zip" TEXT,
    "cbsa_code" TEXT,
    "rationale" TEXT,
    "score" DOUBLE PRECISION,
    "created_at" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_taxonomy" (
    "id" TEXT,
    "key" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "description" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_zip_fact" (
    "id" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "month" BIGINT,
    "rsid_prefix" TEXT,
    "zip5" TEXT,
    "cbsa_code" TEXT,
    "market_category" TEXT,
    "youth_pop" BIGINT,
    "fqma" BIGINT,
    "army_accessions" BIGINT,
    "army_share" DOUBLE PRECISION,
    "potential_remaining" BIGINT,
    "p2p" DOUBLE PRECISION,
    "must_keep" BIGINT DEFAULT 0,
    "must_win" BIGINT DEFAULT 0,
    "market_of_opportunity" BIGINT DEFAULT 0,
    "supplemental_market" BIGINT DEFAULT 0,
    "ingested_at" TEXT,
    "youth_pop_17_24" BIGINT,
    "market_potential" BIGINT,
    "army_share_pct" DOUBLE PRECISION,
    "contracts_total" BIGINT,
    "leads_total" BIGINT,
    "activations_total" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "market_zip_metrics" (
    "id" TEXT,
    "as_of_date" TEXT,
    "component" TEXT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "station_rsid" TEXT,
    "zip" TEXT,
    "zip_category" TEXT,
    "cbsa_code" TEXT,
    "dma_name" TEXT,
    "army_potential" BIGINT,
    "dod_potential" BIGINT,
    "dod_wtd_avg" BIGINT,
    "army_share_of_potential" DOUBLE PRECISION,
    "contracts_ga" BIGINT,
    "contracts_sa" BIGINT,
    "contracts_vol" BIGINT,
    "potential_remaining" BIGINT,
    "p2p_band" TEXT,
    "p2p_value" DOUBLE PRECISION,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "marketing_activities" (
    "id" BIGINT,
    "activity_id" TEXT,
    "event_id" TEXT,
    "activity_type" TEXT,
    "campaign_name" TEXT,
    "channel" TEXT,
    "data_source" TEXT,
    "impressions" BIGINT DEFAULT 0,
    "engagement_count" BIGINT DEFAULT 0,
    "clicks" BIGINT DEFAULT 0,
    "awareness_metric" DOUBLE PRECISION,
    "activation_conversions" BIGINT,
    "reporting_date" TEXT,
    "metadata" TEXT,
    "cost" DOUBLE PRECISION DEFAULT 0,
    "created_at" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "keep_until" TEXT,
    "archived_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "meeting_minutes" (
    "minute_id" TEXT,
    "project_id" TEXT,
    "occurred_at" TEXT,
    "summary" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "keep_until" TEXT,
    "archived_at" TEXT,
    PRIMARY KEY ("minute_id")
);

CREATE TABLE "mi_cbsa_fact" (
    "id" TEXT,
    "fy" TEXT,
    "qtr" TEXT,
    "component" TEXT,
    "rsid_prefix" TEXT,
    "cbsa_code" TEXT,
    "cbsa_name" TEXT,
    "market_category" TEXT,
    "army_potential" DOUBLE PRECISION,
    "dod_potential" DOUBLE PRECISION,
    "army_share_of_potential" DOUBLE PRECISION,
    "potential_remaining" DOUBLE PRECISION,
    "contracts_ga" BIGINT,
    "contracts_sa" BIGINT,
    "contracts_vol" BIGINT,
    "p2p" DOUBLE PRECISION,
    "as_of_date" TEXT,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "mi_dataset_registry" (
    "dataset_key" TEXT,
    "display_name" TEXT NOT NULL,
    "table_name" TEXT NOT NULL,
    "required_columns_json" TEXT NOT NULL,
    "optional_columns_json" TEXT NOT NULL,
    "last_seen_at" TEXT,
    PRIMARY KEY ("dataset_key")
);

CREATE TABLE "mi_demo_fact" (
    "id" TEXT,
    "fy" BIGINT,
    "component" TEXT,
    "geo_type" TEXT,
    "geo_id" TEXT,
    "attribute_key" TEXT,
    "attribute_value" DOUBLE PRECISION,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mi_enlistments_bde" (
    "id" TEXT,
    "bde" TEXT,
    "enlistments" BIGINT,
    "fy" TEXT,
    "as_of_date" TEXT,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "mi_enlistments_bn" (
    "id" TEXT,
    "battalion_name" TEXT,
    "rsid_prefix" TEXT,
    "enlistments" BIGINT,
    "fy" TEXT,
    "as_of_date" TEXT,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "mi_import_template" (
    "template_key" TEXT,
    "dataset_key" TEXT NOT NULL,
    "description" TEXT,
    "columns_json" TEXT NOT NULL,
    "mapping_hints_json" TEXT NOT NULL,
    "validation_rules_json" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    PRIMARY KEY ("template_key")
);

CREATE TABLE "mi_mission_category_ref" (
    "id" TEXT,
    "mission_category" TEXT,
    "education_tier" TEXT,
    "pct_gt_enlistments" DOUBLE PRECISION,
    "pct_enlistments" DOUBLE PRECISION,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "mi_school_fact" (
    "id" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "rsid_prefix" TEXT,
    "school_id" TEXT,
    "school_name" TEXT,
    "enrollment" BIGINT,
    "fqma_est" BIGINT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mi_zip_fact" (
    "id" TEXT,
    "fy" TEXT,
    "qtr" TEXT,
    "component" TEXT,
    "rsid_prefix" TEXT,
    "zip5" TEXT,
    "station_name" TEXT,
    "market_category" TEXT,
    "army_potential" DOUBLE PRECISION,
    "dod_potential" DOUBLE PRECISION,
    "army_share_of_potential" DOUBLE PRECISION,
    "potential_remaining" DOUBLE PRECISION,
    "contracts_ga" BIGINT,
    "contracts_sa" BIGINT,
    "contracts_vol" BIGINT,
    "p2p" DOUBLE PRECISION,
    "as_of_date" TEXT,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_allocation_company_scores" (
    "id" BIGINT,
    "run_id" TEXT,
    "company_id" TEXT,
    "supportability_score" DOUBLE PRECISION,
    "risk_score" DOUBLE PRECISION,
    "confidence_score" DOUBLE PRECISION,
    "score_payload" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_allocation_evidence" (
    "id" BIGINT,
    "run_id" TEXT,
    "company_id" TEXT,
    "evidence_type" TEXT,
    "evidence_uri" TEXT,
    "description" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_allocation_inputs" (
    "id" BIGINT,
    "run_id" TEXT,
    "company_id" TEXT,
    "recruiter_capacity" BIGINT,
    "historical_production" BIGINT,
    "funnel_health" DOUBLE PRECISION,
    "dep_loss" BIGINT,
    "school_access" DOUBLE PRECISION,
    "school_population" BIGINT,
    "ascope" TEXT,
    "pmesii" TEXT,
    "market_intel" TEXT,
    "extra_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_allocation_recommendations" (
    "id" BIGINT,
    "run_id" TEXT,
    "company_id" TEXT,
    "recommended_mission" BIGINT,
    "rationale" TEXT,
    "confidence" DOUBLE PRECISION,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_allocation_runs" (
    "run_id" TEXT,
    "unit_rsid" TEXT,
    "mission_total" BIGINT,
    "status" TEXT DEFAULT 'created',
    "notes" TEXT,
    "approved_allocation" BIGINT,
    "decision_status" TEXT,
    "decision_notes" TEXT,
    "approved_by" TEXT,
    "approved_at" TEXT,
    "created_at" TEXT,
    "started_at" TEXT,
    "completed_at" TEXT,
    PRIMARY KEY ("run_id")
);

CREATE TABLE "mission_assessments" (
    "id" TEXT,
    "period_type" TEXT,
    "period_value" TEXT,
    "scope" TEXT,
    "metrics_json" TEXT,
    "narrative" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_feasibility_narrative" (
    "id" BIGINT,
    "unit_rsid" TEXT,
    "fy" BIGINT,
    "payload" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_risk_evidence" (
    "id" BIGINT,
    "compute_run_id" TEXT,
    "unit_rsid" TEXT,
    "company_id" TEXT,
    "source_key" TEXT,
    "source_run_id" TEXT,
    "notes" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_risk_scores" (
    "id" BIGINT,
    "compute_run_id" TEXT,
    "unit_rsid" TEXT,
    "company_id" TEXT,
    "market_type" TEXT,
    "market_id" TEXT,
    "as_of_date" TEXT,
    "mission_risk_score" DOUBLE PRECISION,
    "risk_level" TEXT,
    "confidence_score" DOUBLE PRECISION,
    "components_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "mission_target" (
    "id" BIGINT,
    "unit_rsid" TEXT NOT NULL,
    "fy" BIGINT NOT NULL,
    "annual_contract_mission" BIGINT NOT NULL,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_mission_target_1" UNIQUE ("unit_rsid", "fy")
);

CREATE TABLE "module_registry" (
    "id" TEXT,
    "module_key" TEXT NOT NULL,
    "display_name" TEXT NOT NULL,
    "owner_role" TEXT,
    "description" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_module_registry_2" UNIQUE ("module_key")
);

CREATE TABLE "org_unit" (
    "id" BIGINT,
    "name" TEXT NOT NULL,
    "type" TEXT,
    "parent_id" BIGINT,
    "uic" TEXT,
    "rsid" TEXT,
    "location_city" TEXT,
    "location_state" TEXT,
    "location_zip" TEXT,
    "cbsa" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "outcome_records" (
    "id" BIGINT,
    "recommendation_table" TEXT,
    "recommendation_id" BIGINT,
    "decision_id" BIGINT,
    "outcome_type" TEXT,
    "outcome_value" TEXT,
    "observed_at" TEXT,
    "notes" TEXT,
    "created_at" TEXT DEFAULT datetime('now'),
    PRIMARY KEY ("id")
);

CREATE TABLE "outcomes" (
    "id" BIGINT,
    "lead_id" TEXT,
    "contract_date" TEXT,
    "ship_date" TEXT,
    "status" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "permission" (
    "key" TEXT,
    "description" TEXT,
    "category" TEXT,
    "display_name" TEXT,
    "permission_key" TEXT,
    PRIMARY KEY ("key")
);

CREATE TABLE "phonetic_dataset_registry" (
    "dataset_key" TEXT,
    "as_of" TEXT,
    "row_count" BIGINT DEFAULT 0,
    "last_loaded_at" TEXT,
    "status" TEXT,
    PRIMARY KEY ("dataset_key")
);

CREATE TABLE "phonetic_map" (
    "id" TEXT,
    "term" TEXT NOT NULL,
    "phonetic" TEXT NOT NULL,
    "type" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "priority_loe" (
    "id" BIGINT,
    "priority_id" BIGINT NOT NULL,
    "loe_id" TEXT NOT NULL,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_priority_loe_1" UNIQUE ("priority_id", "loe_id")
);

CREATE TABLE "processing_metrics" (
    "id" TEXT,
    "fy" BIGINT,
    "qtr" BIGINT,
    "month" BIGINT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "metric_key" TEXT,
    "metric_label" TEXT,
    "value" DOUBLE PRECISION,
    "unit" TEXT,
    "reported_at" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "project" (
    "id" BIGINT,
    "org_unit_id" BIGINT,
    "loe_id" TEXT,
    "event_id" TEXT,
    "name" TEXT,
    "description" TEXT,
    "status" TEXT,
    "start_dt" TEXT,
    "end_dt" TEXT,
    "roi_target" DOUBLE PRECISION,
    "created_at" TEXT,
    "updated_at" TEXT,
    "record_status" TEXT DEFAULT 'active',
    PRIMARY KEY ("id")
);

CREATE TABLE "project_event_link" (
    "id" BIGINT,
    "project_id" TEXT NOT NULL,
    "event_id" BIGINT NOT NULL,
    "org_unit_id" BIGINT,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_project_event_link_1" UNIQUE ("project_id", "event_id")
);

CREATE TABLE "projects" (
    "project_id" TEXT,
    "title" TEXT,
    "description" TEXT,
    "owner" TEXT,
    "status" TEXT,
    "percent_complete" DOUBLE PRECISION DEFAULT 0,
    "created_at" TEXT,
    "updated_at" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "planned_cost" DOUBLE PRECISION DEFAULT 0,
    "actual_cost" DOUBLE PRECISION DEFAULT 0,
    "fy" BIGINT,
    "qtr" BIGINT,
    "month" BIGINT,
    "echelon_type" TEXT,
    "unit_value" TEXT,
    "funding_line" TEXT,
    "keep_until" TEXT,
    "archived_at" TEXT,
    "org_unit_id" BIGINT,
    "station_id" TEXT,
    "category" TEXT,
    "start_date" TEXT,
    "end_date" TEXT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "station_rsid" TEXT,
    "reported_at" TEXT,
    "reporting_date" TEXT,
    "ingested_at" TEXT,
    PRIMARY KEY ("project_id")
);

CREATE TABLE "raw_file_storage" (
    "id" BIGINT,
    "run_id" TEXT,
    "original_filename" TEXT,
    "storage_path" TEXT,
    "content_type" TEXT,
    "size_bytes" BIGINT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "recommendation_explanations" (
    "id" BIGINT,
    "recommendation_table" TEXT,
    "recommendation_id" BIGINT,
    "explanation" TEXT,
    "doctrine_summary" TEXT,
    "doctrine_refs_json" TEXT,
    "created_at" TEXT DEFAULT datetime('now'),
    PRIMARY KEY ("id")
);

CREATE TABLE "recruiter_strength" (
    "id" BIGINT,
    "unit_rsid" TEXT NOT NULL,
    "month" TEXT NOT NULL,
    "recruiters_assigned" BIGINT NOT NULL,
    "recruiters_available" BIGINT NOT NULL,
    "created_at" TEXT,
    "updated_at" TEXT,
    "fy" BIGINT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_recruiter_strength_1" UNIQUE ("unit_rsid", "month")
);

CREATE TABLE "refresh_dataset_rows" (
    "id" BIGINT NOT NULL,
    "source_id" BIGINT,
    "version_id" BIGINT,
    "row_json" JSONB,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_refresh_dataset_rows_0" FOREIGN KEY ("version_id") REFERENCES "dataset_versions" ("id"),
    CONSTRAINT "fk_refresh_dataset_rows_1" FOREIGN KEY ("source_id") REFERENCES "refresh_sources" ("id")
);

CREATE TABLE "refresh_history" (
    "id" BIGINT NOT NULL,
    "job_id" BIGINT,
    "version_id" BIGINT,
    "mode" VARCHAR,
    "status" VARCHAR,
    "applied_by" VARCHAR,
    "applied_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "row_count_before" BIGINT,
    "row_count_after" BIGINT,
    "notes" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_refresh_history_0" FOREIGN KEY ("version_id") REFERENCES "dataset_versions" ("id"),
    CONSTRAINT "fk_refresh_history_1" FOREIGN KEY ("job_id") REFERENCES "refresh_jobs" ("id")
);

CREATE TABLE "refresh_jobs" (
    "id" BIGINT NOT NULL,
    "source_id" BIGINT,
    "filename" VARCHAR NOT NULL,
    "stored_path" VARCHAR NOT NULL,
    "checksum" VARCHAR,
    "uploaded_by" VARCHAR,
    "uploaded_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR,
    "row_count" BIGINT,
    "profile" JSONB,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_refresh_jobs_0" FOREIGN KEY ("source_id") REFERENCES "refresh_sources" ("id")
);

CREATE TABLE "refresh_sources" (
    "id" BIGINT NOT NULL,
    "name" VARCHAR NOT NULL,
    "description" TEXT,
    "canonical_target" VARCHAR,
    "file_types" VARCHAR,
    "required_merge_keys" JSONB,
    "mapping_profile" JSONB,
    "owner" VARCHAR,
    "default_mode" VARCHAR,
    "trusted" VARCHAR,
    "auto_commit" VARCHAR,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_refresh_sources_1" UNIQUE ("name")
);

CREATE TABLE "refresh_staging_rows" (
    "id" BIGINT NOT NULL,
    "job_id" BIGINT,
    "row_number" BIGINT,
    "row_json" JSONB,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_refresh_staging_rows_0" FOREIGN KEY ("job_id") REFERENCES "refresh_jobs" ("id")
);

CREATE TABLE "regulatory_references" (
    "id" TEXT,
    "code" TEXT,
    "title" TEXT,
    "description" TEXT,
    "category" TEXT,
    "authority_level" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "regulatory_traceability" (
    "id" TEXT,
    "reference_id" TEXT NOT NULL,
    "module_key" TEXT NOT NULL,
    "page_route" TEXT,
    "metric_key" TEXT,
    "decision_supported" TEXT,
    "tor_enclosure" TEXT,
    "notes" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "release_notes" (
    "id" BIGINT,
    "title" TEXT,
    "body" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "resource_link" (
    "id" BIGINT,
    "section" TEXT,
    "title" TEXT,
    "url" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "roi_thresholds" (
    "metric_key" TEXT,
    "value" DOUBLE PRECISION,
    PRIMARY KEY ("metric_key")
);

CREATE TABLE "role" (
    "role_key" TEXT,
    "display_name" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("role_key")
);

CREATE TABLE "role_permission" (
    "role_key" TEXT,
    "permission_key" TEXT,
    "granted" BIGINT DEFAULT 1,
    PRIMARY KEY ("role_key", "permission_key"),
    CONSTRAINT "fk_role_permission_0" FOREIGN KEY ("permission_key") REFERENCES "permission" ("key"),
    CONSTRAINT "fk_role_permission_1" FOREIGN KEY ("role_key") REFERENCES "role" ("role_key")
);

CREATE TABLE "role_template" (
    "key" TEXT,
    "name" TEXT,
    "description" TEXT,
    PRIMARY KEY ("key")
);

CREATE TABLE "role_template_permission" (
    "id" BIGINT,
    "role_key" TEXT,
    "permission_key" TEXT,
    "granted" BIGINT DEFAULT 1,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_role_template_permission_0" FOREIGN KEY ("permission_key") REFERENCES "permission" ("key"),
    CONSTRAINT "fk_role_template_permission_1" FOREIGN KEY ("role_key") REFERENCES "role_template" ("key")
);

CREATE TABLE "roles" (
    "id" BIGINT,
    "name" TEXT,
    "description" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_roles_1" UNIQUE ("name")
);

CREATE TABLE "school_accounts" (
    "id" TEXT,
    "school_id" TEXT,
    "assigned_station_rsid" TEXT,
    "assigned_company_prefix" TEXT,
    "assigned_battalion_prefix" TEXT,
    "assigned_brigade_prefix" TEXT,
    "last_contacted_at" TEXT,
    "status" TEXT,
    "notes" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "school_activities" (
    "id" TEXT,
    "school_id" TEXT,
    "station_rsid" TEXT,
    "activity_type" TEXT,
    "activity_date" TEXT,
    "outcome" TEXT,
    "notes" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "school_contacts" (
    "id" TEXT,
    "school_id" TEXT,
    "contact_name" TEXT,
    "contact_role" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "school_fact" (
    "id" TEXT,
    "fy" BIGINT,
    "qtr" TEXT,
    "rsid_prefix" TEXT,
    "school_id" TEXT,
    "school_name" TEXT,
    "school_type" TEXT,
    "enrollment" BIGINT,
    "fqma_est" BIGINT,
    "access_level" TEXT,
    "last_visit_at" TEXT,
    "visits_ytd" BIGINT,
    "engagements_ytd" BIGINT,
    "leads_ytd" BIGINT,
    "contracts_ytd" BIGINT,
    "ingested_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "school_milestones" (
    "id" TEXT,
    "school_id" TEXT,
    "milestone_type" TEXT,
    "milestone_date" TEXT,
    "linked_event_id" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "school_program_fact" (
    "id" TEXT,
    "bde" TEXT,
    "bn" TEXT,
    "co" TEXT,
    "rsid_prefix" TEXT,
    "population" BIGINT,
    "available" BIGINT,
    "attempted_students" BIGINT,
    "attempted_students_pct" DOUBLE PRECISION,
    "contacted_students" BIGINT,
    "contacted_students_pct" DOUBLE PRECISION,
    "fy" TEXT,
    "qtr" TEXT,
    "as_of_date" TEXT,
    "ingested_at" TEXT NOT NULL,
    PRIMARY KEY ("id")
);

CREATE TABLE "school_program_leads" (
    "id" TEXT,
    "lead_id" TEXT,
    "school_id" TEXT,
    "source_tag" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "school_zone_assignments" (
    "id" BIGINT,
    "school_id" TEXT NOT NULL,
    "zone_id" TEXT NOT NULL,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_school_zone_assignments_1" UNIQUE ("school_id", "zone_id")
);

CREATE TABLE "schools" (
    "id" TEXT,
    "school_name" TEXT,
    "school_type" TEXT,
    "district" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip_code" TEXT,
    "latitude" DOUBLE PRECISION,
    "longitude" DOUBLE PRECISION,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "security_roles" (
    "id" TEXT,
    "name" TEXT,
    "description" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_security_roles_2" UNIQUE ("name")
);

CREATE TABLE "spend_fact" (
    "spend_id" TEXT,
    "unit_rsid" TEXT,
    "event_id" TEXT,
    "spend_type" TEXT,
    "amount" DOUBLE PRECISION,
    "spend_dt" TEXT,
    "notes" TEXT,
    PRIMARY KEY ("spend_id")
);

CREATE TABLE "staging_uploads" (
    "id" BIGINT,
    "dataset_key" TEXT,
    "source_name" TEXT,
    "uploaded_at" TEXT,
    "raw_json" TEXT,
    "validated" BIGINT DEFAULT 0,
    PRIMARY KEY ("id")
);

CREATE TABLE "station_zip_coverage" (
    "id" BIGINT NOT NULL,
    "station_rsid" VARCHAR(4) NOT NULL,
    "zip_code" VARCHAR(5) NOT NULL,
    "market_category" VARCHAR(3) NOT NULL DEFAULT 'UNK',
    "source_file" VARCHAR,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_station_zip_coverage_1" UNIQUE ("station_rsid", "zip_code"),
    CONSTRAINT "fk_station_zip_coverage_0" FOREIGN KEY ("station_rsid") REFERENCES "stations" ("rsid")
);

CREATE TABLE "stations" (
    "id" BIGINT NOT NULL,
    "rsid" VARCHAR(4) NOT NULL,
    "display" VARCHAR,
    "company_id" BIGINT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_stations_1" UNIQUE ("rsid"),
    CONSTRAINT "fk_stations_0" FOREIGN KEY ("company_id") REFERENCES "companies" ("id")
);

CREATE TABLE "stg_raw_dataset" (
    "id" BIGINT,
    "ingest_run_id" BIGINT,
    "row_number" BIGINT,
    "row_json" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "stg_raw_dataset_profile" (
    "id" BIGINT,
    "ingest_file_id" BIGINT,
    "columns_json" TEXT,
    "sample_json" TEXT,
    "detected_source_hint" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "surveys" (
    "id" BIGINT,
    "survey_id" TEXT,
    "lead_id" TEXT,
    "responses_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "system_observations" (
    "id" BIGINT,
    "username" TEXT,
    "title" TEXT,
    "body" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "system_settings" (
    "key" TEXT,
    "value" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("key")
);

CREATE TABLE "system_update" (
    "id" BIGINT,
    "component" TEXT,
    "status" TEXT,
    "message" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "targeting_board_decisions" (
    "id" BIGINT,
    "decision_id" TEXT NOT NULL,
    "chain_id" TEXT NOT NULL,
    "board_id" TEXT,
    "nomination_title" TEXT,
    "decision" TEXT,
    "decision_reason" TEXT,
    "approved_funding" DOUBLE PRECISION,
    "approved_resources" TEXT,
    "commander_notes" TEXT,
    "decided_by" TEXT,
    "decided_at" TEXT,
    "created_by" TEXT,
    "updated_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "status" TEXT DEFAULT 'recorded',
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_targeting_board_decisions_1" UNIQUE ("decision_id")
);

CREATE TABLE "targeting_follow_on_actions" (
    "id" BIGINT,
    "action_id" TEXT NOT NULL,
    "chain_id" TEXT NOT NULL,
    "decision_id" TEXT,
    "board_id" TEXT,
    "action_title" TEXT,
    "action_details" TEXT,
    "owner" TEXT,
    "owner_role" TEXT,
    "support_requirements" TEXT,
    "due_date" TEXT,
    "status" TEXT DEFAULT 'open',
    "execution_notes" TEXT,
    "created_by" TEXT,
    "updated_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "completed_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_targeting_follow_on_actions_1" UNIQUE ("action_id")
);

CREATE TABLE "targeting_pipeline_comments" (
    "id" BIGINT,
    "chain_id" TEXT NOT NULL,
    "stage" TEXT NOT NULL,
    "comment_type" TEXT DEFAULT 'note',
    "comment_text" TEXT NOT NULL,
    "author_role" TEXT,
    "author_name" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "targeting_pipeline_history" (
    "id" BIGINT,
    "chain_id" TEXT NOT NULL,
    "stage" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "from_status" TEXT,
    "to_status" TEXT,
    "actor" TEXT,
    "details_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "targeting_pipeline_records" (
    "id" BIGINT,
    "chain_id" TEXT NOT NULL,
    "origin_stage" TEXT,
    "current_stage" TEXT NOT NULL,
    "pipeline_stage" TEXT,
    "record_type" TEXT,
    "title" TEXT NOT NULL,
    "issue_category" TEXT,
    "problem_statement" TEXT,
    "observed_pattern" TEXT,
    "mission_gap" TEXT,
    "impacted_scope" TEXT,
    "impacted_entity" TEXT,
    "recommended_focus_90_day" TEXT,
    "contributing_factors_json" TEXT,
    "staff_inputs_json" TEXT,
    "staff_input_notes" TEXT,
    "recommended_next_action" TEXT,
    "owner_lead" TEXT,
    "status" TEXT DEFAULT 'active',
    "active_flag" BIGINT DEFAULT 1,
    "inactive_reason" TEXT,
    "source_fusion_id" TEXT,
    "origin" TEXT,
    "nomination_type" TEXT,
    "requested_quarter" TEXT,
    "submitting_unit" TEXT,
    "briefer_submitter" TEXT,
    "requested_resources" TEXT,
    "requested_funding" DOUBLE PRECISION,
    "projected_impact" TEXT,
    "source_context" TEXT,
    "board_id" TEXT,
    "board_notes" TEXT,
    "board_decision" TEXT,
    "decision_authority" TEXT DEFAULT 'Battalion Commander',
    "created_by" TEXT,
    "updated_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "promoted_to_twg_at" TEXT,
    "promoted_to_board_at" TEXT,
    "decision_recorded_at" TEXT,
    "closed_at" TEXT,
    "rationale" TEXT,
    "due_date" TEXT,
    "validation_status" TEXT,
    "board_recommendation" TEXT,
    "readiness_blockers_json" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_targeting_pipeline_records_1" UNIQUE ("chain_id")
);

CREATE TABLE "task" (
    "id" BIGINT,
    "project_id" BIGINT,
    "title" TEXT,
    "owner" TEXT,
    "status" TEXT,
    "percent_complete" BIGINT DEFAULT 0,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "task_assignment" (
    "id" BIGINT,
    "task_id" BIGINT,
    "assignee" TEXT,
    "assigned_at" TEXT,
    "percent_expected" BIGINT,
    PRIMARY KEY ("id")
);

CREATE TABLE "task_comment" (
    "id" BIGINT,
    "task_id" BIGINT,
    "commenter" TEXT,
    "comment" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "tasks" (
    "task_id" TEXT,
    "project_id" TEXT,
    "title" TEXT,
    "description" TEXT,
    "owner" TEXT,
    "status" TEXT,
    "percent_complete" DOUBLE PRECISION DEFAULT 0,
    "due_date" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "import_job_id" TEXT,
    "record_status" TEXT DEFAULT 'active',
    "keep_until" TEXT,
    "archived_at" TEXT,
    PRIMARY KEY ("task_id")
);

CREATE TABLE "tickets" (
    "id" BIGINT,
    "title" TEXT,
    "category" TEXT,
    "description" TEXT,
    "priority" TEXT,
    "status" TEXT,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    PRIMARY KEY ("id")
);

CREATE TABLE "transform_recipes" (
    "id" BIGINT NOT NULL,
    "name" VARCHAR NOT NULL,
    "description" TEXT,
    "steps" JSONB NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_transform_recipes_1" UNIQUE ("name")
);

CREATE TABLE "twg_agenda_items" (
    "id" BIGINT,
    "twg_id" TEXT NOT NULL,
    "title" TEXT,
    "description" TEXT,
    "order_idx" BIGINT DEFAULT 0,
    "created_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "twg_board_items" (
    "id" BIGINT,
    "twg_id" TEXT NOT NULL,
    "title" TEXT,
    "description" TEXT,
    "linked_recommendation_id" BIGINT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "twg_items" (
    "id" BIGINT,
    "wg_id" BIGINT,
    "title" TEXT,
    "owner" TEXT,
    "due" TEXT,
    "status" TEXT,
    "notes" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "twg_minutes" (
    "id" BIGINT,
    "twg_id" TEXT NOT NULL,
    "minute_text" TEXT,
    "recorded_by" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "twg_tasks" (
    "id" BIGINT,
    "twg_id" TEXT NOT NULL,
    "title" TEXT,
    "details" TEXT,
    "assignee" TEXT,
    "status" TEXT DEFAULT 'open',
    "due_date" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    "archived" BIGINT DEFAULT 0,
    "archived_at" TEXT,
    "archived_by" TEXT,
    "created_by" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "unit" (
    "unit_code" TEXT,
    "echelon" TEXT NOT NULL,
    "unit_name" TEXT NOT NULL,
    "parent_code" TEXT,
    "created_at" TEXT NOT NULL DEFAULT datetime('now'),
    "updated_at" TEXT NOT NULL DEFAULT datetime('now'),
    PRIMARY KEY ("unit_code"),
    CONSTRAINT "fk_unit_0" FOREIGN KEY ("parent_code") REFERENCES "unit" ("unit_code")
);

CREATE TABLE "usarec_completion" (
    "id" TEXT,
    "scope_type" TEXT,
    "scope_value" TEXT,
    "completed_by" TEXT,
    "completed_at" TEXT,
    "details_json" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "user_account" (
    "id" TEXT,
    "email" TEXT NOT NULL,
    "display_name" TEXT,
    "password_hash" TEXT NOT NULL,
    "is_active" BIGINT DEFAULT 1,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_user_account_2" UNIQUE ("email")
);

CREATE TABLE "user_decisions" (
    "id" BIGINT,
    "recommendation_table" TEXT,
    "recommendation_id" BIGINT,
    "action" TEXT,
    "notes" TEXT,
    "user_id" TEXT,
    "created_at" TEXT DEFAULT datetime('now'),
    PRIMARY KEY ("id")
);

CREATE TABLE "user_permission" (
    "id" BIGINT,
    "user_id" BIGINT,
    "permission_key" TEXT,
    "granted" BIGINT DEFAULT 1,
    "granted_by" TEXT,
    "granted_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_user_permission_0" FOREIGN KEY ("permission_key") REFERENCES "permission" ("key"),
    CONSTRAINT "fk_user_permission_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE "user_permission_override" (
    "id" BIGINT,
    "user_id" TEXT,
    "permission_key" TEXT,
    "granted" BIGINT,
    "reason" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_user_permission_override_0" FOREIGN KEY ("permission_key") REFERENCES "permission" ("key"),
    CONSTRAINT "fk_user_permission_override_1" FOREIGN KEY ("user_id") REFERENCES "user_account" ("id")
);

CREATE TABLE "user_preferences" (
    "id" BIGINT,
    "user_id" BIGINT NOT NULL,
    "default_scope" TEXT,
    "sidebar_pinned" BIGINT DEFAULT 0,
    "saved_filters" TEXT,
    "created_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_user_preferences_1" UNIQUE ("user_id")
);

CREATE TABLE "user_role" (
    "user_id" TEXT,
    "role_key" TEXT,
    PRIMARY KEY ("user_id", "role_key"),
    CONSTRAINT "fk_user_role_0" FOREIGN KEY ("role_key") REFERENCES "role" ("role_key"),
    CONSTRAINT "fk_user_role_1" FOREIGN KEY ("user_id") REFERENCES "user_account" ("id")
);

CREATE TABLE "user_role_template" (
    "id" BIGINT,
    "user_id" BIGINT,
    "role_key" TEXT,
    "assigned_at" TEXT,
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_user_role_template_0" FOREIGN KEY ("role_key") REFERENCES "role_template" ("key"),
    CONSTRAINT "fk_user_role_template_1" FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE "user_roles" (
    "id" BIGINT,
    "user_id" BIGINT,
    "role_id" BIGINT,
    "assigned_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "users" (
    "id" BIGINT NOT NULL,
    "username" VARCHAR NOT NULL,
    "role" VARCHAR(14) NOT NULL,
    "scope" VARCHAR,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    CONSTRAINT "sqlite_autoindex_users_1" UNIQUE ("username")
);

CREATE TABLE "working_group" (
    "id" BIGINT,
    "org_unit_id" BIGINT,
    "name" TEXT,
    "wg_type" TEXT,
    "description" TEXT,
    "created_at" TEXT,
    "updated_at" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "zip_metrics" (
    "id" BIGINT,
    "zip" TEXT,
    "metric_key" TEXT,
    "metric_value" DOUBLE PRECISION,
    "station_rsid" TEXT,
    "scope" TEXT,
    "as_of" TEXT,
    PRIMARY KEY ("id")
);

CREATE INDEX "ix_station_rsid" ON "budget_line_item" ("station_rsid");
CREATE INDEX "ix_budget_line_item_event_id" ON "budget_line_item" ("event_id");
CREATE INDEX "ix_budget_line_item_project_id" ON "budget_line_item" ("project_id");
CREATE INDEX "ix_budget_line_item_eor" ON "budget_line_item" ("eor_code");
CREATE INDEX "ix_budget_line_item_funding_source" ON "budget_line_item" ("funding_source");
CREATE INDEX "ix_budget_line_item_dims" ON "budget_line_item" ("qtr", "event_id", "category", "amount");
CREATE INDEX "ix_budget_line_item_fy_org" ON "budget_line_item" ("fy_budget_id", "qtr");
CREATE INDEX "idx_documents_uploaded_at" ON "documents" ("uploaded_at");
CREATE INDEX "ix_event_dims" ON "event" ("fy", "qtr", "org_unit_id", "station_id", "funding_line", "category");
CREATE INDEX "ix_event_org_unit_id" ON "event" ("org_unit_id");
CREATE INDEX "ix_event_metrics_event_id" ON "event_metrics" ("event_id");
CREATE INDEX "ix_events_event_id" ON "events" ("event_id");
CREATE INDEX "ix_expenses_dims" ON "expenses" ("fy", "qtr", "org_unit_id", "station_id", "funding_line", "category");
CREATE INDEX "idx_dep_loss_station_tp_cmpnt" ON "fact_dep_loss" ("station_rsid", "time_period", "cmpnt_cd");
CREATE INDEX "idx_dep_loss_station_tp" ON "fact_dep_loss" ("station_rsid", "time_period");
CREATE INDEX "idx_dep_loss_station" ON "fact_dep_loss" ("station_rsid");
CREATE INDEX "idx_fact_emm_activity_begin" ON "fact_emm_activity" ("begin_date");
CREATE INDEX "idx_fact_emm_activity_fy" ON "fact_emm_activity" ("fy");
CREATE INDEX "idx_fact_emm_activity_rsid" ON "fact_emm_activity" ("rsid");
CREATE INDEX "idx_fact_enlistments_bn_as_of" ON "fact_enlistments_bn" ("as_of_date");
CREATE INDEX "idx_fact_enlistments_bn_rsid" ON "fact_enlistments_bn" ("rsid");
CREATE INDEX "ix_fact_funnel_dims" ON "fact_funnel" ("fy", "qtr", "scope_type", "scope_value");
CREATE INDEX "ix_fact_marketing_dims" ON "fact_marketing" ("fy", "qtr", "scope_type", "scope_value");
CREATE UNIQUE INDEX "ux_fact_marketing_org_date_campaign_channel" ON "fact_marketing" ("org_unit_id", "date_key", "campaign", "channel");
CREATE INDEX "ix_fact_dims" ON "fact_production" ("fy", "qtr", "scope_type", "scope_value");
CREATE UNIQUE INDEX "ux_fact_production_org_date_metric_job" ON "fact_production" ("org_unit_id", "date_key", "metric_key", "import_job_id");
CREATE INDEX "ix_fact_production_metric" ON "fact_production" ("metric_key");
CREATE INDEX "ix_fact_production_org_date" ON "fact_production" ("org_unit_id", "date_key");
CREATE INDEX "idx_fusion_evidence_run" ON "fusion_evidence" ("fusion_run_id");
CREATE INDEX "idx_fusion_process_date" ON "fusion_process" ("session_date");
CREATE INDEX "idx_fusion_unit" ON "fusion_recommendations" ("unit_rsid");
CREATE INDEX "idx_fusion_run_unit" ON "fusion_recommendations" ("fusion_run_id", "unit_rsid");
CREATE INDEX "ix_fy_budget_org_fy" ON "fy_budget" ("org_unit_id", "fy");
CREATE INDEX "idx_leads_created_at" ON "leads" ("created_at");
CREATE INDEX "idx_leads_zip5" ON "leads" ("zip5");
CREATE INDEX "idx_leads_school_id" ON "leads" ("school_id");
CREATE INDEX "idx_market_capacity_unit_fy" ON "market_capacity" ("unit_rsid", "fy");
CREATE INDEX "idx_mh_scores_market" ON "market_health_scores" ("market_type", "market_id");
CREATE INDEX "idx_mal_scores_run" ON "mission_allocation_company_scores" ("run_id");
CREATE INDEX "idx_mal_inputs_run" ON "mission_allocation_inputs" ("run_id");
CREATE INDEX "idx_mal_recs_run" ON "mission_allocation_recommendations" ("run_id");
CREATE INDEX "idx_mal_runs_unit" ON "mission_allocation_runs" ("unit_rsid");
CREATE INDEX "idx_mr_scores_unit" ON "mission_risk_scores" ("unit_rsid");
CREATE UNIQUE INDEX "idx_mission_target_unit_fy" ON "mission_target" ("unit_rsid", "fy");
CREATE INDEX "ix_org_unit_parent_id" ON "org_unit" ("parent_id");
CREATE INDEX "idx_out_rec" ON "outcome_records" ("recommendation_table", "recommendation_id");
CREATE INDEX "ix_outcomes_lead_id" ON "outcomes" ("lead_id");
CREATE UNIQUE INDEX "idx_permission_key" ON "permission" ("permission_key");
CREATE INDEX "ix_project_event_link_event" ON "project_event_link" ("event_id");
CREATE INDEX "ix_project_event_link_proj" ON "project_event_link" ("project_id");
CREATE INDEX "ix_projects_dims" ON "projects" ("fy", "qtr", "org_unit_id", "station_id", "funding_line", "category");
CREATE UNIQUE INDEX "ux_projects_project_id" ON "projects" ("project_id");
CREATE INDEX "idx_rex_rec" ON "recommendation_explanations" ("recommendation_table", "recommendation_id");
CREATE INDEX "idx_recruiter_strength_unit_month" ON "recruiter_strength" ("unit_rsid", "month");
CREATE INDEX "idx_targeting_board_decisions_chain" ON "targeting_board_decisions" ("chain_id", "decided_at");
CREATE INDEX "idx_targeting_follow_on_actions_chain" ON "targeting_follow_on_actions" ("chain_id", "status");
CREATE INDEX "idx_targeting_pipeline_comments_chain" ON "targeting_pipeline_comments" ("chain_id", "created_at");
CREATE INDEX "idx_targeting_pipeline_history_chain" ON "targeting_pipeline_history" ("chain_id", "created_at");
CREATE INDEX "idx_targeting_pipeline_board" ON "targeting_pipeline_records" ("board_id", "current_stage");
CREATE INDEX "idx_targeting_pipeline_stage" ON "targeting_pipeline_records" ("current_stage", "status");
CREATE UNIQUE INDEX "ux_tasks_task_id" ON "tasks" ("task_id");
CREATE INDEX "idx_unit_echelon" ON "unit" ("echelon");
CREATE INDEX "idx_unit_parent" ON "unit" ("parent_code");
CREATE INDEX "idx_udec_rec" ON "user_decisions" ("recommendation_table", "recommendation_id");
CREATE INDEX "ix_users_username" ON "users" ("username");
COMMIT;
