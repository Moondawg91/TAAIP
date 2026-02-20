# TAAIP Requirements Gap Report

Total requirements: 50

Missing: 0

## R001 - Sidebar - Dashboard

Status: **OK**

- Check: frontend_route /dashboard — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: nav_path /dashboard — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts

## R002 - Sidebar - Command Center

Status: **OK**

- Check: frontend_route /command-center — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: nav_path /command-center — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts

## R003 - Sidebar - Projects & Events

Status: **OK**

- Check: frontend_route /planning/projects-events — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: nav_path /planning/projects-events — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts

## R004 - Budget Tracker

Status: **OK**

- Check: frontend_route /budget/tracker — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: backend_route /api/budget/dashboard — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/budget_dashboard.py

## R005 - Events ROI rollup

Status: **OK**

- Check: backend_route /api/rollups/events — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/tactical_rollups.py

## R006 - Marketing rollup

Status: **OK**

- Check: backend_route /api/rollups/marketing — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/tactical_rollups.py

## R007 - Funnel rollup

Status: **OK**

- Check: backend_route /api/rollups/funnel — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/tactical_rollups.py

## R008 - Mission Assessment

Status: **OK**

- Check: backend_route /api/command-center/mission-assessment — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/command_center.py
- Check: frontend_route /command-center/mission-assessment — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js

## R009 - Command Priorities API

Status: **OK**

- Check: backend_route /api/command-center/priorities — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/command_center.py

## R010 - LOEs API

Status: **OK**

- Check: backend_route /api/command-center/loes — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/command_center.py

## R011 - Imports - upload endpoint

Status: **OK**

- Check: backend_route /api/import/upload — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/imports.py

## R012 - Imports - parse & map & validate & commit

Status: **OK**

- Check: backend_route /api/import/parse — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/imports.py
- Check: backend_route /api/import/map — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/imports.py
- Check: backend_route /api/import/validate — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/imports.py
- Check: backend_route /api/import/commit — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/imports.py

## R013 - RBAC helpers present

Status: **OK**

- Check: file_glob services/api/app/routers/rbac.py — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/services/api/app/routers/rbac.py']
- Check: regex services/api/app/routers/rbac.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/rbac.py

## R014 - Audit logging utility

Status: **OK**

- Check: regex services/api/app/routers/rbac.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/rbac.py

## R015 - Exports - CSV endpoint

Status: **OK**

- Check: backend_route /api/budget/dashboard/export.csv — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/budget_dashboard.py
- Check: regex apps/web/src/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/contexts/ScopeContext.tsx

## R016 - Exports - JSON endpoint

Status: **OK**

- Check: backend_route /api/budget/dashboard — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/budget_dashboard.py

## R017 - Home - news/updates/quick links

Status: **OK**

- Check: frontend_route / — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: regex apps/web/src/pages/HomePage.tsx — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/pages/HomePage.tsx

## R018 - No visible "Scope" wording

Status: **OK**

- Check: forbidden_word apps/web/src/{components,pages}/**/*.{js,jsx,ts,tsx} — OK

## R019 - Dark theme present

Status: **OK**

- Check: file_glob apps/web/src/theme/muiTheme.ts — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/apps/web/src/theme/muiTheme.ts']
- Check: regex apps/web/src/theme/muiTheme.ts — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/theme/muiTheme.ts

## R020 - Funding source taxonomy

Status: **OK**

- Check: regex apps/web/src/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/constants/funding.ts

## R021 - No demo operational data seeded

Status: **OK**

- Check: forbidden_word populate_*.py — OK

## R022 - Drilldown dropdown filters present

Status: **OK**

- Check: regex apps/web/src/components/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/components/DashboardFilterBar.tsx

## R023 - Nav items route without runtime error

Status: **OK**

- Check: nav_routes_match  — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts', '/Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js']

## R024 - System self-check endpoint

Status: **OK**

- Check: backend_route /api/system/self-check — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/system.py

