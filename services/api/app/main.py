"""© 2026 TAAIP. Copyright pending. All rights reserved.
API entrypoint and router mounting. OpenAPI description includes branding footer.
"""

from dotenv import load_dotenv
import os
import logging

# Load environment variables from services/api/.env (local dev)
load_dotenv("services/api/.env")
load_dotenv()

# Log LOCAL_DEV_AUTH_BYPASS at startup for visibility
_log = logging.getLogger("uvicorn")
_log.info(f"LOCAL_DEV_AUTH_BYPASS={os.getenv('LOCAL_DEV_AUTH_BYPASS')}")

from fastapi import FastAPI, APIRouter
from . import database
from . import api_org
from . import api_auth
from .routers import compat_org
from fastapi.middleware.cors import CORSMiddleware
from . import api_ingest
from . import api_domain
from .db import init_db, get_db_path




app = FastAPI(title="TAAIP API", description="TAAIP API service. © 2026 TAAIP. Copyright pending.")

# Create a single API router mounted under /api so all app endpoints live
# under a common namespace.
api_router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router.include_router(compat_org.router)
api_router.include_router(api_auth.router)
api_router.include_router(api_org.router)
api_router.include_router(api_ingest.router)
# v1/v2 routers will be included later after domain routers to ensure
# domain (SQLAlchemy) endpoints take precedence over older compatibility routes.
from .routers import powerbi_feed
api_router.include_router(powerbi_feed.router)
from .routers import imports as imports_router
api_router.include_router(imports_router.router)
from .routers import rbac as rbac_router
api_router.include_router(rbac_router.router)
from .routers import funnel as funnel_router
api_router.include_router(funnel_router.router)
from .routers import benchmarks as benchmarks_router
api_router.include_router(benchmarks_router.router)
from .routers import projects as projects_router
api_router.include_router(projects_router.router)
from .routers import command_priorities as command_priorities_router
api_router.include_router(command_priorities_router.router)
from .routers import meetings as meetings_router
api_router.include_router(meetings_router.router)
from .routers import calendar as calendar_router
api_router.include_router(calendar_router.router)
from .routers import analytics as analytics_router
api_router.include_router(analytics_router.router)
from .routers import rollups as rollups_router
api_router.include_router(rollups_router.router)
from .routers import events as events_router
api_router.include_router(events_router.router)
from .routers import mission_assessments as mission_assessments_router
api_router.include_router(mission_assessments_router.router)
from .routers import budgets as budgets_router
api_router.include_router(budgets_router.router)
from .routers import projects as projects_router
api_router.include_router(projects_router.router)
from .routers import working_groups as wg_router
api_router.include_router(wg_router.router)
from .routers import docs as docs_router
api_router.include_router(docs_router.router)
from .routers import resources as resources_router
api_router.include_router(resources_router.router)
from .routers import training as training_router
api_router.include_router(training_router.router)
from .routers import automation as automation_router
api_router.include_router(automation_router.router)
from .routers import home as home_router
api_router.include_router(home_router.router)
from .routers import v2_home as v2_home_router
api_router.include_router(v2_home_router.router)
from .routers import v2_org as v2_org_router
api_router.include_router(v2_org_router.router)
from .routers import compat_helpers as compat_helpers_router
api_router.include_router(compat_helpers_router.router)

from .routers import health as health_router
api_router.include_router(health_router.router)
from .routers import exports as exports_router
api_router.include_router(exports_router.router)

# System/self-check router
from .routers import system as system_router
api_router.include_router(system_router.router)
from .routers import budget_summary as budget_summary_router
api_router.include_router(budget_summary_router.router)
from .routers import budget_dashboard as budget_dashboard_router
api_router.include_router(budget_dashboard_router.router)
from .routers import comptroller as comptroller_router
api_router.include_router(comptroller_router.router)
from .routers import projects_dashboard as projects_dashboard_router
api_router.include_router(projects_dashboard_router.router)
from .routers import events_dashboard as events_dashboard_router
api_router.include_router(events_dashboard_router.router)
from .routers import performance_dashboard as performance_dashboard_router
api_router.include_router(performance_dashboard_router.router)
from .routers import performance_summary as performance_summary_router
api_router.include_router(performance_summary_router.router)
from .routers import planning_summary as planning_summary_router
api_router.include_router(planning_summary_router.router)
from .routers import operations_summary as operations_summary_router
api_router.include_router(operations_summary_router.router)
from .routers import imports_compat as imports_compat_router
api_router.include_router(imports_compat_router.router)
from .routers import meta as meta_router
api_router.include_router(meta_router.router)

from .routers import tactical_rollups as tactical_rollups_router
api_router.include_router(tactical_rollups_router.router)

from .routers import tactical_dashboards as tactical_dashboards_router
api_router.include_router(tactical_dashboards_router.router)

# New lightweight dashboards router for empty-safe dashboard endpoints
from .routers import dashboards as dashboards_router
api_router.include_router(dashboards_router.router)

# Dashboard exports for CSV/JSON
from .routers import exports_dashboards as exports_dashboards_router
api_router.include_router(exports_dashboards_router.router)

# Command center router (mission-assessment + priorities)
from .routers import command_center as command_center_router
api_router.include_router(command_center_router.router)

from .routers import maintenance as maintenance_router
api_router.include_router(maintenance_router.router)
# start the DB-driven maintenance scheduler (disabled by default in test/dev)
if os.getenv('RUN_MAINT_SCHED', '0') == '1':
    try:
        from . import maintenance_scheduler
        maintenance_scheduler.start_scheduler(poll_interval=int(os.getenv('MAINT_POLL_SECONDS', '60')))
    except Exception:
        pass

# New v1/v2 compatibility routers for test-suite
from .routers import v1 as v1_router
from .routers import v2 as v2_router
api_router.include_router(v1_router.router)
api_router.include_router(v2_router.router)

# include domain router after compatibility routers so legacy /api/v2 compatibility
# endpoints (used by tests) take precedence over SQLAlchemy domain routes
api_router.include_router(api_domain.router)

# additional operational endpoints
from .routers import event_ops as event_ops_router
api_router.include_router(event_ops_router.router)
from .routers import tasks as tasks_router
api_router.include_router(tasks_router.router)
from .routers import boards as boards_router
api_router.include_router(boards_router.router)

# Mount the composed API router under /api
app.include_router(api_router, prefix="/api")

# NOTE: Database schema must be managed with Alembic migrations.
# Run `alembic upgrade head` after configuring DATABASE_URL for your environment.


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def _on_startup():
    # initialize DB schema and optionally seed deterministic dev data
    try:
        init_db()
        _log.info(f"DB path: {get_db_path()}")
    except Exception as e:
        _log.error(f"DB init/seed failed: {e}")
