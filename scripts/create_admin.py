#!/usr/bin/env python3
"""
Create or update an administrator user in the SQLite DB at /opt/TAAIP/recruiting.db.

This script safely:
- backs up the DB to /opt/TAAIP/recruiting.db.bak.<ts>
- generates a cryptographically-strong salt
- computes SHA-256(password + salt)
- inserts the admin user if the username does not already exist

Usage (run as root or a user that can write the DB):
  sudo python3 /opt/TAAIP/scripts/create_admin.py --username admin --email admin@taaip.mil --password admin123

If user exists, the script prints the existing user info (without password/hash).
"""

import argparse
import datetime
import hashlib
import os
import secrets
import shutil
import sqlite3
import sys


DB_PATH = "/opt/TAAIP/recruiting.db"


def backup_db(db_path: str) -> str:
    ts = int(datetime.datetime.utcnow().timestamp())
    dst = f"{db_path}.bak.{ts}"
    shutil.copy2(db_path, dst)
    return dst


def user_exists(conn: sqlite3.Connection, username: str) -> bool:
    cur = conn.execute("SELECT COUNT(1) FROM users WHERE username = ?", (username,))
    r = cur.fetchone()
    return bool(r and r[0])


def create_admin(conn: sqlite3.Connection, username: str, email: str, password: str, first_name: str, last_name: str, role: str, tier: int):
    now = datetime.datetime.utcnow().isoformat()
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    # Default values for optional columns if present
    start_date = now
    end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat()
    rank = 'O-6'

    # Insert required columns; use INSERT OR IGNORE to avoid duplicates
    conn.execute(
        '''INSERT OR IGNORE INTO users
        (username, email, password_hash, password_salt, first_name, last_name, rank, role, tier, start_date, end_date, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (username, email, password_hash, salt, first_name, last_name, rank, role, tier, start_date, end_date, 1, now, now)
    )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Create an admin user in the TAAIP recruiting.db")
    parser.add_argument("--db", default=DB_PATH, help="Path to SQLite DB (default: /opt/TAAIP/recruiting.db)")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--first-name", default="Admin")
    parser.add_argument("--last-name", default="User")
    parser.add_argument("--role", default="administrator")
    parser.add_argument("--tier", type=int, default=1)

    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}")
        sys.exit(2)

    print(f"Backing up DB {args.db}...")
    bak = backup_db(args.db)
    print(f"Backup created: {bak}")

    conn = sqlite3.connect(args.db)
    try:
        # quick sanity check: ensure users table exists
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            print("ERROR: 'users' table not found in DB.")
            sys.exit(3)

        if user_exists(conn, args.username):
            print(f"User '{args.username}' already exists — no changes made.")
            cur = conn.execute("SELECT id, username, email, first_name, last_name, role, tier, is_active FROM users WHERE username = ?", (args.username,))
            print("Existing user:")
            for row in cur.fetchall():
                print(row)
            return

        create_admin(conn, args.username, args.email, args.password, args.first_name, args.last_name, args.role, args.tier)
        print(f"Inserted admin user '{args.username}' (password was provided on command line). Change password on first login.")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