## R025 - Maintenance endpoints

Status: **OK**

- Check: backend_route /api/system/status — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/system.py
- Check: backend_route /api/system/observations — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/system.py
- Check: backend_route /api/system/proposals — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/system.py

## R026 - Command Center pages wired

Status: **OK**

- Check: frontend_route /command-center/priorities — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: frontend_route /command-center/lines-of-effort — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js

## R027 - Export buttons/pages present

Status: **OK**

- Check: regex apps/web/src/components/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/components/dashboard/DashboardToolbar.tsx

## R028 - Budget API empty-safe

Status: **OK**

- Check: backend_route /api/budget/dashboard — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/budget_dashboard.py
- Check: regex services/api/app/routers/budget_dashboard.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/budget_dashboard.py

## R029 - Maintenance guard implemented in frontend

Status: **OK**

- Check: regex apps/web/src/App.js — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: frontend_route /maintenance — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js

## R030 - API import check command present in docs

Status: **OK**

- Check: regex **/DEPLOYMENT_*.md — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/DEPLOYMENT_QUICKSTART.md

## R031 - Tactical rollups linked to budget

Status: **OK**

- Check: regex services/api/app/routers/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/exports.py

## R032 - Home status strip endpoint used

Status: **OK**

- Check: regex apps/web/src/pages/HomePage.tsx — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/pages/HomePage.tsx

## R033 - RBAC enforcement in routers

Status: **OK**

- Check: regex services/api/app/routers/**/*.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/system.py

## R034 - Audit log table creation in codebase

Status: **OK**

- Check: regex services/api/app/routers/rbac.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/rbac.py

## R035 - Exports placeholders for ppt/pdf/xlsx

Status: **OK**

- Check: regex services/api/app/routers/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/exports.py

## R036 - Navigation config exists

Status: **OK**

- Check: file_glob apps/web/src/nav/navConfig.ts — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts']

## R037 - No improper rounded UI styles

Status: **OK**

- Check: regex apps/web/src/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/index.css

## R038 - Help / system status page exists

Status: **OK**

- Check: frontend_route /help/system-status — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js

## R039 - System self-check UI exists (admin)

Status: **OK**

- Check: frontend_route /admin/system-self-check — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js

## R040 - Role management UI

Status: **OK**

- Check: frontend_route /admin/roles — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js

## R041 - Events page exists

Status: **OK**

- Check: frontend_route /ops/events — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js

## R042 - Command Priorities UI export

Status: **OK**

- Check: regex apps/web/src/pages/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/pages/insights/AnalyticsPage.tsx

## R043 - Mission assessment payload shape

Status: **OK**

- Check: regex services/api/app/routers/command_center.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/command_center.py

## R044 - Budget breakdown endpoints

Status: **OK**

- Check: regex services/api/app/routers/budget_dashboard.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/budget_dashboard.py

## R045 - Maintenance scheduler off by default

Status: **OK**

- Check: regex services/api/app/main.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/main.py

## R046 - Route health meta endpoint

Status: **OK**

- Check: backend_route /api/meta/routes — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/meta.py

## R047 - Top header component exists

Status: **OK**

- Check: file_glob apps/web/src/components/TopHeader.tsx — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/apps/web/src/components/TopHeader.tsx']

## R048 - Empty state components used

Status: **OK**

- Check: file_glob apps/web/src/components/common/EmptyState.tsx — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/apps/web/src/components/common/EmptyState.tsx']
- Check: regex apps/web/src/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/components/common/EmptyState.tsx

## R049 - Tests or conftest exist for imports

Status: **OK**

- Check: file_glob services/api/tests/test_commit_fallback.py — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/services/api/tests/test_commit_fallback.py']

## R050 - Documentation: How to run build + import checks

Status: **OK**

- Check: regex **/GETTING_STARTED*.md — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/GETTING_STARTED.md
- Check: regex **/DEPLOYMENT_*.md — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/DEPLOYMENT_QUICKSTART.md

