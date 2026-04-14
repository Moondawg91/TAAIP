from services.api.app import database
from services.api.app.db import connect
from services.api.app.services import execution_quality


def _db():
    return next(database.get_db())


def test_execution_quality_no_dataset_status():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS funnel_transitions")
    conn.commit()
    conn.close()

    payload = execution_quality.summarize_execution_quality(_db(), "USAREC", "USAREC", "USAREC", "USAREC")
    assert payload["status"] == "no_active_dataset"


def test_execution_quality_valid_summary():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS funnel_transitions")
    cur.execute(
        """
        CREATE TABLE funnel_transitions (
          id TEXT,
          lead_key TEXT,
          station_rsid TEXT,
          from_stage TEXT,
          to_stage TEXT,
          transitioned_at TEXT,
          created_at TEXT
        )
        """
    )
    cur.execute("INSERT INTO funnel_transitions VALUES(?,?,?,?,?,?,datetime('now'))", ("1", "L1", "B234", "lead", "prospect", "2026-01-01T00:00:00Z"))
    cur.execute("INSERT INTO funnel_transitions VALUES(?,?,?,?,?,?,datetime('now'))", ("2", "L1", "B234", "prospect", "enlist", "2026-02-15T00:00:00Z"))
    conn.commit()
    conn.close()

    payload = execution_quality.summarize_execution_quality(_db(), "STN", "B234", "USAREC", "USAREC")
    assert payload["status"] == "ok"
    assert payload["execution_quality"]["summary"]["avg_flash_to_bang"] >= 0
