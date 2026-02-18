from backend.routers.imports import load_table_from_file, canonicalize_columns, classify_profile, ensure_fact_tables, load_usarec_market, load_usarec_zip_category, load_dod_org_hierarchy
from backend.routers.imports import _connect, _utc_now
import sqlite3, json, traceback

def process_import(batch_id: str, stored_path: str):
    try:
        db = _connect()
        cur = db.cursor()
        cur.execute("UPDATE raw_import_batches SET status=? WHERE batch_id=?", ("processing", batch_id))
        db.commit()

        df_proc, meta_proc = load_table_from_file(stored_path)
        df_proc = df_proc.dropna(how="all")
        df_proc.columns = [str(c).strip() for c in df_proc.columns]
        canonical_cols, _ = canonicalize_columns(list(df_proc.columns))
        prof, _ = classify_profile(set(canonical_cols))

        ensure_fact_tables(db)
        if prof == "USAREC_MARKET_CONTRACTS_SHARE":
            load_usarec_market(db, df_proc, batch_id)
        elif prof == "USAREC_ZIP_CATEGORY":
            load_usarec_zip_category(db, df_proc, batch_id)
        elif prof == "DOD_ORG_HIERARCHY":
            load_dod_org_hierarchy(db, df_proc, batch_id)

        cur.execute("UPDATE raw_import_batches SET status=? WHERE batch_id=?", ("done", batch_id))
        db.commit()
        db.close()
    except Exception as e:
        try:
            cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("error", str(e), batch_id))
            db.commit()
            db.close()
        except Exception:
            pass
        traceback.print_exc()
*** End Patch