import sqlite3
from backend.ingestion.loaders.sama_loader import load_sama


def test_sama_loader_basic(tmp_path):
    csv = tmp_path / "sama.csv"
    csv.write_text("ZIP CODE,STATION,SAMA SCORE\n27587,3J3H - WAKE FOREST,85.2\n")

    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE sama_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zip_code TEXT,
            station TEXT,
            sama_score REAL,
            batch_id TEXT,
            created_at TEXT
        );
        """
    )
    con.commit()

    batch_id = "test_batch_sama"
    load_sama(con, str(csv), batch_id)

    cur.execute("SELECT zip_code, station, sama_score, batch_id FROM sama_data WHERE batch_id=?", (batch_id,))
    rows = cur.fetchall()
    assert len(rows) == 1
    zipv, station, score, bid = rows[0]
    assert zipv == "27587"
    assert "WAKE FOREST" in station
    assert abs(score - 85.2) < 0.001
