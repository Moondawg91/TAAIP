#!/usr/bin/env python3
"""Integration test: POST a small projects CSV to the upload endpoint and verify DB count.

Usage:
  TARGET_URL=http://localhost:8000 TARGET_DB=/path/to/recruiting.db python3 scripts/integration_test_upload.py
"""
import os
import sys
import time
import sqlite3
import requests

TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:8000")
UPLOAD_URL = f"{TARGET_URL}/api/v2/upload/projects?replace=true"
TARGET_DB = os.environ.get("TARGET_DB")  # optional: path to sqlite DB to verify


CSV_CONTENT = """project_id,name,status,created_at
test_proj_001,Integration Project 1,in_progress,2025-01-01T00:00:00Z
test_proj_002,Integration Project 2,completed,2025-01-02T00:00:00Z
"""


def write_tmp_csv(path):
    with open(path, "w") as fh:
        fh.write(CSV_CONTENT)


def post_csv(path):
    files = {"file": (os.path.basename(path), open(path, "rb"), "text/csv")}
    try:
        resp = requests.post(UPLOAD_URL, files=files, timeout=30)
        return resp
    except Exception as e:
        print("ERROR: request failed:", e)
        return None


def check_db_count(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM projects")
        n = cur.fetchone()[0]
        conn.close()
        return n
    except Exception as e:
        print("ERROR: DB check failed:", e)
        return None


def main():
    tmp = "/tmp/taaip_integration_projects.csv"
    write_tmp_csv(tmp)
    print("Posting CSV to:", UPLOAD_URL)
    resp = post_csv(tmp)
    if resp is None:
        print("Request failed.")
        sys.exit(2)

    print("HTTP", resp.status_code)
    try:
        data = resp.json()
    except Exception:
        print("Non-JSON response:\n", resp.text)
        sys.exit(2)

    print("Response:", data)
    if resp.status_code != 200 or data.get("status") != "success":
        print("Upload did not report success.")
        sys.exit(3)

    if TARGET_DB:
        # give server a moment to commit
        time.sleep(1)
        n = check_db_count(TARGET_DB)
        print("Projects in DB:", n)
        if n is None:
            sys.exit(4)
        # Expect at least 2 projects
        if n < 2:
            print("Unexpected project count (<2)")
            sys.exit(5)

    print("Integration test passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
