#!/usr/bin/env python3
"""Archive and purge staging rows from fact_enlistments_bn.

Usage examples:
  python scripts/archive_staging.py --dry-run
  python scripts/archive_staging.py --retention-days 7
  python scripts/archive_staging.py --commit-run run_20260306_041436_65d47a

Behavior:
 - Finds candidate `source_run_id` values in `fact_enlistments_bn`.
 - By default, selects runs that have a committed canonical `ingest_run_id` in
   `fact_enlistments` or are older than `--retention-days`.
 - Exports staged rows for each selected run to `data/archive/fact_enlistments_bn_<run>.csv`.
 - Deletes exported rows from `fact_enlistments_bn` and VACUUMs the DB unless `--dry-run`.
"""
import argparse
import csv
import datetime
import os
import re
import sqlite3
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Archive and purge staging runs from fact_enlistments_bn")
    p.add_argument("--db-path", default=os.environ.get("TAAIP_DB_PATH", "data/taaip.sqlite3"))
    p.add_argument("--archive-dir", default="data/archive")
    p.add_argument("--retention-days", type=int, default=30,
                   help="Archive runs older than this many days (unless committed).")
    p.add_argument("--commit-run", help="Archive/delete only this specific source_run_id")
    p.add_argument("--dry-run", action="store_true", help="Don't delete or vacuum; just report and write CSVs")
    p.add_argument("--min-rows", type=int, default=1, help="Minimum rows required to consider archiving a run")
    return p.parse_args()


RUN_TS_RE = re.compile(r"run_(\d{8})_(\d{6})")


def run_timestamp_from_id(run_id: str):
    m = RUN_TS_RE.search(run_id)
    if not m:
        return None
    datepart, timepart = m.group(1), m.group(2)
    try:
        return datetime.datetime.strptime(datepart + timepart, "%Y%m%d%H%M%S")
    except Exception:
        return None


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def export_run(conn, run_id, archive_dir):
    cur = conn.cursor()
    cur.execute("SELECT * FROM fact_enlistments_bn WHERE source_run_id=?", (run_id,))
    rows = cur.fetchall()
    if not rows:
        return 0
    # get column names
    cols = [d[0] for d in cur.description]
    ensure_dir(archive_dir)
    safe_name = run_id.replace("/", "_")
    path = os.path.join(archive_dir, f"fact_enlistments_bn_{safe_name}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    return len(rows)


def main():
    args = parse_args()
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = None
    cur = conn.cursor()

    # gather staging runs and counts
    cur.execute("SELECT source_run_id, COUNT(*) FROM fact_enlistments_bn GROUP BY source_run_id")
    staging = cur.fetchall()
    if not staging:
        print("No staging runs found in fact_enlistments_bn.")
        return 0

    # which runs are committed in canonical table
    cur.execute("SELECT DISTINCT ingest_run_id FROM fact_enlistments")
    committed = {r[0] for r in cur.fetchall()}

    now = datetime.datetime.utcnow()
    candidates = []
    for run_id, cnt in staging:
        if cnt < args.min_rows:
            continue
        if args.commit_run:
            if run_id == args.commit_run:
                candidates.append((run_id, cnt))
            continue
        ts = run_timestamp_from_id(run_id)
        age_days = None
        if ts:
            age_days = (now - ts).days
        should = False
        if run_id in committed:
            should = True
        elif age_days is not None and age_days >= args.retention_days:
            should = True
        if should:
            candidates.append((run_id, cnt))

    if not candidates:
        print("No candidate runs to archive/delete.")
        return 0

    print(f"Found {len(candidates)} candidate runs to archive: {[r for r,_ in candidates]}")

    for run_id, cnt in candidates:
        print(f"Exporting run {run_id} ({cnt} rows) to CSV...")
        exported = export_run(conn, run_id, args.archive_dir)
        print(f"  exported {exported} rows for {run_id}")
        if not args.dry_run:
            print(f"  Deleting staging rows for {run_id}...")
            cur.execute("DELETE FROM fact_enlistments_bn WHERE source_run_id=?", (run_id,))
            conn.commit()
            print(f"  Deleted {cur.rowcount} rows for {run_id}")

    if not args.dry_run:
        print("VACUUMing database...")
        cur.execute("VACUUM")
        conn.commit()
        print("VACUUM complete.")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
