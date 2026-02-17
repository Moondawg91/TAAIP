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
from .db import init_schema, get_db_path




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
api_router.include_router(api_domain.router)
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
from .routers import meetings as meetings_router
api_router.include_router(meetings_router.router)
from .routers import calendar as calendar_router
api_router.include_router(calendar_router.router)
from .routers import analytics as analytics_router
api_router.include_router(analytics_router.router)
from .routers import events as events_router
api_router.include_router(events_router.router)
from .routers import budgets as budgets_router
api_router.include_router(budgets_router.router)
from .routers import projects as projects_router
api_router.include_router(projects_router.router)
from .routers import working_groups as wg_router
api_router.include_router(wg_router.router)
from .routers import docs as docs_router
api_router.include_router(docs_router.router)
from .routers import training as training_router
api_router.include_router(training_router.router)
from .routers import automation as automation_router
api_router.include_router(automation_router.router)
from .routers import compat_helpers as compat_helpers_router
api_router.include_router(compat_helpers_router.router)

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
        init_schema()
        _log.info(f"DB path: {get_db_path()}")
    except Exception as e:
        _log.error(f"DB init/seed failed: {e}")
