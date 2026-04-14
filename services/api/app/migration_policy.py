import os


LEGACY_MIGRATION_COMMAND = "./.venv/bin/python -m alembic -c services/api/alembic.ini upgrade head"


def legacy_schema_bootstrap_enabled() -> bool:
    return os.getenv("TAAIP_ALLOW_LEGACY_SCHEMA_BOOTSTRAP", "0") == "1"


def legacy_bootstrap_message(source: str) -> str:
    return (
        f"{source} is deprecated for schema management. "
        "Alembic under services/api/alembic is the single migration source of truth. "
        f"Run `{LEGACY_MIGRATION_COMMAND}` instead. "
        "Set TAAIP_ALLOW_LEGACY_SCHEMA_BOOTSTRAP=1 only for isolated test/bootstrap workflows."
    )


def legacy_script_message(source: str) -> str:
    return (
        f"{source} is a deprecated legacy migration script and is blocked by default. "
        "Alembic under services/api/alembic is the single migration source of truth. "
        f"Run `{LEGACY_MIGRATION_COMMAND}` instead. "
        "Set TAAIP_ALLOW_LEGACY_MIGRATIONS=1 only to replay historical scripts intentionally."
    )