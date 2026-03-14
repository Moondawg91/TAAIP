# Command Center (Design Notes)

Purpose
-------
Single-pane dashboard that consolidates decision engine outputs for leadership and operators.

Data sources (existing APIs)
- Market Health: `/api/v2/market-health/latest`
- Mission Risk: `/api/v2/mission-risk/latest`
- School Targeting: `/api/v2/targeting/schools`
- Mission Allocation: mission allocation results/details endpoints

Core widgets (MVP)
- Top-line summary cards: Market Health score, Mission Risk aggregated score, Allocation coverage
- Time-series / as-of date selector (optional MVP)
- Tables: Top priority schools (from School Targeting), Top companies allocations (from Mission Allocation)
- Flags: Recruiting pressure indicators from existing inputs

UI tech: React + MUI (existing app uses MUI). Keep initial page as a new route under `apps/web/src/pages/command/`.

Acceptance criteria for MVP
- Page loads without runtime errors
- Pulls and displays latest results from the four engines
- Simple responsive layout with cards + tables

Next steps
1. Scaffold the page and basic fetch hooks (this commit)
2. Add small card components and wire to endpoints
3. Add smoke tests for data fetching
4. Iterate on layout and UX with screenshots
