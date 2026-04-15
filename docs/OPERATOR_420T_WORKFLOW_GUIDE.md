# 420T Operator Workflow Guide

Purpose:
- Execute operator drill-downs using the same connected backend outputs consumed by command.
- Keep operations evidence-based and traceable.

## Access Perspective

Open shell with operator perspective:
- `?role=operator420t`

Operator path:
- Workflow Home
- Command Center
- Market to ROI Diagnostics
- TWG and Targeting Board
- Asset, Execution, Processing
- Power BI

Notes:
- Operator perspective intentionally excludes admin console.
- Mission Adjustment is commander-focused and not shown in operator path.

## Daily Operator Sequence

## 1) Command Center Snapshot

- Confirm current posture and alerts.
- Identify focus areas for drill-down.

## 2) Diagnostics Drill-Down

- Review market/funnel/school/ROI signals.
- Capture evidence that supports expected action.

## 3) Decision Sync (TWG and Board)

- Confirm prioritized items and board-directed shifts.
- Ensure operator actions align with board intent.

## 4) Execution and Processing

- Review execution tracker state:
  - not started
  - in progress
  - completed
  - blocked
- Review flash-to-bang processing health and stalled items.
- Identify escalations for TWG/BOARD routing.

## 5) Export Surface

- Confirm Power BI operational output reflects same signal chain.

## Operator Sustainment Rules

- Do not manually override upstream analytics in UI.
- Do not use admin refresh controls from operator workflows.
- Treat no-data as a valid operational state requiring scope/source review.

## Operator Troubleshooting Quick Checks

- If view is empty, verify perspective and scope.
- If processing appears stale, verify upstream execution state and source freshness.
- If data quality is suspect, route issue through admin refresh workflow.
