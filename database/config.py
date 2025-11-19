"""
Database Configuration for TAAIP 2.0
Supports PostgreSQL, SQL Server, and SQLite (dev only)
"""
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool, QueuePool
import logging

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()

# Database URL from environment or default to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', 'data', 'taaip.sqlite3')}"
)

# Determine database type
DB_TYPE = "sqlite"
if DATABASE_URL.startswith("postgresql"):
    DB_TYPE = "postgresql"
elif DATABASE_URL.startswith("mssql"):
    DB_TYPE = "sqlserver"

logger.info(f"Initializing database connection: {DB_TYPE}")

# Engine configuration based on database type
engine_kwargs = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
    "future": True,
}

if DB_TYPE == "sqlite":
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = NullPool
else:
    # For PostgreSQL/SQL Server, use connection pooling
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "20"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    engine_kwargs["pool_pre_ping"] = True  # Verify connections before using
    engine_kwargs["pool_recycle"] = 3600  # Recycle connections after 1 hour
    engine_kwargs["poolclass"] = QueuePool

# Create engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency for FastAPI to get database session.
    Use with: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database schema - creates all tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db_health() -> dict:
    """Check database connection health"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "database_type": DB_TYPE,
            "connection": "active"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database_type": DB_TYPE,
            "error": str(e)
        }


# Migration helper functions
def get_current_db_path() -> Optional[str]:
    """Get path to current SQLite database (for migration)"""
    if DB_TYPE == "sqlite":
        import re
        match = re.search(r'sqlite:///(.+)$', DATABASE_URL)
        if match:
            return match.group(1)
    return None


def is_migration_needed() -> bool:
    """Check if we need to migrate from SQLite to PostgreSQL"""
    return (
        os.getenv("MIGRATE_FROM_SQLITE", "false").lower() == "true"
        and DB_TYPE == "postgresql"
    )
