from services.api.app import database
from services.api.app.db import connect
from services.api.app.services import forecasting, what_if


def _db():
    return next(database.get_db())


def test_forecasting_and_what_if_shapes():
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS station_zip_coverage")
    cur.execute("DROP TABLE IF EXISTS market_category_weights")
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
    cur.execute("INSERT INTO station_zip_coverage(station_rsid, zip_code, market_category, source_file, created_at) VALUES('D456','45678','MK','test',datetime('now'))")
    conn.commit()
    conn.close()

    proj = forecasting.project_scope(_db(), "STN", "D456", assumptions={"mission_delta": 0.1})
    assert "projected_feasibility" in proj
    assert "projected_production_range" in proj

    wi = what_if.run_what_if(_db(), "STN", "D456", {"scenario_name": "surge", "effort_shift": 0.2})
    assert wi["scenario_name"] == "surge"
