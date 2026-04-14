from services.api.app import database
from services.api.app.db import connect
from services.api.app.services import accountability_engine


def _db():
    return next(database.get_db())


def test_accountability_returns_decision_ready_fields():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS station_zip_coverage")
    cur.execute("DROP TABLE IF EXISTS market_category_weights")
    cur.execute("DROP TABLE IF EXISTS schools")
    cur.execute("DROP TABLE IF EXISTS funnel_transitions")

    cur.execute(
        """
        CREATE TABLE station_zip_coverage(
          id INTEGER PRIMARY KEY,
          station_rsid TEXT,
          zip_code TEXT,
          market_category TEXT,
          source_file TEXT,
          created_at TEXT
        )
        """
    )
    cur.execute("CREATE TABLE market_category_weights(id INTEGER PRIMARY KEY, category TEXT, weight INTEGER)")
    cur.execute("INSERT INTO market_category_weights(category, weight) VALUES('MK', 5)")
    cur.execute("INSERT INTO station_zip_coverage(station_rsid, zip_code, market_category, source_file, created_at) VALUES('C345','34567','MK','test',datetime('now'))")

    cur.execute("CREATE TABLE schools(school_id TEXT, school_name TEXT, station_rsid TEXT, zip_code TEXT, enrollment INTEGER)")
    cur.execute("INSERT INTO schools VALUES('SCH1','Central HS','C345','34567',1000)")

    cur.execute("CREATE TABLE funnel_transitions(id TEXT, lead_key TEXT, station_rsid TEXT, from_stage TEXT, to_stage TEXT, transitioned_at TEXT, created_at TEXT)")
    cur.execute("INSERT INTO funnel_transitions VALUES('1','L1','C345','lead','prospect','2026-01-01T00:00:00Z','2026-01-01T00:00:00Z')")
    cur.execute("INSERT INTO funnel_transitions VALUES('2','L1','C345','prospect','test','2026-04-01T00:00:00Z','2026-04-01T00:00:00Z')")

    conn.commit()
    conn.close()

    data = accountability_engine.classify_scope(_db(), "STN", "C345")
    assert data["classification"] in {
        "market_constrained",
        "access_constrained",
        "effort_misaligned",
        "execution_failure",
        "leadership_or_training_issue",
        "balanced",
        "insufficient_data",
    }
    assert "recommended_next_action" in data
