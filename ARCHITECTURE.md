# TAAIP — System Architecture (Targeting, AI/LMS, Compliance)

This document describes the updated architecture for TAAIP covering frontend, API gateway & auth, backend services, data & storage, targeting & AI, visualization & LMS, integrations, and security/governance.

## Goals
- Provide a unified frontend codebase for Web + Mobile (shared components).
- Separate business API and ML microservices for scale and security.
- Use managed Azure services for data and analytics while enabling model lifecycle and retraining.
- Meet DoD/Fed security posture (RMF / ATO / FedRAMP) and implement enterprise-grade logging and governance.

## Top-level Components
- Frontend (Single repo)
  - React (Web) + React Native (Mobile) using Expo + React Native Web for code sharing
  - Shared component library, design system, storybook for UI development
  - Two primary apps: Admin UI (web) and Recruiter Mobile App

- API Gateway & Authentication
  - Azure API Management (preferred) or Kong for on-prem/edge
  - OAuth2 + Azure AD (primary), support CAC/PIV for DoD users
  - WAF and rate-limiting policies at the gateway

- Backend Services
  - Node.js Business API(s) (REST/GraphQL) — handles orchestration, RBAC, business rules
  - Python ML microservices (FastAPI) — lead scoring, lookalike modeling, forecasting
  - Containerized services running in AKS (Azure Kubernetes Service)

- Data & Storage
  - Azure Database for PostgreSQL — primary transactional store
  - Azure Data Lake (object store), ingested into Synapse for analytics/warehouse
  - Redis for caching/session state
  - Elasticsearch (or OpenSearch) for search and analytic indexing

- Targeting & AI Layer
  - Lead Scoring Engine (Python / FastAPI) — real-time predictions
  - Lookalike models & forecasting in Azure ML — training & batch scoring
  - Model Registry, retraining pipelines (Azure ML Pipelines, MLOps)

- Visualization & LMS
  - Power BI or Vantage Embedded for dashboards
  - LMS integrations (MoodleGov, Microsoft Learn) for training modules and compliance

- Integrations / External Systems
  - Army systems (iKrome, BI Zone, G2 Zone, AIMS/Van)
  - Ad Platforms (aggregated ingestion), Google, Meta
  - Microsoft Graph for email/calendar interactions

- Security & Governance
  - RMF / ATO workflows, FedRAMP/DoD IL2+ compliance
  - Encryption at rest (Azure-managed keys) and in transit (TLS 1.2+)
  - HSM (Azure Key Vault + Managed HSM) for key management
  - Centralized logging (Azure Monitor), SIEM integration, audit trails, RBAC

- End Users / Outputs
  - BN / BDE leadership dashboards
  - Recruiters (mobile CRM + tasks)
  - G2 / BI analysts, campaign managers

## Data Flow (high level)
1. External sources (ad platforms, partner systems, Army systems) push or are pulled into ingestion pipelines.
2. Raw data lands in Azure Data Lake; streaming events go through event hub or Kafka (AKS/managed) into processing.
3. Processed events and canonical datasets are stored in Azure Data Lake and loaded to Synapse for analytics.
4. Business API (Node.js) reads/writes transactional data to PostgreSQL and serves UI requests.
5. Real-time scoring requests call the ML microservice (FastAPI) which uses a lightweight model or calls Azure ML for online scoring.
6. Batch model training uses Synapse datasets and Azure ML; trained models are versioned in Model Registry and published for batch/online scoring.
7. Dashboards and BI query Synapse or materialized views for reports and maps (CBSA overlays).
8. LMS systems receive enrollment events and training completion data back into analytics.

## Deployment Topology
- Azure subscription with segregated resource groups for:
  - Networking & Security (VNETs, NSGs, Azure Firewall)
  - Platform (AKS, Redis, Postgres)
  - Data (Data Lake, Synapse, Storage Accounts)
  - AI/ML (Azure ML workspace, Model Registry)
  - Observability (Log Analytics workspaces)

