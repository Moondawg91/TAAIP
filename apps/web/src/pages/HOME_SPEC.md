Home — 420T Command Decision Support Portal

Specification (locked):

- Title: Home — 420T Command Decision Support Portal
- Layout: 3-column PowerBI style
  - LEFT (md=3): Quick Actions; System Readiness
  - CENTER (md=6): Strategic Flash Feed; Upcoming Items
  - RIGHT (md=3): Reference Rails; Data Status

System Readiness sources:
- GET /api/system/status
- GET /api/market-intel/readiness
- GET /api/phonetics/readiness

Blocking UI behavior:
- Show missing dataset keys and provide direct link to Imports Center and import templates.

Design constraints:
- Dark PowerBI-style look preserved
- Dense layout
- borderRadius <= 4px
- Do not reorder sidebar sections or rename reference rails

Snapshot test: Home page must include the title and the two key headings: "Strategic Flash Feed" and "Reference Rails".
