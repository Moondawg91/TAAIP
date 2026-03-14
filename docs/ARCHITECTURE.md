## TAAIP System Architecture

```mermaid
flowchart LR
  subgraph Ingestion
    A[Data Ingestion<br/>(CSV, API, Backfills)]
    B[Preprocessing / ETL]
  end

  subgraph Storage
    DB[(SQLite / Postgres / Persistent DB)]
  end

  subgraph Backend
    API[API Gateway / Routers]
    Migrations[Runtime Migrations]
    Tests[Test Suite (pytest)]
    CI[CI - GitHub Actions]

    subgraph Engines
      MH[Market Health Engine]
      ST[School Targeting Engine]
      MR[Mission Risk Engine]
      MA[Mission Allocation Engine]
    end
  end

  subgraph Frontend
    Web[React + MUI]
    CC[Command Center]
    MAL[Mission Allocation UI]
    TB[Targeting Board]
  end

  %% Data flows
  A --> B --> DB
  DB --> MH
  DB --> ST
  DB --> MR
  DB --> MA

  MH --> DB
  ST --> DB
  MR --> DB
  MA --> DB

  MH --> API
  ST --> API
  MR --> API
  MA --> API

  API --> Web
  Web --> CC
  Web --> MAL
  Web --> TB

  %% Operations
  CI --> Tests
  CI --> Migrations
  CI --> API
  CI --> Web

  Tests --> API
  Tests --> Engines

  Migrations --> DB

  %% Notes
  classDef engines fill:#fef3c7,stroke:#f59e0b;
  class MH,ST,MR,MA engines

  classDef backend fill:#eef2ff,stroke:#6366f1;
  class API,Migrations,Tests,CI backend

  classDef frontend fill:#ecfccb,stroke:#84cc16;
  class Web,CC,MAL,TB frontend

  %% labels
  MH:::engines
  ST:::engines
  MR:::engines
  MA:::engines

  API:::backend
  CI:::backend
  Tests:::backend
  Migrations:::backend

  Web:::frontend
  CC:::frontend
  MAL:::frontend
  TB:::frontend
```

### Ingestion framework

- Sources: CSV uploads, scheduled ETL, backfills, and external APIs.
- Preprocessing normalizes fields, timestamps, and canonical IDs (company_rsid, school_id).

### Canonical storage

- Primary persistent store: Postgres (recommended) or SQLite for local/dev.
- Canonical tables created by runtime migrations: market_health_scores, market_health_evidence, school_targeting_scores, mission_risk_scores, mission_risk_evidence, mission_allocation_*.

### Decision engines (completed)

- Market Health — computes market supportability and evidence
- School Targeting — computes school priority scores
- Mission Risk — computes mission-level risk scores and top factors
- Mission Allocation — produces allocation recommendations and integrates MH/MR evidence

### API layer

- REST endpoints under `/api/v2/` expose engines and allocation data. Key endpoints:
  - `POST /api/v2/mission-risk/run`
  - `GET  /api/v2/mission-risk/latest`
  - `POST /api/v2/market-health/run`
  - `GET  /api/v2/market-health/latest`
  - `POST /api/v2/school-targeting/run`
  - `GET  /api/v2/targeting/schools`
  - Mission Allocation endpoints for run/results/details

### Frontend pages (current)

- `apps/web/src/pages/command/MissionAllocationPage.jsx` — Mission Allocation UI with evidence table
- `apps/web/src/pages/command/TargetingBoard.jsx` — Targeting Board shows school priorities
- `apps/web/src/pages/command/CommandCenter.jsx` — (scaffolded) Command Center aggregator

### CI / Tests

- GitHub Actions workflow runs targeted tests on PRs and pushes to `main`.
- Test suite: `pytest` under `services/api/app/tests/` covers engine math, persistence, endpoints, and integration.

### Scaffolded future connectors

- External CRM / outreach system connector (planned)
- PowerBI / Looker export (reporting connector)
- Streaming ingestion (Kafka) for real-time scoring

### Next planned modules

1. Mission Risk tuning pass (small adjustments to weights and penalty)
2. Command Center feature completion: richer cards, time-series, filters
3. Targeting Intelligence (PMESII-PT / ASCOPE analytics)
4. Production migrations and backfill plan
