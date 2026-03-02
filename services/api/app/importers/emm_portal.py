from datetime import datetime
from typing import List, Dict, Tuple


def _map_column_name(col: str) -> str:
    c = col.strip().upper()
    mapping = {
        'RSID': 'rsid',
        'UNIT': 'unit_name',
        'ACTIVITY ID': 'activity_id',
        'MAC': 'mac',
        'TITLE': 'title',
        'WHERE': 'where_text',
        'ACTIVITY TYPE': 'activity_type',
        'ACTIVITY STATUS': 'activity_status',
        'FY': 'fy',
        'BEGIN DATE': 'begin_date',
        'END DATE': 'end_date',
        'AAR_DUE': 'aar_due',
        'CONTROLLING_ACCOUNT': 'controlling_account'
    }
    return mapping.get(c, None)


def normalize_rows(df):
    cols = list(df.columns)
    mapped = {}
    for c in cols:
        mapped_name = _map_column_name(c)
        if mapped_name:
            mapped[c] = mapped_name
    rows = []
    errors = []
    for idx, r in df.iterrows():
        out = {}
        for orig_col, mapped_col in mapped.items():
            val = r.get(orig_col)
            if mapped_col == 'fy':
                try:
                    out['fy'] = int(val) if val not in (None, '', 'nan') else None
                except Exception:
                    try:
                        out['fy'] = int(str(val).strip())
                    except Exception:
                        out['fy'] = None
            elif mapped_col in ('begin_date','end_date','aar_due'):
                # try parse ISO-like dates, otherwise keep raw string
                try:
                    out[mapped_col] = val.strftime('%Y-%m-%d') if hasattr(val, 'strftime') else str(val) if val not in (None, '') else None
                except Exception:
                    out[mapped_col] = str(val) if val not in (None, '') else None
            else:
                out[mapped_col] = str(val).strip() if val not in (None, '') else None
        rows.append(out)
    return rows, errors


def process_and_load(df, ctx, conn, run_id):
    cur = conn.cursor()
    rows, errors = normalize_rows(df)
    inserted = 0
    for e in errors:
        cur.execute('INSERT INTO import_run_error_v2 (run_id, row_num, message) VALUES (?,?,?)', (run_id, e.get('row'), e.get('message')))
    for r in rows:
        try:
            # derive scope/time stamps
            unit = ctx.get('unit_rsid') or r.get('rsid') or None
            fy = r.get('fy') or ctx.get('scope_fy')
            qtr = r.get('qtr_num') or ctx.get('scope_qtr')
            # derive rsm_month from begin_date if present else from ctx
            rsm = None
            bd = r.get('begin_date') or r.get('start_date')
            try:
                if bd:
                    from datetime import datetime as _dt
                    dtd = _dt.fromisoformat(bd)
                    rsm = f"{dtd.year:04d}-{dtd.month:02d}"
                    if not fy:
                        # compute fy from date
                        from .. import scope as _scope
                        fy = _scope.compute_current_fy(dtd.date())
                    if not qtr:
                        from .. import scope as _scope
                        qtr = _scope.compute_current_qtr_num(dtd.date())
            except Exception:
                rsm = None

            cur.execute('INSERT INTO fact_emm_activity (activity_id, rsid, unit_rsid, unit_name, mac, title, where_text, activity_type, activity_status, fy, qtr_num, rsm_month, begin_date, end_date, start_date, aar_due, controlling_account, source_run_id, source_system) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                r.get('activity_id'), r.get('rsid'), unit, r.get('unit_name'), r.get('mac'), r.get('title'), r.get('where_text'), r.get('activity_type'), r.get('activity_status'), fy, qtr, rsm, r.get('begin_date'), r.get('end_date'), r.get('begin_date'), r.get('aar_due'), r.get('controlling_account'), run_id, ctx.get('source_system')
            ))
            inserted += 1
        except Exception as ex:
            cur.execute('INSERT INTO import_run_error_v2 (run_id, row_num, message) VALUES (?,?,?)', (run_id, None, f'load_error: {str(ex)}'))
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return inserted
