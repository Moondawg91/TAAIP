import os
import pathlib

import pytest


def _test_db_path():
    # ensure tests use a disposable DB in the repo root
    return os.environ.get('TAAIP_DB_PATH', './taaip_test.db')


@pytest.fixture(scope='session', autouse=True)
def init_test_db():
    """Create a clean SQLite DB and initialize schema for the test session.

    This mirrors app startup behaviour and ensures tests have a consistent
    schema regardless of collection order.
    """
    db_path = _test_db_path()
    # force the test DB path so imports use this DB
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"
    os.environ['TAAIP_DB_PATH'] = db_path

    # remove any leftover test DB for a fresh start
    try:
        p = pathlib.Path(db_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass

    # Import and initialize schema
    # Re-import/reload DB modules so they honor the overridden DATABASE_URL
    try:
        import importlib, sys
        if 'services.api.app.db' in sys.modules:
            importlib.reload(sys.modules['services.api.app.db'])
        from services.api.app.db import init_db
        init_db()
        # Ensure SQLAlchemy model tables are created on the engine used by the app
        try:
            from services.api.app import database, models
            models.Base.metadata.create_all(bind=database.engine)
        except Exception:
            pass
    except Exception:
        # Let tests run; failures will be surfaced
        pass

    yield

    # session teardown: remove the test DB file
    try:
        p = pathlib.Path(db_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass
