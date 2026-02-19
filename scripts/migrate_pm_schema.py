#!/usr/bin/env python3
"""
Migration helper to add missing Project Management schema columns to the SQLite DB.

Usage: python3 scripts/migrate_pm_schema.py [--db ./data/recruiting.db]
"""
import argparse
import sqlite3
from typing import List


def ensure_columns(conn: sqlite3.Connection, table: str, cols: List[str]):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    existing = [r[1] for r in cur.fetchall()]
    for c in cols:
        if c not in existing:
            print(f"Adding column {c} to {table}")
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {c} TEXT")
    conn.commit()


def ensure_budget_txn_columns(conn: sqlite3.Connection):
    cur = conn.cursor()
    # create table if missing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS budget_transactions (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            date TEXT,
            type TEXT,
            description TEXT,
            amount REAL,
            category TEXT
        )
        """
    )
    conn.commit()
    # ensure expected columns
    cur.execute("PRAGMA table_info(budget_transactions)")
    existing = [r[1] for r in cur.fetchall()]
    additions = []
    for c in ("txn_id", "created_at"):
        if c not in existing:
            additions.append(c)
    for c in additions:
        print(f"Adding column {c} to budget_transactions")
        cur.execute(f"ALTER TABLE budget_transactions ADD COLUMN {c} TEXT")
    conn.commit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="./data/recruiting.db")
    args = p.parse_args()

    db = args.db
    print(f"Opening DB: {db}")
    conn = sqlite3.connect(db)

    # participants
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            person_id TEXT,
            role TEXT,
            unit TEXT,
            attendance INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    ensure_columns(conn, "participants", ["participant_id", "created_at"])

    # budget transactions
    ensure_budget_txn_columns(conn)

    # roi_records
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS roi_records (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            calculated_at TEXT,
            cost_total REAL,
            benefit_est REAL,
            roi REAL
        )
        """
    )
    conn.commit()
    ensure_columns(conn, "roi_records", ["roi_id", "total_spent", "computed_at"])

    # emm_mappings
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS emm_mappings (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            emm_event_id TEXT,
            raw_payload TEXT
        )
        """
    )
    conn.commit()
    ensure_columns(conn, "emm_mappings", ["mapping_id", "source_id", "payload", "created_at"])

    # projects optional columns
    cur.execute("PRAGMA table_info(projects)")
    existing = [r[1] for r in cur.fetchall()]
    for c, ddl in (
        ("funding_amount", "REAL DEFAULT 0"),
        ("spent_amount", "REAL DEFAULT 0"),
        ("metadata", "TEXT DEFAULT NULL"),
    ):
        if c not in existing:
            print(f"Adding column {c} to projects")
            cur.execute(f"ALTER TABLE projects ADD COLUMN {c} {ddl}")
    conn.commit()

    print("Migration complete.")
    conn.close()


if __name__ == "__main__":
    main()
