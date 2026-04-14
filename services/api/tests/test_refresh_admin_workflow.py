import base64
import json
import os
import sqlite3

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from services.api.app import database
from services.api.app.main import app
from services.api.app.runtime_env import runtime_preflight


def _jwt_like(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{header}.{body}.signature"


def _setup_db(tmp_path):
    db_path = str(tmp_path / "taaip_refresh_admin.db")
    os.environ["TAAIP_DB_PATH"] = db_path
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["LOCAL_DEV_AUTH_BYPASS"] = "0"
    os.environ["TAAIP_MASTER_MODE"] = "0"
    try:
        database.reload_engine_if_needed()
    except Exception:
        pass

    from services.api.app import db as app_db

    app_db.set_test_raw_conn(None)
    database.set_shared_session(None)
    database.SessionLocal = database.SessionProxy(
        sessionmaker(autocommit=False, autoflush=False, bind=database.engine)
    )

    app_db.init_schema()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS refresh_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            canonical_target TEXT,
            file_types TEXT,
            required_merge_keys TEXT,
            mapping_profile TEXT,
            owner TEXT,
            default_mode TEXT,
            trusted TEXT,
            auto_commit TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            filename TEXT,
            stored_path TEXT,
            checksum TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT,
            status TEXT,
            row_count INTEGER,
            profile TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_staging_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            row_number INTEGER,
            row_json TEXT
        );
        CREATE TABLE IF NOT EXISTS dataset_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            version TEXT,
            checksum TEXT,
            created_by TEXT,
            created_at TEXT,
            row_count INTEGER,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_dataset_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            version_id INTEGER,
            row_json TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            version_id INTEGER,
            mode TEXT,
            status TEXT,
            applied_by TEXT,
            applied_at TEXT,
            row_count_before INTEGER,
            row_count_after INTEGER,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS dataset_active (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER UNIQUE,
            version_id INTEGER,
            bound_at TEXT,
            bound_by TEXT
        );
        """
    )
    conn.commit()
    conn.close()
    return db_path


def test_refresh_requires_admin_role(tmp_path):
    _setup_db(tmp_path)
    client = TestClient(app)
    token = _jwt_like({"sub": "commander", "roles": ["station_user"], "permissions": [], "scopes": []})

    response = client.post(
        "/api/refresh/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Funnel Refresh", "canonical_target": "funnel_authoritative"},
    )

    assert response.status_code == 403


def test_refresh_upload_rejects_invalid_schema_with_structured_error(tmp_path):
    _setup_db(tmp_path)
    client = TestClient(app)
    token = _jwt_like({"sub": "admin", "roles": ["system_admin"], "permissions": ["admin.permissions.manage"], "scopes": []})

    source = client.post(
        "/api/refresh/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Market Core Refresh",
            "canonical_target": "market_core",
            "required_merge_keys": ["station_rsid", "zip_code"],
        },
    )
    assert source.status_code == 200
    source_id = source.json()["id"]

    bad_csv = "wrong_col,another\nA,1\nB,2\n"
    response = client.post(
        f"/api/refresh/sources/{source_id}/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("market_refresh.csv", bad_csv.encode(), "text/csv")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "invalid_schema"
    assert "station_rsid" in body["detail"]["missing_columns"]


def test_runtime_preflight_resolves_writable_paths(tmp_path, monkeypatch):
    monkeypatch.setenv('TAAIP_DB_PATH', str(tmp_path / 'ops.db'))
    monkeypatch.setenv('TAAIP_UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setenv('TAAIP_REFRESH_UPLOAD_DIR', str(tmp_path / 'refresh_uploads'))
    monkeypatch.setenv('EXPORT_STORAGE_DIR', str(tmp_path / 'exports'))
    monkeypatch.setenv('TAAIP_DOCUMENTS_PATH', str(tmp_path / 'documents'))

    status = runtime_preflight()

    assert status['status'] == 'ok'
    assert any(check['name'] == 'db_directory' and check['status'] == 'ok' for check in status['checks'])


def test_refresh_upload_rejects_empty_payload_without_rebinding_active_version(tmp_path):
    db_path = _setup_db(tmp_path)
    client = TestClient(app)
    token = _jwt_like({"sub": "admin", "roles": ["system_admin"], "permissions": ["admin.permissions.manage"], "scopes": []})

    source = client.post(
        "/api/refresh/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "School Contacts", "canonical_target": "school_contacts"},
    )
    assert source.status_code == 200
    source_id = source.json()["id"]

    response = client.post(
        f"/api/refresh/sources/{source_id}/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("school_contacts.csv", b"school_name\n", "text/csv")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "no_data"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dataset_active WHERE source_id = ?", (source_id,))
    assert cur.fetchone()[0] == 0
    conn.close()
