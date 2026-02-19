import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

def _create_engine_from_env():
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
