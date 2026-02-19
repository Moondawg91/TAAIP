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
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_shared_session = None


def set_shared_session(sess):
    global _shared_session
    _shared_session = sess


def reload_engine_if_needed():
    """Recreate the SQLAlchemy engine if `DATABASE_URL` env changed since import.

    Call this after changing `DATABASE_URL` in tests or fixtures so the module's
    `engine` and `SessionLocal` reflect the current environment.
    """
    global engine, SessionLocal
    desired = os.getenv("DATABASE_URL") or "sqlite:///./taaip_dev.db"
    try:
        current_url = str(engine.url)
    except Exception:
        current_url = None
    if current_url != desired:
        engine = _create_engine_from_env()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
