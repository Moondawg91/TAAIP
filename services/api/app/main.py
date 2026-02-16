"""© 2025 Maroon Moon, LLC. All rights reserved.
API entrypoint and router mounting. OpenAPI description includes branding footer.
"""

from fastapi import FastAPI
from . import database
from . import api_org
from . import api_auth
from fastapi.middleware.cors import CORSMiddleware
from . import api_ingest
from . import api_domain


app = FastAPI(title="TAAIP API", description="TAAIP API service. © 2025 Maroon Moon, LLC. All rights reserved.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_auth.router)
app.include_router(api_org.router)
app.include_router(api_ingest.router)
app.include_router(api_domain.router)

# NOTE: Database schema must be managed with Alembic migrations.
# Run `alembic upgrade head` after configuring DATABASE_URL for your environment.


@app.get("/health")
def health():
    return {"status": "ok"}
