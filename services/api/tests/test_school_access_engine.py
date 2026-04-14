from sqlalchemy import text

from services.api.app import database
from services.api.app.services import school_access


def _db():
    return next(database.get_db())


def test_school_access_no_dataset_status():
    payload = school_access.summarize_school_access(_db(), "STN", "ZZZZ", "USAREC", "USAREC")
    assert payload["status"] in {"no_active_dataset", "invalid_dataset_schema"}


def test_school_access_valid_summary():
    db = _db()
    db.execute(text("DROP TABLE IF EXISTS schools"))
    db.execute(
        text(
            """
            CREATE TABLE schools (
              school_id TEXT,
              school_name TEXT,
              station_rsid TEXT,
              zip_code TEXT,
              enrollment INTEGER,
              created_at TEXT
            )
            """
        )
    )
    db.execute(
        text(
            "INSERT INTO schools(school_id, school_name, station_rsid, zip_code, enrollment, created_at) "
            "VALUES(:id, :name, :station, :zip, :enrollment, datetime('now'))"
        ),
        {"id": "S1", "name": "Alpha HS", "station": "A123", "zip": "11111", "enrollment": 900},
    )
    db.execute(
        text(
            "INSERT INTO schools(school_id, school_name, station_rsid, zip_code, enrollment, created_at) "
            "VALUES(:id, :name, :station, :zip, :enrollment, datetime('now'))"
        ),
        {"id": "S2", "name": "Bravo HS", "station": "A123", "zip": "11112", "enrollment": 600},
    )
    db.commit()

    payload = school_access.summarize_school_access(_db(), "STN", "A123", "USAREC", "USAREC")
    assert payload["status"] == "ok"
    assert "summary" in payload["school_access"]
    assert isinstance(payload["school_access"]["top_access_gaps"], list)
