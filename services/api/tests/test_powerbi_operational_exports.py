from fastapi.testclient import TestClient

from services.api.app.db import connect
from services.api.app.main import app


client = TestClient(app)


def test_powerbi_operational_dataset_shape():
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
    cur.execute("INSERT INTO station_zip_coverage(station_rsid, zip_code, market_category, source_file, created_at) VALUES('Z999','99999','MK','test',datetime('now'))")
    conn.commit()
    conn.close()

    r = client.get("/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("status") == "ok"
    data = payload.get("data", {})
    assert "market_qma_summary" in data
    assert "school_access_summary" in data
    assert "execution_quality_summary" in data
    assert "accountability" in data
