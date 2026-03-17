import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

def _create_engine_from_env():
    # Prefer explicit test DB path when present so the engine follows
    # `TAAIP_DB_PATH` used by the test harness. Fall back to DATABASE_URL.
    taaip_path = os.getenv("TAAIP_DB_PATH")
    if taaip_path:
        DATABASE_URL = f"sqlite:///{taaip_path}"
    else:
        DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./taaip_dev.db"
    if DATABASE_URL.startswith("sqlite"):
        eng = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=NullPool)

        @event.listens_for(eng, "connect")
        def _sqlite_pragmas(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                    cursor.execute("PRAGMA foreign_keys=ON;")
                    cursor.execute("PRAGMA busy_timeout=10000;")
                finally:
                    cursor.close()
    else:
        eng = create_engine(DATABASE_URL)
    return eng


# Create engine/session at import-time but allow re-creation if env changes.
engine = _create_engine_from_env()
_shared_session = None


class SessionProxy:
    """A stable proxy around a SQLAlchemy sessionmaker.

    This object allows test modules that import `SessionLocal` early to
    retain a reference that can later be configured to return a shared
    session (used by the pytest transactional fixture) or produce new
    sessions from an internal sessionmaker.
    """
    def __init__(self, maker):
        self._maker = maker

    def __call__(self):
        # If a shared session was installed by tests, return it so all
        # callers operate on the same Session instance.
        global _shared_session
        if _shared_session is not None:
            return _shared_session
        return self._maker()

    def configure(self, **kwargs):
        return self._maker.configure(**kwargs)

    def __getattr__(self, name):
        return getattr(self._maker, name)


SessionLocal = SessionProxy(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def set_shared_session(sess):
    global _shared_session
    _shared_session = sess




def reload_engine_if_needed():
    """Recreate the SQLAlchemy engine if `DATABASE_URL` env changed since import.

    Call this after changing `DATABASE_URL` in tests or fixtures so the module's
    `engine` and `SessionLocal` reflect the current environment.
    """
    global engine, SessionLocal
    # Respect TAAIP_DB_PATH if set (tests use this), otherwise fall back to
    # DATABASE_URL or the default. This mirrors `_create_engine_from_env()`
    # so reloads use the same computed URL as engine creation.
    taaip_path = os.getenv("TAAIP_DB_PATH")
    if taaip_path:
        desired = f"sqlite:///{taaip_path}"
    else:
        desired = os.getenv("DATABASE_URL") or "sqlite:///./taaip_dev.db"
    try:
        current_url = str(engine.url)
    except Exception:
        current_url = None
    if current_url != desired:
        engine = _create_engine_from_env()
        # If SessionLocal is our proxy type, update its internal maker so
        # existing references continue to work. Otherwise, replace it.
        try:
            if isinstance(SessionLocal, SessionProxy):
                SessionLocal._maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            else:
                SessionLocal = SessionProxy(sessionmaker(autocommit=False, autoflush=False, bind=engine))
        except Exception:
            SessionLocal = SessionProxy(sessionmaker(autocommit=False, autoflush=False, bind=engine))
        # Ensure SQLAlchemy model metadata exists on the newly-created engine.
        try:
            # Import here to avoid import-time cycles when module is imported elsewhere.
            from services.api.app import models as _models
            try:
                _models.Base.metadata.create_all(bind=engine)
            except Exception:
                pass
        except Exception:
            pass


def get_db():
    # When running tests we may set a shared session so FastAPI handlers
    # and test code operate on the exact same SQLAlchemy Session instance.
    global _shared_session
    # Ensure the engine and SessionLocal reflect any env changes made by tests
    reload_engine_if_needed()
    if _shared_session is not None:
        yield _shared_session
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
