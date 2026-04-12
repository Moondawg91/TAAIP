# Backend Placeholder Classification

Scanned placeholder/backlog backend modules and classification.

- services/api/app/services/mission_allocation_engine.py
  - Status: implemented skeleton with scoring and recommendations.
  - Classification: implement now (functionality largely present). Keep and refine; no nav changes required.

- services/api/app/automation/engine.py
  - Status: simple heuristic implemented (`simple_event_recommendation`). Persists recommendations to `ai_recommendation`.
  - Classification: temporary shim acceptable for local dev. Keep as-is and document behavior.

- services/api/app/routers/fs_loss.py
  - Status: returns empty-safe placeholder summary until Data Hub imports exist; includes small station-level aggregation if table present.
  - Classification: temporary shim acceptable for local dev; hide UI nav for this feature until Data Hub data is available.

- Export generation paths (various routers e.g., budget_dashboard, powerbi_feed)
  - Status: several export endpoints implemented (CSV/JSON/XLSX/PDF/PPTX) with fallbacks.
  - Classification: implemented now - no immediate work required.

Notes:
- Action taken: Hidden FS Loss and several frontend pages from nav to avoid clickable dead pages. Mission allocation engine left as implemented skeleton.
- Next steps: optionally implement richer mission allocation algorithms and provide configuration for automation heuristics. For now, mark these as "working but iterative".
