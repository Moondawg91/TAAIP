import re
from typing import List, Dict, Tuple


def _find_bn_column(cols):
    for c in cols:
        if 'BATTALION' in c.upper() or 'BN' in c.upper() or 'LU_BATTALION' in c.upper():
            return c
    return None


def _find_enlistments_column(cols):
    for c in cols:
        if 'ENLIST' in c.upper() or 'ENLISTMENTS' in c.upper():
            return c
    return None


def _find_rsid_column(cols):
    for c in cols:
        # accept explicit 'rsid' or CBSA column as rsid for market-level files
        if c is None:
            continue
        if str(c).strip().lower() == 'rsid' or 'RSID' in str(c).upper():
            return c
    for c in cols:
        if str(c).strip().lower() == 'cbsa':
            return c
    return None


def normalize_rows(df):
    cols = list(df.columns)
    bn_col = _find_bn_column(cols)
    en_col = _find_enlistments_column(cols)
    rsid_col = _find_rsid_column(cols)

    if not rsid_col or not en_col:
        raise ValueError('required columns missing: rsid or enlistments')

    rows = []
    errors = []
    for idx, r in df.iterrows():
        try:
            rsid = str(r.get(rsid_col, '')).strip() if rsid_col else ''
            bn_name = str(r.get(bn_col, '')).strip() if bn_col else ''
            enlist_raw = r.get(en_col, None)
            try:
                # normalize string: remove commas/whitespace then coerce to int
                if enlist_raw in (None, '', 'nan'):
                    enlistments = None
                else:
                    s = str(enlist_raw).replace(',', '').strip()
                    if s == '':
                        enlistments = None
                    else:
                        enlistments = int(float(s))
            except Exception:
                # attempt to extract digits as a fallback
                m = re.search(r"(\d+)", str(enlist_raw))
                enlistments = int(m.group(1)) if m else None
            row = {
                'as_of_date': None,
                'bn_name': bn_name,
                'rsid': rsid,
                'enlistments': enlistments
            }
            rows.append(row)
        except Exception as e:
            errors.append({'row': idx+2, 'message': str(e)})
    return rows, errors


def process_and_load(df, ctx, conn, run_id):
    cur = conn.cursor()
    rows, errors = normalize_rows(df)
    inserted = 0
    for e in errors:
        cur.execute('INSERT INTO import_run_error_v2 (run_id, row_num, message) VALUES (?,?,?)', (run_id, e['row'], e['message']))
    for r in rows:
        try:
            # scope values: prefer ctx scope, fall back to parsed as_of_date
            unit = ctx.get('unit_rsid') or r.get('rsid')
            fy = None
            qtr = None
            rsm = None
            ad = r.get('as_of_date')
            try:
                if ad:
                    from datetime import datetime as _dt
                    dtd = _dt.fromisoformat(ad)
                    rsm = f"{dtd.year:04d}-{dtd.month:02d}"
                    from .. import scope as _scope
                    fy = _scope.compute_current_fy(dtd.date())
                    qtr = _scope.compute_current_qtr_num(dtd.date())
            except Exception:
                pass
            if fy is None:
                fy = ctx.get('scope_fy')
            if qtr is None:
                qtr = ctx.get('scope_qtr')
            if rsm is None:
                rsm = ctx.get('scope_rsm_month')

            cur.execute('INSERT INTO fact_enlistments_bn (as_of_date, bn_name, rsid, unit_rsid, enlistments, fy, qtr_num, rsm_month, source_run_id, source_system) VALUES (?,?,?,?,?,?,?,?,?,?)', (
                r.get('as_of_date'), r.get('bn_name'), r.get('rsid'), unit, r.get('enlistments'), fy, qtr, rsm, run_id, ctx.get('source_system')
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


def g2_cbsa_normalizer(df):
    """Canonical normalizer for CBSA enlistments.

    Returns: (rows, errors) where rows is list of dicts matching loader expectations.
    This mirrors normalize_rows() behavior but is exposed for registry/normalizer wiring.
    """
    return normalize_rows(df)
