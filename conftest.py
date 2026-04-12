import os
import pathlib
import tempfile
import uuid
import importlib
import atexit


# Create a session-unique temporary SQLite DB file to avoid cross-test
# contention. This file will be used for the whole pytest session and
# removed at the end. Using an absolute temp path avoids using the
# repo-local ./data/ file which can be shared by other processes.
_tmp_dir = tempfile.gettempdir()
_unique = uuid.uuid4().hex
TEST_DB_PATH = pathlib.Path(_tmp_dir) / f"taaip_test_{_unique}.db"
# Export DB path and SQLAlchemy URL for all modules to use.
os.environ['TAAIP_DB_PATH'] = str(TEST_DB_PATH)
os.environ['DATABASE_URL'] = f"sqlite:///{TEST_DB_PATH}"
# Default: disable WAL on problematic filesystems during tests
os.environ['TAAIP_DISABLE_WAL'] = '1'

def _init_test_db():
    """Reload the app database layer and create tables for the test DB."""
    try:
        # If the database module was already imported, reload it so it picks up
        # the overridden DATABASE_URL/TAAIP_DB_PATH and recreates the engine.
        if 'services.api.app.database' in globals() or 'services.api.app.database' in __import__('sys').modules:
            importlib.reload(__import__('services.api.app.database', fromlist=['*']))
        # Trigger DB init helpers if present (some modules define init helpers)
        try:
            from services.api.app import db as app_db
            try:
                # best-effort init hook
                app_db.init_db()
            except Exception:
                pass
        except Exception:
            pass
        # ensure SQLAlchemy model tables exist on the newly-created engine
        try:
            from services.api.app import database, models
            models.Base.metadata.create_all(bind=database.engine)
        except Exception:
            pass
    except Exception:
        pass


_init_test_db()


def _cleanup_test_db():
    # Remove the temporary DB file when the test session/process exits.
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except Exception:
        pass


# Register cleanup for when pytest or the interpreter exits
atexit.register(_cleanup_test_db)


def _safe_import_db_module():
    try:
        return importlib.import_module('services.api.app.database')
    except Exception:
        return None


import pytest


@pytest.fixture(autouse=True)
def _close_db_between_tests():
    """Autouse fixture that runs after each test to ensure DB sessions
    and engine connections are closed/disposed. This reduces the
    likelihood of lingering locks between tests.
    """
    yield
    dbmod = _safe_import_db_module()
    if not dbmod:
        return
    try:
        # clear any shared session reference
        if hasattr(dbmod, 'set_shared_session'):
            try:
                dbmod.set_shared_session(None)
            except Exception:
                pass
    except Exception:
        pass
    try:
        # dispose engine connections (best-effort)
        if hasattr(dbmod, 'engine') and dbmod.engine is not None:
            try:
                dbmod.engine.dispose()
            except Exception:
                pass
    except Exception:
        pass

