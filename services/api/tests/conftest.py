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
    # ensure DATABASE_URL env is consistent for SQLAlchemy engine
    os.environ.setdefault('DATABASE_URL', f"sqlite:///{db_path}")
    os.environ.setdefault('TAAIP_DB_PATH', db_path)

    # remove any leftover test DB for a fresh start
    try:
        p = pathlib.Path(db_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass

    # Import and initialize schema
    try:
        from services.api.app.db import init_db

        init_db()
    except Exception:
        # Let tests run; if init fails they'll fail with clear errors
        pass

    yield

    # session teardown: remove the test DB file
    try:
        p = pathlib.Path(db_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass
