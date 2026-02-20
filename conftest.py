import os
import pathlib

# Ensure tests run with a deterministic test DB set before any imports
TEST_DB = './taaip_test.db'
# Force override so modules import the correct DB path
os.environ['TAAIP_DB_PATH'] = TEST_DB
os.environ['DATABASE_URL'] = f"sqlite:///{TEST_DB}"

# Remove an old test DB if present to ensure a clean slate
try:
    p = pathlib.Path(TEST_DB)
    if p.exists():
        p.unlink()
except Exception:
    pass

import importlib

# Initialize DB schema early so modules that import engines/sessions
# see the correct schema during test collection.
try:
    # If the database module was already imported, reload it so it picks up
    # the overridden DATABASE_URL above and recreates the engine.
    if 'services.api.app.database' in globals() or 'services.api.app.database' in __import__('sys').modules:
        importlib.reload(__import__('services.api.app.database', fromlist=['*']))
    from services.api.app import database, db
    # call init_schema/init_db to create raw tables
    try:
        db.init_db()
    except Exception:
        pass
    # ensure SQLAlchemy model tables exist on the engine used by the app
    try:
        from services.api.app import models
        models.Base.metadata.create_all(bind=database.engine)
    except Exception:
        pass
except Exception:
    pass
