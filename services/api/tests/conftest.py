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
            # Ensure the SQLAlchemy engine is reloaded to reflect the updated DATABASE_URL
            try:
                if hasattr(database, 'reload_engine_if_needed'):
                    database.reload_engine_if_needed()
            except Exception:
                pass
            models.Base.metadata.create_all(bind=database.engine)
        except Exception:
            pass
        # Best-effort: ensure marketing_activities has the canonical set of columns
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(marketing_activities)")
            cols = [r[1] for r in cur.fetchall()]
            if 'activity_id' not in cols:
                try:
                    cur.executescript('''
                    PRAGMA foreign_keys=OFF;
                    CREATE TABLE IF NOT EXISTS marketing_activities_new (
                        activity_id TEXT PRIMARY KEY,
                        event_id TEXT,
                        activity_type TEXT,
                        campaign_name TEXT,
                        channel TEXT,
                        data_source TEXT,
                        impressions INTEGER DEFAULT 0,
                        engagement_count INTEGER DEFAULT 0,
                        awareness_metric REAL,
                        activation_conversions INTEGER DEFAULT 0,
                        reporting_date TEXT,
                        metadata TEXT,
                        cost REAL DEFAULT 0,
                        created_at TEXT,
                        import_job_id TEXT,
                        record_status TEXT DEFAULT 'active'
                    );
                    INSERT OR IGNORE INTO marketing_activities_new(activity_id,event_id,activity_type,campaign_name,channel,data_source,impressions,engagement_count,awareness_metric,activation_conversions,reporting_date,metadata,cost,created_at,import_job_id,record_status)
                        SELECT COALESCE(activity_id, CAST(id AS TEXT)), event_id, activity_type, campaign_name, channel, data_source, impressions, engagement_count, awareness_metric, activation_conversions, reporting_date, metadata, cost, created_at, import_job_id, record_status FROM marketing_activities;
                    DROP TABLE IF EXISTS marketing_activities;
                    ALTER TABLE marketing_activities_new RENAME TO marketing_activities;
                    PRAGMA foreign_keys=ON;
                    ''' )
                except Exception:
                    pass
            conn.commit()
            conn.close()
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


@pytest.fixture(autouse=True)
def transactional_tests():
    """Run each test inside a transaction and rollback after completion.

    This preserves module-level setup (tables created in setup_module)
    while isolating test data changes so repeated deterministic inserts
    don't collide across tests.
    """
    from services.api.app import database
    from sqlalchemy.orm import sessionmaker

    # Keep original SessionLocal to restore after the test
    orig_SessionLocal = database.SessionLocal
    conn = database.engine.connect()
    # Start a top-level transaction that will be rolled back after the test
    trans = conn.begin()
    # Ensure raw sqlite3 callers used by the app share the same DB-API
    # connection so commits are visible inside the active test transaction.
    try:
        from services.api.app import db as app_db
        raw_conn = conn.connection
        app_db.set_test_raw_conn(raw_conn)
    except Exception:
        pass
    # Create a single Session instance bound to the connection and ensure
    # SessionLocal() returns that same session object. This makes both the
    # test code and the FastAPI request handlers share the same ORM session,
    # avoiding visibility/isolation issues.
    Session = sessionmaker(autocommit=False, autoflush=False, bind=conn)
    shared_session = Session()
    # start a SAVEPOINT so test can rollback without interfering with outer
    # transaction semantics when nested session commits occur inside request handlers
    try:
        shared_session.begin_nested()
        from sqlalchemy import event

        @event.listens_for(shared_session, "after_transaction_end")
        def restart_savepoint(sess, trans):
            # If the nested transaction ended, open a new nested transaction
            # to maintain isolation for the duration of the test.
            if trans.nested and not sess.is_active:
                try:
                    sess.begin_nested()
                except Exception:
                    pass
    except Exception:
        pass
    # Provide a proxy object so `database.SessionLocal.configure(...)` still works
    class SessionProxy:
        def __init__(self, maker, shared):
            self._maker = maker
            self._shared = shared

        def __call__(self):
            return self._shared

        def configure(self, **kwargs):
            return self._maker.configure(**kwargs)

        def __getattr__(self, name):
            return getattr(self._maker, name)

    proxy = SessionProxy(Session, shared_session)
    database.SessionLocal = proxy
    try:
        # expose shared session to FastAPI dependency via helper
        from services.api.app import database as dbmod
        dbmod.set_shared_session(shared_session)
    except Exception:
        pass
    try:
        yield
    finally:
        # Restore original SessionLocal and rollback outer transaction
        try:
            # close shared session if present
            try:
                shared_session.close()
            except Exception:
                pass
        except Exception:
            pass
        # clear shared session hook
        try:
            from services.api.app import database as dbmod
            dbmod.set_shared_session(None)
        except Exception:
            pass
        database.SessionLocal = orig_SessionLocal
        try:
            from services.api.app import db as app_db
            app_db.set_test_raw_conn(None)
        except Exception:
            pass
        try:
            trans.rollback()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
