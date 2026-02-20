# TAAIP Requirements Gap Report

Total requirements: 50

Missing: 24

## R001 - Sidebar - Dashboard

Status: **MISSING**

- Check: frontend_route /dashboard — MISSING
- Check: nav_path /dashboard — MISSING

## R002 - Sidebar - Command Center

Status: **MISSING**

- Check: frontend_route /command-center — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts
- Check: nav_path /command-center — MISSING

## R003 - Sidebar - Projects & Events

Status: **MISSING**

- Check: frontend_route /planning/projects-events — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts
- Check: nav_path /planning/projects-events — MISSING

## R004 - Budget Tracker

Status: **MISSING**

- Check: frontend_route /budget/tracker — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts
- Check: backend_route /api/budget/dashboard — MISSING

## R005 - Events ROI rollup

Status: **MISSING**

- Check: backend_route /api/rollups/events — MISSING

## R006 - Marketing rollup

Status: **MISSING**

- Check: backend_route /api/rollups/marketing — MISSING

## R007 - Funnel rollup

Status: **MISSING**

- Check: backend_route /api/rollups/funnel — MISSING

## R008 - Mission Assessment

Status: **MISSING**

- Check: backend_route /api/command-center/mission-assessment — MISSING
- Check: frontend_route /command-center/mission-assessment — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts

## R009 - Command Priorities API

Status: **MISSING**

- Check: backend_route /api/command-center/priorities — MISSING

## R010 - LOEs API

Status: **MISSING**

- Check: backend_route /api/command-center/loes — MISSING

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

Status: **MISSING**

- Check: backend_route /api/budget/dashboard/export.csv — MISSING
- Check: regex apps/web/src/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/contexts/ScopeContext.tsx

## R016 - Exports - JSON endpoint

Status: **MISSING**

- Check: backend_route /api/budget/dashboard — MISSING

## R017 - Home - news/updates/quick links

Status: **OK**

- Check: frontend_route / — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts
- Check: regex apps/web/src/pages/HomePage.tsx — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/pages/HomePage.tsx

## R018 - No visible "Scope" wording

Status: **MISSING**

- Check: forbidden_word apps/web/src/** — MISSING
  - Where: ['/Users/ambermooney/Desktop/TAAIP/apps/web/src/contexts/ScopeContext.tsx', '/Users/ambermooney/Desktop/TAAIP/apps/web/src/components/ScopePicker.js', '/Users/ambermooney/Desktop/TAAIP/apps/web/src/components/SidebarFilters.js', '/Users/ambermooney/Desktop/TAAIP/apps/web/src/api/client.js', '/Users/ambermooney/Desktop/TAAIP/apps/web/src/pages/command/LinesOfEffortPage.tsx']

## R019 - Dark theme present

Status: **MISSING**

- Check: file_glob apps/web/src/theme/muiTheme.ts — OK
  - Where: ['/Users/ambermooney/Desktop/TAAIP/apps/web/src/theme/muiTheme.ts']
- Check: regex apps/web/src/theme/muiTheme.ts — MISSING

## R020 - Funding source taxonomy

Status: **OK**

- Check: regex apps/web/src/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/constants/funding.ts

## R021 - No demo operational data seeded

Status: **MISSING**

- Check: forbidden_word populate_*.py — MISSING
  - Where: ['/Users/ambermooney/Desktop/TAAIP/populate_twg_data.py']

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

Status: **MISSING**

- Check: backend_route /api/system/status — MISSING
- Check: backend_route /api/system/observations — MISSING
- Check: backend_route /api/system/proposals — MISSING

## R026 - Command Center pages wired

Status: **MISSING**

- Check: frontend_route /command-center/priorities — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts
- Check: frontend_route /command-center/lines-of-effort — MISSING

## R027 - Export buttons/pages present

Status: **OK**

- Check: regex apps/web/src/components/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/components/dashboard/DashboardToolbar.tsx

## R028 - Budget API empty-safe

Status: **MISSING**

- Check: backend_route /api/budget/dashboard — MISSING
- Check: regex services/api/app/routers/budget_dashboard.py — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/budget_dashboard.py

## R029 - Maintenance guard implemented in frontend

Status: **MISSING**

- Check: regex apps/web/src/App.js — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/App.js
- Check: frontend_route /maintenance — MISSING

## R030 - API import check command present in docs

Status: **MISSING**

- Check: regex **/DEPLOYMENT_*.md — MISSING

## R031 - Tactical rollups linked to budget

Status: **OK**

- Check: regex services/api/app/routers/** — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/services/api/app/routers/exports.py

## R032 - Home status strip endpoint used

Status: **MISSING**

- Check: regex apps/web/src/pages/HomePage.tsx — MISSING

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
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts

## R039 - System self-check UI exists (admin)

Status: **OK**

- Check: frontend_route /admin/system-self-check — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts

## R040 - Role management UI

Status: **OK**

- Check: frontend_route /admin/roles — OK
  - Where: /Users/ambermooney/Desktop/TAAIP/apps/web/src/nav/navConfig.ts

## R041 - Events page exists

Status: **MISSING**

- Check: frontend_route /ops/events — MISSING

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

Status: **MISSING**

- Check: backend_route /api/meta/routes — MISSING

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

Status: **MISSING**

- Check: regex **/GETTING_STARTED*.md — MISSING
- Check: regex **/DEPLOYMENT_*.md — MISSING
- Check: regex **/LOCAL_SETUP.md — MISSING