- AKS cluster(s):
  - Namespaces: `business-api`, `ml`, `ingest`, `infra`.
  - Use Azure AD pod identity for service identities.
  - Use Horizontal Pod Autoscaler for stateless services; Virtual Nodes / KEDA for burst workloads.

- Networking:
  - Private endpoints for databases and storage where possible.
  - API gateway (APIM) in front of public endpoints; internal services talk over private network.

## Security Controls
- Authentication & Authorization:
  - OAuth2 with Azure AD; for DoD/CAC users, integrate certificate-based auth (PIV) via gateway or identity broker.
  - RBAC enforced at API and data layer.

- Data Protection:
  - Transparent Data Encryption on PostgreSQL; storage account encryption.
  - Use Azure Key Vault for secrets; HSM for sensitive keys.

- Runtime Security:
  - Image scanning in CI (Trivy / Azure Container Registry tasks).
  - Pod security policies / OPA/Gatekeeper policies for AKS.
  - WAF on API gateway and DDoS protection.

- Auditing & Logging:
  - Central logging (Azure Monitor / Log Analytics). Forward to SIEM for retention and correlation.
  - Audit trails for model changes and data access (Data Access Governance).

## Model Lifecycle & MLOps
- Data preparation in Synapse / Data Factory.
- Training jobs orchestration in Azure ML; register models into a Model Registry with metadata and lineage.
- CI for models: automated unit tests, validation, and fairness checks.
- Deployment: real-time containerized scoring endpoint (FastAPI) for low-latency; batch scoring through Synapse/Azure ML.
- Retraining: scheduled pipelines triggered by data drift or time windows.

## Observability & SLOs
- Define SLOs: e.g., 99.9% availability for API Gateway; P95 latency for scoring endpoints <100ms (online model) or <500ms (proxy to Azure ML).
- Instrument services with OpenTelemetry, push to Azure Monitor.
- Alerts for error rates, latency, model performance drift, and data pipeline failures.

## CI/CD & IaC
- Use GitHub Actions (or Azure DevOps) for CI/CD.
- Build container images, run tests, scan images, push to Azure Container Registry.
- IaC: Bicep or Terraform for reproducible infra (AKS, Postgres, Key Vault, APIM, Synapse).
- Promotion workflow: dev -> staging -> prod with approvals and automated security gates.

## Scale & Cost Considerations
- Offload heavy batch work to Synapse and use spot/low-priority compute for experiments.
- Use autoscaling clusters and reserved capacity where predictable.
- Cache frequent read queries in Redis to reduce DB load.

## Compliance / RMF Considerations
- Document control sets and gap analysis against RMF/FedRAMP.
- Include continuous monitoring and annual ATO evidence packaging.
- Use Azure Blueprint patterns to enforce baseline controls.

## Quick Recommendations / Phased Roadmap
1. Phase 1 (MVP):
   - Frontend skeleton (React + RN web), Node.js Business API, FastAPI scoring service (simulated model), PostgreSQL, basic CI, host on AKS.
   - APIM with Azure AD auth; permissive CORS for dev only.
2. Phase 2:
   - Add Data Lake + Synapse ingestion; start offline model training with Azure ML.
   - Add Redis cache and Elasticsearch for search.
3. Phase 3:
   - Harden security (PIV integration, HSM, WAF tuning), implement MLOps, and integrate LMS and BI.
4. Phase 4 (ATO/Production):
   - RMF artifacts, continuous monitoring, SOX/FISMA evidence, and production readiness checks.

## Next artifacts to produce (I can generate)
- PlantUML diagram for architecture visualization (`diagrams/architecture.puml`).
- Sample Kubernetes manifests for `business-api` and `ml-scorer` with resource limits, probes, and horizontal autoscaler.
- A `run-dev.sh` to start local dev stack (fastapi + simple static server) and tests for the endpoints.


---

If you'd like, I will generate the PlantUML diagram and sample Kubernetes manifest files now.