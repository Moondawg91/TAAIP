from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..runtime_env import apply_runtime_environment

SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    'market_core': {
        'merge_keys': ['station_rsid', 'zip_code'],
        'required_aliases': [
            ['station_rsid', 'rsid', 'station'],
            ['zip_code', 'zip', 'zip5'],
            ['market_category', 'category'],
            ['qma_population', 'population', 'market_population'],
        ],
        'downstream_surfaces': ['command-center', 'mission-adjustment', 'powerbi'],
    },
    'funnel_authoritative': {
        'merge_keys': ['lead_id'],
        'required_aliases': [
            ['lead_id', 'lead_key', 'prid'],
            ['current_stage', 'stage', 'to_stage'],
        ],
        'downstream_surfaces': ['command-center', 'mission-adjustment', 'execution', 'powerbi'],
    },
    'school_contacts': {
        'merge_keys': ['school_name', 'station_rsid'],
        'required_aliases': [
            ['school_name', 'school', 'school_id'],
            ['station_rsid', 'unit_rsid', 'org_unit_id', 'zip_code'],
        ],
        'downstream_surfaces': ['diagnostics', 'mission-adjustment', 'powerbi'],
    },
    'emm_portal': {
        'merge_keys': ['event_name', 'event_date'],
        'required_aliases': [
            ['event_name', 'event', 'event_id'],
            ['event_date', 'date', 'captured_at'],
        ],
        'downstream_surfaces': ['diagnostics', 'powerbi'],
    },
}


def ensure_refresh_schema(db: Session) -> None:
    statements = [
        '''CREATE TABLE IF NOT EXISTS refresh_sources (
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
        )''',
        '''CREATE TABLE IF NOT EXISTS refresh_jobs (
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
        )''',
        '''CREATE TABLE IF NOT EXISTS refresh_staging_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            row_number INTEGER,
            row_json TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS dataset_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            version TEXT,
            checksum TEXT,
            created_by TEXT,
            created_at TEXT,
            row_count INTEGER,
            notes TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS refresh_dataset_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            version_id INTEGER,
            row_json TEXT,
            created_at TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS refresh_history (
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
        )''',
        '''CREATE TABLE IF NOT EXISTS dataset_active (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER UNIQUE,
            version_id INTEGER,
            bound_at TEXT,
            bound_by TEXT
        )''',
    ]
    for statement in statements:
        db.execute(text(statement))
    db.commit()


def normalize_column(value: Any) -> str:
    return re.sub(r'[^a-z0-9]+', '_', str(value or '').strip().lower()).strip('_')


def resolve_source_key(canonical_target: Any = None, filename: str | None = None, columns: Sequence[Any] | None = None) -> str:
    explicit = normalize_column(canonical_target)
    if explicit in SOURCE_REGISTRY:
        return explicit

    filename_norm = normalize_column(filename)
    if 'market' in filename_norm:
        return 'market_core'
    if 'funnel' in filename_norm or 'lead' in filename_norm:
        return 'funnel_authoritative'
    if 'school' in filename_norm:
        return 'school_contacts'
    if 'emm' in filename_norm or 'portal' in filename_norm or 'event' in filename_norm:
        return 'emm_portal'

    normalized_columns = {normalize_column(column) for column in (columns or [])}
    for key, config in SOURCE_REGISTRY.items():
        if _matches_required_aliases(normalized_columns, config.get('required_aliases') or []):
            return key

    return explicit or 'generic_authoritative'


def default_merge_keys(source_key: str) -> List[str]:
    return list((SOURCE_REGISTRY.get(source_key) or {}).get('merge_keys') or [])


def _matches_required_aliases(normalized_columns: Iterable[str], required_aliases: Sequence[Sequence[str]]) -> bool:
    available = set(normalized_columns)
    if not required_aliases:
        return True
    for alias_group in required_aliases:
        if not any(normalize_column(alias) in available for alias in alias_group):
            return False
    return True


def validate_uploaded_frame(df: Any, canonical_target: Any = None, filename: str | None = None) -> Dict[str, Any]:
    apply_runtime_environment()
    columns = list(getattr(df, 'columns', [])) if df is not None else []
    normalized_columns = {normalize_column(column) for column in columns}
    row_count = int(len(df.index)) if df is not None and getattr(df, 'index', None) is not None else 0
    source_key = resolve_source_key(canonical_target=canonical_target, filename=filename, columns=columns)
    config = SOURCE_REGISTRY.get(source_key, {})

    missing_columns: List[str] = []
    for alias_group in config.get('required_aliases') or []:
        if not any(normalize_column(alias) in normalized_columns for alias in alias_group):
            missing_columns.append(alias_group[0])

    lineage = {
        'canonical_target': canonical_target,
        'detected_source': source_key,
        'filename': filename,
        'row_count_detected': row_count,
        'detected_columns': [str(column) for column in columns],
        'downstream_surfaces': config.get('downstream_surfaces') or [],
    }

    if row_count <= 0:
        return {
            'valid': False,
            'code': 'no_data',
            'message': 'The uploaded dataset did not contain any usable rows.',
            'missing_columns': missing_columns,
            'lineage': lineage,
        }

    if missing_columns:
        return {
            'valid': False,
            'code': 'invalid_schema',
            'message': 'The uploaded dataset is missing required authoritative columns.',
            'missing_columns': missing_columns,
            'lineage': lineage,
        }

    return {
        'valid': True,
        'code': 'validated',
        'message': 'Authoritative dataset validated successfully.',
        'missing_columns': [],
        'lineage': lineage,
        'merge_keys': default_merge_keys(source_key),
    }


def parse_profile(raw_profile: Any) -> Dict[str, Any]:
    if isinstance(raw_profile, dict):
        return raw_profile
    if isinstance(raw_profile, str) and raw_profile.strip():
        try:
            return json.loads(raw_profile)
        except Exception:
            return {'raw_profile': raw_profile}
    return {}


def build_error_detail(validation: Dict[str, Any], job_id: int | None = None) -> Dict[str, Any]:
    detail = {
        'code': validation.get('code') or 'refresh_failed',
        'message': validation.get('message') or 'Refresh validation failed.',
        'missing_columns': validation.get('missing_columns') or [],
        'lineage': validation.get('lineage') or {},
    }
    if job_id is not None:
        detail['job_id'] = job_id
    return detail
