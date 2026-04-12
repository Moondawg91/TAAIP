"""One-shot script to register and seed the Vantage Market Core CSV
as a dataset in the refresh slice. Safe-first: creates a DatasetVersion
and sets it active (replace mode). Run from repository root with the
virtualenv active.

This script performs the minimum necessary backend inserts to make the
`market_core_vantage` source available to the new market_core router.
It preserves audit tables (`refresh_history`, `dataset_versions`) and
does not touch domain tables.
"""
import os
import csv
import uuid
from services.api.app import database
from services.api.app.models_refresh import RefreshSource, RefreshJob, DatasetVersion, RefreshDatasetRow, RefreshHistory, DatasetActive


# prefer repository-root `uploads/` folder; when executed as a module cwd
# is normally repo root so this resolves correctly in both CLI and tests
CSV_PATH = os.path.abspath(os.path.join(os.getcwd(), 'uploads', '6L MARKET CORE.csv'))


def load_rows(path):
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        return [r for r in reader]


def main():
    rows = load_rows(CSV_PATH)
    print(f"Loaded {len(rows)} rows from {CSV_PATH}")

    # Ensure DB schema exists and SQLAlchemy engine targets the same DB path
    try:
        from services.api.app.db import init_db
        init_db()
    except Exception:
        pass

    Session = database.SessionLocal
    db = Session()
    try:
        # register source if missing
        src = db.query(RefreshSource).filter(RefreshSource.canonical_target == 'market_core_vantage').first()
        if not src:
            mapping_profile = {
                'groups': {
                    'identity': ['zip'],
                    'enlisted_assignment': [
                        'enlisted_begin_effective_date','enlisted_end_effective_date','rsid_enlisted','rsid_enlisted_station','rsid_enlisted_company','rsid_enlisted_battalion','rsid_enlisted_brigade','rsid_enlisted_command','lduic_enlisted_station','lduic_enlisted_company','lduic_enlisted_battalion','uic_enlisted_brigade','uic_enlisted_command'
                    ],
                    'medical_assignment': [
                        'medical_begin_effective_date','medical_end_effective_date','rsid_medical','rsid_medical_station','rsid_medical_company','rsid_medical_battalion','rsid_medical_brigade','rsid_medical_command','lduic_medical_station','lduic_medical_company','lduic_medical_battalion','uic_medical_brigade','uic_medical_command'
                    ],
                    'chaplain_assignment': [
                        'chaplain_begin_effective_date','chaplain_end_effective_date','rsid_chaplain','rsid_chaplain_station','rsid_chaplain_company','rsid_chaplain_battalion','rsid_chaplain_brigade','rsid_chaplain_command','lduic_chaplain_station','lduic_chaplain_company','lduic_chaplain_battalion','uic_chaplain_brigade','uic_chaplain_command'
                    ],
                    'demographic_metrics': list(rows[0].keys())
                },
                'validation': {
                    'required_merge_keys': ['zip'],
                    'require_assignment_chain': True,
                }
            }
            src = RefreshSource(
                name='Vantage Market Core',
                description='Vantage Market Core ZIP-level market data',
                canonical_target='market_core_vantage',
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
            print(f"Registered source id={src.id}")
        else:
            print(f"Source already registered id={src.id}")

        # create a dataset version and populate rows
        ver = DatasetVersion(
            source_id=src.id,
            version=str(uuid.uuid4()),
            created_by='seed_market_core',
            row_count=len(rows),
            notes='Seeded from uploads/6L MARKET CORE.csv'
        )
        db.add(ver)
        db.commit()
        db.refresh(ver)
        print(f"Created dataset_version id={ver.id}")

        # bulk insert refresh_dataset_rows
        for r in rows:
            rdr = RefreshDatasetRow(source_id=src.id, version_id=ver.id, row_json=r)
            db.add(rdr)
        db.commit()
        print(f"Inserted {len(rows)} refresh_dataset_rows for version_id={ver.id}")

        # create refresh history record
        hist = RefreshHistory(job_id=None, version_id=ver.id, mode='replace', status='applied', applied_by='seed_market_core', row_count_before=0, row_count_after=len(rows), notes='seed commit')
        db.add(hist)
        db.commit()

        # set dataset active
        act = db.query(DatasetActive).filter(DatasetActive.source_id == src.id).first()
        if not act:
            act = DatasetActive(source_id=src.id, version_id=ver.id, bound_by='seed_market_core')
            db.add(act)
        else:
            act.version_id = ver.id
            act.bound_by = 'seed_market_core'
        db.commit()
        print(f"Set dataset_active for source_id={src.id} -> version_id={ver.id}")

    finally:
        db.close()


if __name__ == '__main__':
    main()
