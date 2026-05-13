from pathlib import Path

from database import rsid_hierarchy
from services.api.scripts.import_org_units import connect_db, ensure_indexes, link_parents, upsert_rows
from services.api.scripts.seed_master_org_units import ensure_org_unit_table


def test_canonical_hierarchy_counts_match_master_csv():
    rows = rsid_hierarchy.get_org_unit_seed_rows()
    counts = {}
    for row in rows:
        counts[row["echelon"]] = counts.get(row["echelon"], 0) + 1

    assert counts == {
        "CMD": 1,
        "BDE": 5,
        "BN": 38,
        "CO": 241,
        "STN": 1314,
    }


def test_sample_hierarchy_path_uses_canonical_rows():
    path = rsid_hierarchy.get_full_hierarchy_path("1A1D")

    assert path is not None
    assert path["command"] == "USAREC"
    assert path["brigade"] == "1ST BDE"
    assert path["battalion"] == "1A"
    assert path["company"] == "1A1"
    assert path["station"] == "1A1D"
    assert path["station_name"] == "ALBANY"


def test_seed_rows_populate_org_unit_table(tmp_path: Path):
    db_path = tmp_path / "org.sqlite3"
    conn = connect_db(str(db_path))
    try:
        ensure_org_unit_table(conn)
        ensure_indexes(conn)
        rows = rsid_hierarchy.get_org_unit_seed_rows()
        stats = upsert_rows(conn, rows, "test_seed", dry_run=False)
        link_stats = link_parents(conn, dry_run=False)

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM org_unit")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM org_unit WHERE echelon='STN'")
        stations = cur.fetchone()[0]
        cur.execute("SELECT parent_rsid FROM org_unit WHERE rsid='1A1D'")
        station_parent = cur.fetchone()[0]
    finally:
        conn.close()

    assert stats["inserted"] == 1599
    assert stats["updated"] == 0
    assert stats["skipped"] == 0
    assert link_stats == {"linked": 1598, "failed": 0}
    assert total == 1599
    assert stations == 1314
    assert station_parent == "1A1"
