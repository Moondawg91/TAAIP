import os
import pathlib

# Ensure tests run with a deterministic test DB set before any imports
TEST_DB = os.environ.get('TAAIP_DB_PATH', './taaip_test.db')
os.environ.setdefault('TAAIP_DB_PATH', TEST_DB)
os.environ.setdefault('DATABASE_URL', f"sqlite:///{TEST_DB}")

# Remove an old test DB if present to ensure a clean slate
try:
    p = pathlib.Path(TEST_DB)
    if p.exists():
        p.unlink()
except Exception:
    pass

# Initialize DB schema early so modules that import engines/sessions
# see the correct schema during test collection.
try:
    from services.api.app.db import init_db

    init_db()
except Exception:
    # If init fails, let pytest surface the error in test runs.
    pass

# Ensure SQLAlchemy model tables exist for tests that use SessionLocal/engine
try:
    from services.api.app import database, models

    # Create tables defined by SQLAlchemy models on the same engine used in tests
    try:
        models.Base.metadata.create_all(bind=database.engine)
    except Exception:
        pass
except Exception:
    pass
