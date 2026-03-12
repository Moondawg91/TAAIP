# TOR Route Matrix

This document lists critical TOR routes and their duty/function, KPIs and primary data sources. Protect these routes from deletion or accidental merge.

| Route | TOR Duty / Function | KPIs | Primary Data Sources |
|---|---|---|---|
| /planning | Planning / TWG / Fusion hub | Meeting cadence, proposals completed | EMM, G2, Vantage, AIE |
| /planning/calendar | QTR planning calendar | Events scheduled, capacity | EMM, Calendar feeds |
| /roi/events | ROI event rollups and detail | CPL, CPC, ROI score | EMM, Leads, Vantage |
| /schools | School recruiting dashboard | Leads, engagements, conversions | ALRL, AIE, Vantage |
| /data-hub | Data Hub (ONLY uploads) | Uploads, runs, coverage | Local/S3 + registry |
| /helpdesk/new | Submit new help ticket | Tickets created, SLA | Helpdesk DB |
| /helpdesk/status | Ticket status | Open/closed metrics | Helpdesk DB |
| /budget | Budget dashboard | Spend vs plan, allocations | Finance feeds |
| /command-center | 420T Command Center | Operational readiness KPIs | EMM, G2, Org data |

**Tested routes**
- See `apps/web/src/__tests__/tor_routes.test.js`

Maintainers: TAAIP Frontend team
