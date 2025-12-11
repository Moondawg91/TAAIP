#!/usr/bin/env python3
"""Safely back up DB and update/insert an admin user's password.

Usage:
  sudo python3 /opt/TAAIP/scripts/update_admin_password.py admin
  (script will prompt for password interactively)

This script:
 - Makes a timestamped copy of the SQLite DB before changing anything
 - Generates a random salt and SHA256(password + salt)
 - Updates password_hash and password_salt for existing user, or inserts
   a minimal administrator record if user does not exist.
"""
import argparse
import datetime
import getpass
import hashlib
import os
import shutil
import secrets
import sqlite3
import sys


DEFAULT_DB = "/opt/TAAIP/recruiting.db"


def backup_db(db_path: str) -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dest = f"{db_path}.bak.{ts}"
    shutil.copy2(db_path, dest)
    return dest


def compute_hash(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def upsert_admin(db_path: str, username: str, password: str) -> None:
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found at {db_path}")
        sys.exit(2)

    print("Backing up DB...")
    bak = backup_db(db_path)
    print(f"Backup written to: {bak}")

    salt = secrets.token_hex(16)
    password_hash = compute_hash(password, salt)
    now = datetime.datetime.utcnow().isoformat()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check if user exists
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    row = cur.fetchone()

    if row:
        user_id = row[0]
        print(f"Updating password for existing user id={user_id} (username={username})")
        cur.execute(
            """
            UPDATE users
            SET password_hash=?, password_salt=?, updated_at=?
            WHERE id=?
            """,
            (password_hash, salt, now, user_id),
        )
    else:
        print(f"User '{username}' not found — inserting minimal administrator row")
        cur.execute(
            """
            INSERT INTO users (username, email, password_hash, password_salt, role, tier, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                f"{username}@taaip.mil",
                password_hash,
                salt,
                "administrator",
                1,
                1,
                now,
                now,
            ),
        )

    conn.commit()
    conn.close()
    print("Password update complete.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("username", help="username to update (e.g. admin)")
    p.add_argument("--db", default=DEFAULT_DB, help="path to SQLite DB")
    p.add_argument("--password", help="password (unsafe — prefer interactive)")
    args = p.parse_args()

    if args.password:
        password = args.password
    else:
        password = getpass.getpass(prompt=f"Enter new password for '{args.username}': ")
        confirm = getpass.getpass(prompt="Confirm password: ")
        if password != confirm:
            print("Passwords do not match — aborting")
            sys.exit(3)

    try:
        upsert_admin(args.db, args.username, password)
    except Exception as e:
        print("ERROR: failed to update DB:", e)
        sys.exit(4)


if __name__ == "__main__":
    main()
