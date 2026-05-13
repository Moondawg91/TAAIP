#!/usr/bin/env python3
"""Seed org_unit from the canonical USAREC master hierarchy CSV."""

import argparse
import sqlite3
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from database.rsid_hierarchy import CANONICAL_CSV_PATH, get_org_unit_seed_rows
from services.api.scripts.import_org_units import connect_db, ensure_indexes, get_db_path, link_parents, upsert_rows


def ensure_org_unit_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS org_unit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT
        )
        """
    )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed org_unit from the canonical USAREC hierarchy CSV")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--source", default="usarec_master_static")
    args = parser.parse_args()

    rows = get_org_unit_seed_rows()
    conn = connect_db(get_db_path())
    try:
        ensure_org_unit_table(conn)
        ensure_indexes(conn)
        stats = upsert_rows(conn, rows, args.source, dry_run=args.dry_run)
        link_stats = link_parents(conn, dry_run=args.dry_run)
    finally:
        conn.close()

    print(f"Canonical CSV: {CANONICAL_CSV_PATH}")
    print(f"Seed rows: {len(rows)}")
    print(
        "Upsert summary: "
        f"inserted={stats['inserted']} updated={stats['updated']} skipped={stats['skipped']}"
    )
    print(f"Parent linking: linked={link_stats['linked']} failed={link_stats['failed']}")
    return 0 if link_stats["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
