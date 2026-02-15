from fastapi import FastAPI
from . import database
from . import api_org
from . import api_auth
from fastapi.middleware.cors import CORSMiddleware
from . import api_ingest


app = FastAPI(title="TAAIP API")

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

# NOTE: Database schema must be managed with Alembic migrations.
# Run `alembic upgrade head` after configuring DATABASE_URL for your environment.


@app.get("/health")
def health():
    return {"status": "ok"}
