from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_repo_path(*parts: str) -> str:
    return str((REPO_ROOT.joinpath(*parts)).resolve())


def _resolve_env_path(env_name: str, default_relative: str) -> str:
    raw_value = os.getenv(env_name)
    candidate = Path(raw_value) if raw_value else (REPO_ROOT / default_relative)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return str(candidate.resolve())


def apply_runtime_environment() -> Dict[str, str]:
    settings = {
        'repo_root': str(REPO_ROOT),
        'db_path': _resolve_env_path('TAAIP_DB_PATH', 'data/taaip.sqlite3'),
        'upload_dir': _resolve_env_path('TAAIP_UPLOAD_DIR', 'services/api/.data/imports'),
        'refresh_upload_dir': _resolve_env_path('TAAIP_REFRESH_UPLOAD_DIR', 'data/refresh_uploads'),
        'export_storage_dir': _resolve_env_path('EXPORT_STORAGE_DIR', 'data/exports'),
        'documents_path': _resolve_env_path('TAAIP_DOCUMENTS_PATH', 'data/documents'),
        'host': os.getenv('HOST', '127.0.0.1'),
        'port': os.getenv('PORT', '8000'),
        'frontend_dir': resolve_repo_path('taaip-dashboard'),
    }

    os.environ['TAAIP_DB_PATH'] = settings['db_path']
    os.environ.setdefault('DATABASE_URL', f"sqlite:///{settings['db_path']}")
    os.environ['TAAIP_UPLOAD_DIR'] = settings['upload_dir']
    os.environ['TAAIP_REFRESH_UPLOAD_DIR'] = settings['refresh_upload_dir']
    os.environ['EXPORT_STORAGE_DIR'] = settings['export_storage_dir']
    os.environ['TAAIP_DOCUMENTS_PATH'] = settings['documents_path']

    Path(settings['db_path']).parent.mkdir(parents=True, exist_ok=True)
    for key in ('upload_dir', 'refresh_upload_dir', 'export_storage_dir', 'documents_path'):
        Path(settings[key]).mkdir(parents=True, exist_ok=True)

    return settings


def runtime_preflight() -> Dict[str, Any]:
    settings = apply_runtime_environment()
    checks: List[Dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append({'name': name, 'status': 'ok' if ok else 'error', 'detail': detail})

    db_parent = Path(settings['db_path']).parent
    add_check('db_directory', db_parent.exists() and os.access(db_parent, os.W_OK), f"DB directory: {db_parent}")

    for env_key, setting_key in (
        ('TAAIP_UPLOAD_DIR', 'upload_dir'),
        ('TAAIP_REFRESH_UPLOAD_DIR', 'refresh_upload_dir'),
        ('EXPORT_STORAGE_DIR', 'export_storage_dir'),
        ('TAAIP_DOCUMENTS_PATH', 'documents_path'),
    ):
        target = Path(settings[setting_key])
        add_check(env_key.lower(), target.exists() and os.access(target, os.W_OK), f"Path: {target}")

    add_check('database_url', str(os.getenv('DATABASE_URL', '')).startswith('sqlite:///') or bool(os.getenv('DATABASE_URL')), os.getenv('DATABASE_URL', 'unset'))

    status = 'ok' if all(item['status'] == 'ok' for item in checks) else 'error'
    return {'status': status, 'settings': settings, 'checks': checks}
