#!/usr/bin/env python3
"""
Import script for Vantage CSV exports into the TAAIP refresh pipeline.

Usage:
  python services/api/tools/import_vantage_csv.py /path/to/vantage.csv

What it does:
  - normalizes headers
  - runs lightweight validation (required merge keys, numeric parsing)
  - maps known source fields to canonical TAAIP fields where possible
  - writes rows into `refresh_dataset_rows` via SQLAlchemy models
  - creates a `dataset_versions` record and `refresh_history`
  - preserves source name, version UUID, and audit records

This follows the same pattern as `seed_market_core.py` but adds validation
and normalization specific to Vantage exports.
"""
import os
import csv
import uuid
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

from services.api.app import database
from services.api.app.models_refresh import (
    RefreshSource,
    DatasetVersion,
    RefreshDatasetRow,
    RefreshHistory,
    DatasetActive,
)


def normalize_col(name: str) -> str:
    if not name:
        return name
    s = name.strip().lower()
    s = s.replace('%', 'pct')
    s = s.replace('#', 'num')
    s = s.replace(' ', '_')
    s = s.replace('-', '_')
    s = s.replace('/', '_')
    return s


def infer_numeric_fields(rows: List[Dict[str, Any]], threshold=0.6) -> List[str]:
    """Return list of columns that look numeric in the sample set."""
    counts = {}
    total = max(1, len(rows))
    for r in rows:
        for k, v in r.items():
            if v is None or v == '':
                continue
            try:
                float(str(v).replace(',', ''))
                counts[k] = counts.get(k, 0) + 1
            except Exception:
                pass
    return [k for k, c in counts.items() if (c / total) >= threshold]


def load_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        rows = []
        for r in reader:
            new = {normalize_col(k): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
            rows.append(new)
    return rows


def get_or_create_source(db, canonical_target='market_core_vantage') -> RefreshSource:
    src = db.query(RefreshSource).filter(RefreshSource.canonical_target == canonical_target).first()
    if src:
        return src

    # conservative default mapping/profile — lightweight
    mapping_profile = {
        'groups': {
            'identity': ['zip'],
            'demographic_metrics': [],
        },
        'validation': {
            'required_merge_keys': ['zip'],
        }
    }
    src = RefreshSource(
        name='Vantage Market Core (import_vantage_csv)',
        description='Imported Vantage CSV via import_vantage_csv.py',
        canonical_target=canonical_target,
        file_types='csv',
        required_merge_keys=['zip'],
        mapping_profile=mapping_profile,
        default_mode='replace',
        trusted='false',
        auto_commit='false'
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    return src


def validate_rows(rows: List[Dict[str, Any]], required_merge_keys: List[str]) -> Dict[str, Any]:
    total = len(rows)
    missing_merge = 0
    bad_numeric = 0
    numeric_fields = infer_numeric_fields(rows)
    errors = []

    for i, r in enumerate(rows, start=1):
        # merge key(s)
        for key in required_merge_keys:
            if not r.get(key):
                missing_merge += 1
                errors.append({'row': i, 'error': f'missing_merge_key:{key}'})
        # numeric parsing
        for nf in numeric_fields:
            v = r.get(nf)
            if v in (None, ''):
                continue
            try:
                float(str(v).replace(',', ''))
            except Exception:
                bad_numeric += 1
                errors.append({'row': i, 'error': f'invalid_numeric:{nf}', 'value': v})

    summary = {
        'total_rows': total,
        'missing_merge_key_count': missing_merge,
        'invalid_numeric_count': bad_numeric,
        'numeric_fields_inferred': numeric_fields,
        'errors_sample': errors[:10]
    }
    return summary


def map_row_to_canonical(row: Dict[str, Any], mapping_profile: Dict[str, Any]) -> Dict[str, Any]:
    # Simple mapping strategy: if mapping_profile contains group->list of field names,
    # preserve normalized keys and return a canonicalized dict. For unknown fields, keep them.
    mapped = dict(row)
    # Example: ensure 'zip' is present as string
    if 'zip' in mapped:
        mapped['zip'] = str(mapped['zip']).zfill(5) if mapped['zip'] else mapped['zip']
    return mapped


def persist_dataset(db, src: RefreshSource, rows: List[Dict[str, Any]], source_filename: str, notes: str = '') -> Dict[str, Any]:
    ver = DatasetVersion(
        source_id=src.id,
        version=str(uuid.uuid4()),
        created_by='import_vantage_csv',
        row_count=len(rows),
        notes=notes or f'Imported from {source_filename} at {datetime.utcnow().isoformat()}'
    )
    db.add(ver)
    db.commit()
    db.refresh(ver)

    # insert refresh_dataset_rows
    for r in rows:
        rdr = RefreshDatasetRow(source_id=src.id, version_id=ver.id, row_json=r)
        db.add(rdr)
    db.commit()

    # create refresh history (applied commit)
    hist = RefreshHistory(job_id=None, version_id=ver.id, mode=src.default_mode or 'replace', status='applied', applied_by='import_vantage_csv', row_count_before=0, row_count_after=len(rows), notes='import commit')
    db.add(hist)
    db.commit()

    # set active dataset
    act = db.query(DatasetActive).filter(DatasetActive.source_id == src.id).first()
    if not act:
        act = DatasetActive(source_id=src.id, version_id=ver.id, bound_by='import_vantage_csv')
        db.add(act)
    else:
        act.version_id = ver.id
        act.bound_by = 'import_vantage_csv'
    db.commit()

    return {'version_id': ver.id, 'version': ver.version}


def main():
    parser = argparse.ArgumentParser(description='Import Vantage CSV into TAAIP refresh pipeline')
    parser.add_argument('csv_path', help='Path to Vantage CSV file')
    parser.add_argument('--canonical', default='market_core_vantage', help='Refresh source canonical target')
    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv_path)
    if not os.path.exists(csv_path):
        print(f'ERROR: file not found: {csv_path}')
        return

    # load rows
    rows = load_csv(csv_path)
    print(f'Loaded {len(rows)} rows from {csv_path}')

    # ensure DB schema exists
    try:
        from services.api.app.db import init_db
        init_db()
    except Exception:
        pass

    Session = database.SessionLocal
    db = Session()
    try:
        src = get_or_create_source(db, canonical_target=args.canonical)

        required_merge_keys = src.required_merge_keys or ['zip']

        validation = validate_rows(rows, required_merge_keys)
        print('\nValidation Summary:')
        print(json.dumps(validation, indent=2))

        # persist mapped rows only if no missing merge keys
        if validation['missing_merge_key_count'] > 0:
            print('\nAborting load: missing required merge keys. Fix source and retry.')
            return

        mapped_rows = [map_row_to_canonical(r, src.mapping_profile or {}) for r in rows]

        res = persist_dataset(db, src, mapped_rows, os.path.basename(csv_path), notes=f'Imported via import_vantage_csv from {csv_path}')

        print('\nPersisted dataset:')
        print(json.dumps(res, indent=2))

        # save validation artifact
        art_dir = os.path.join(os.getcwd(), 'artifacts')
        os.makedirs(art_dir, exist_ok=True)
        out_path = os.path.join(art_dir, f'vantage_import_validation_{res.get("version")}.json')
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps({'validation': validation, 'persist': res}, indent=2))
        print(f'Wrote validation artifact: {out_path}')

    finally:
        db.close()


if __name__ == '__main__':
    main()
