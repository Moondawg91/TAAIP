# TAAIP Command Demo Sequence

This sequence uses only the connected authoritative outputs already in production flow.
It does not introduce synthetic analytics and does not require demo-only data.

## Audience Perspectives

- Commander / Command Team
- 420T Operator
- Admin / Maintainer

## Opening Screen

Start at the commander workflow shell home in `taaip-dashboard`.

Opening message:
- The workflow is one connected path from command picture to execution and export.
- Admin controls are isolated from commander and operator perspectives.

## Decision Flow

1. Command Center
- Show current command picture and connected phase2 operational block.
- Confirm alerts, LOE posture, targeting signal, accountability signal, and execution signal are present.

2. Mission Adjustment
- Move directly into feasibility/mission adjustment justification.
- Keep this step in the commander path only.

3. Diagnostics
- Show market, funnel, school access, school plan, and ROI diagnostics.
- Call out how diagnostics map to downstream board and execution actions.

4. TWG and Targeting Board
- Show synchronized posture between TWG prioritization and board-directed actions.
- Confirm decisions are reflected downstream and not recomputed in the UI.

5. Asset, Execution, and Processing
- Show asset distribution recommendations, execution tracker state, and flash-to-bang processing health.
- Demonstrate stalled/blocked execution escalation logic.

6. Power BI Export Surface
- Close with authoritative export-facing surface for command reporting.

## 420T Operator Walkthrough

Use operator perspective to validate drill-down support without admin controls.

1. Command Center
- Confirm operator can view command picture and operational signals.

2. Diagnostics and Decision Sync
- Drill into diagnostics, TWG, and targeting board context used for action.

3. Execution and Processing
- Validate execution task state, blocked/off-track conditions, and supporting rationale.
- Confirm operator evidence comes from authoritative backend outputs only.

## Admin / Maintainer Walkthrough

Use admin perspective for safe maintenance controls.

1. Admin Console and Refresh Surfaces
- Validate refresh source management is admin-only.
- Validate schema/no-data failures are structured and honest.

2. Safety Check
- Confirm admin maintenance actions do not alter commander/operator shell visibility.
- Confirm no command-facing step exposes admin-only controls.

## Evidence Points During Demo

- Command Center summary includes connected phase2 outputs.
- Mission adjustment output includes rationale/evidence and confidence signals.
- Diagnostics show market/funnel/school/ROI linkage.
- TWG and board posture align with execution downstream.
- Execution and processing show status, blockers, and escalations.
- Admin refresh routes enforce `admin.permissions.manage` and reject invalid/no-data uploads without rebinding active datasets.

## Expected Commander Questions

- What changed from command picture to mission adjustment recommendation?
- Which diagnostics most influenced targeting and execution posture?
- What is currently blocked/off-track and what was escalated?
- Are exports aligned to the same authoritative pipeline used in the command view?
- What happens if source data is missing or invalid during refresh?

## Fallback Behavior for No-Data Scopes

- Command Center and diagnostics return neutral/no-data shapes instead of fabricated defaults.
- Mission adjustment returns structured no-data/partial-signal context and does not invent outputs.
- Refresh uploads with no rows fail as `no_data` and do not update `dataset_active`.
- Refresh uploads with missing required schema fail as `invalid_schema` and do not update `dataset_active`.

## Role-Safe Validation Checklist

- Commander perspective shows commander workflow steps and no admin console.
- 420T operator perspective shows operational drill-down sequence and no admin console.
- Admin perspective can access admin console and refresh controls.
- Non-admin roles receive 403 on refresh source routes.
