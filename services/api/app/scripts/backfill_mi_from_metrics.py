"""Backfill canonical Market-Intel tables (`mi_zip_fact`, `mi_cbsa_fact`) from
`market_zip_metrics`/`market_zip_fact` for local deterministic completion.

Idempotent: uses INSERT OR REPLACE with deterministic IDs so repeated runs are safe.
"""
from services.api.app.db import connect
import sqlite3
from datetime import datetime


def _now_iso():
    return datetime.utcnow().isoformat() + 'Z'


def backfill(conn):
    cur = conn.cursor()

    # ensure source exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_zip_metrics'")
    if not cur.fetchone():
        print('NO_SOURCE_TABLE')
        return

    # determine columns available in market_zip_metrics
    cur.execute("PRAGMA table_info('market_zip_metrics')")
    cols = [r[1] for r in cur.fetchall()]
    has_cbsa = 'cbsa_code' in cols or 'cbsa' in cols
    zip_col = 'zip5' if 'zip5' in cols else ('zip' if 'zip' in cols else None)

    # read rows
    sel_cols = []
    for c in ('zip5','zip','cbsa_code','cbsa','population','potential_remaining','contracts_vol','p2p_value','opportunity_score','as_of_date'):
        if c in cols:
            sel_cols.append(c)
    q = f"SELECT {', '.join(sel_cols)} FROM market_zip_metrics"
    cur.execute(q)
    rows = cur.fetchall()

    now = _now_iso()
    # backfill mi_zip_fact
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mi_zip_fact'")
    has_mi_zip = True if cur.fetchone() else False
    if has_mi_zip:
        for r in rows:
            row = dict(r)
            z = row.get('zip5') or row.get('zip')
            if not z:
                continue
            as_of = row.get('as_of_date') or None
            fy = None
            try:
                if as_of:
                    fy = str(datetime.fromisoformat(as_of).year)
            except Exception:
                try:
                    fy = str(as_of[:4])
                except Exception:
                    fy = str(datetime.utcnow().year)
            fy = fy or str(datetime.utcnow().year)
            mid = f"mi_bfill_zip_{z}_{fy}"
            potential = row.get('potential_remaining') or 0
            contracts = row.get('contracts_vol') or 0
            p2p = row.get('p2p_value') or row.get('p2p') or 0
            # use opportunity_score as army_potential proxy if available
            army_potential = row.get('opportunity_score') if 'opportunity_score' in row else None
            cur.execute("INSERT OR REPLACE INTO mi_zip_fact(id, fy, qtr, component, rsid_prefix, zip5, station_name, market_category, army_potential, dod_potential, army_share_of_potential, potential_remaining, contracts_ga, contracts_sa, contracts_vol, p2p, as_of_date, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                mid, fy, None, None, None, z, None, None, army_potential, None, None, float(potential), None, None, int(contracts), float(p2p), as_of, now
            ))
        conn.commit()

    # backfill mi_cbsa_fact by aggregating cbsa if present; fallback to market_zip_fact if metrics lack cbsa
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mi_cbsa_fact'")
    has_mi_cbsa = True if cur.fetchone() else False
    if has_mi_cbsa:
        agg = {}
        # prefer cbsa from market_zip_metrics rows if present
        for r in rows:
            row = dict(r)
            cb = row.get('cbsa_code') or row.get('cbsa')
            if not cb:
                continue
            as_of = row.get('as_of_date') or None
            try:
                fy = str(datetime.fromisoformat(as_of).year) if as_of else str(datetime.utcnow().year)
            except Exception:
                fy = str(as_of[:4]) if as_of else str(datetime.utcnow().year)
            key = (cb, fy)
            rec = agg.get(key, {'population':0, 'potential':0, 'contracts':0, 'p2ps':[]})
            rec['population'] += int(row.get('population') or 0)
            rec['potential'] += float(row.get('potential_remaining') or 0)
            rec['contracts'] += int(row.get('contracts_vol') or 0)
            p2 = row.get('p2p_value') or row.get('p2p')
            if p2 is not None:
                try:
                    rec['p2ps'].append(float(p2))
                except Exception:
                    pass
            agg[key] = rec

        # if no cbsa found in metrics, try market_zip_fact for cbsa hints
        if not agg:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_zip_fact'")
            if cur.fetchone():
                cur.execute('SELECT cbsa_code, fy, SUM(COALESCE(market_potential,0)) as population, SUM(COALESCE(potential_remaining,0)) as potential, SUM(COALESCE(contracts_total,0)) as contracts, AVG(COALESCE(p2p,0)) as p2p_avg FROM market_zip_fact GROUP BY cbsa_code, fy')
                for r in cur.fetchall():
                    if not r[0]:
                        continue
                    cb = r[0]
                    fy = str(r[1]) if r[1] else str(datetime.utcnow().year)
                    key = (cb, fy)
                    agg[key] = {'population': int(r[2] or 0), 'potential': float(r[3] or 0), 'contracts': int(r[4] or 0), 'p2ps': [float(r[5] or 0)]}

        for (cb, fy), vals in agg.items():
            mid = f"mi_bfill_cbsa_{cb}_{fy}"
            avg_p2p = sum(vals['p2ps'])/len(vals['p2ps']) if vals['p2ps'] else 0
            cur.execute("INSERT OR REPLACE INTO mi_cbsa_fact(id, fy, qtr, component, rsid_prefix, cbsa_code, cbsa_name, market_category, army_potential, dod_potential, army_share_of_potential, potential_remaining, contracts_ga, contracts_sa, contracts_vol, p2p, as_of_date, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                mid, fy, None, None, None, cb, None, None, None, None, None, float(vals['potential']), None, None, int(vals['contracts']), float(avg_p2p), None, now
            ))
        conn.commit()

    print('BACKFILL_OK')


if __name__ == '__main__':
    conn = connect()
    try:
        backfill(conn)
    finally:
        conn.close()
