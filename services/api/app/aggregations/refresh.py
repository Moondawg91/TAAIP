import sqlite3
from datetime import datetime


def refresh_agg_kpis(conn: sqlite3.Connection, unit_rsid: str = None):
    """Simple KPI refresh: populate a small agg_kpis_period table with contract counts per unit/month."""
    cur = conn.cursor()
    # ensure table
    try:
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS agg_kpis_period (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_rsid TEXT,
            period TEXT,
            contracts INTEGER,
            updated_at TEXT
        );
        ''')
    except Exception:
        pass

    # recompute aggregates
    where = ''
    params = []
    if unit_rsid:
        where = 'WHERE f.unit_rsid = ?'
        params = [unit_rsid]
    try:
        cur.execute(f"SELECT f.unit_rsid, f.period_date, SUM(COALESCE(f.contracts,0)) as contracts FROM fact_enlistments f {where} GROUP BY f.unit_rsid, f.period_date", params)
        rows = cur.fetchall()
        for unit, period, contracts in rows:
            cur.execute('INSERT INTO agg_kpis_period (unit_rsid, period, contracts, updated_at) VALUES (?,?,?,?)', (unit, period, contracts, datetime.utcnow().isoformat()))
        conn.commit()
    except Exception:
        pass


def refresh_market_from_contracts(conn: sqlite3.Connection, batch_id: str = None, unit_rsid: str = None):
    """Lightweight best-effort transform: promote recently-loaded
    rows from `fact_market_share_contracts` into `market_zip_fact` and
    aggregated `market_cbsa_fact` where possible.

    This is intentionally conservative: it attempts to insert minimal
    columns so downstream dashboards can surface newly-uploaded markets.
    Returns number of zip-level rows inserted.
    """
    import uuid
    cur = conn.cursor()
    try:
        params = []
        where = ''
        if batch_id:
            where = 'WHERE batch_id = ?'
            params = [batch_id]
        cur.execute(f"SELECT fy, per, rsid, zip, contracts, share, totpop, imported_at, mkt FROM fact_market_share_contracts {where}", params)
        rows = cur.fetchall()
        if not rows:
            return 0

        inserted = 0
        cbsa_agg = {}
        for r in rows:
            try:
                fy, per, rsid, zipv, contracts, share, totpop, imported_at, mkt = r
            except Exception:
                vals = list(r) + [None] * 9
                fy, per, rsid, zipv, contracts, share, totpop, imported_at, mkt = vals[:9]

            try:
                zip5 = (zipv or '')
                if zip5 and len(zip5) > 5:
                    zip5 = zip5[:5]
                if zip5 and len(zip5) < 5:
                    zip5 = zip5.zfill(5)
            except Exception:
                zip5 = None

            try:
                fqma = int(totpop) if totpop is not None else None
            except Exception:
                fqma = None
            try:
                contracts_i = int(contracts) if contracts is not None else None
            except Exception:
                contracts_i = None
            try:
                army_share = float(share) if share is not None else None
            except Exception:
                army_share = None

            potential_remaining = None
            try:
                if fqma is not None and contracts_i is not None:
                    potential_remaining = max(0, fqma - contracts_i)
            except Exception:
                potential_remaining = None

            p2p = None
            try:
                if fqma and contracts_i is not None and fqma > 0:
                    p2p = float(contracts_i) / float(fqma)
            except Exception:
                p2p = None

            now = imported_at or datetime.utcnow().isoformat()
            mid = f"mz_{uuid.uuid4().hex}"

            # attempt insert into common market_zip_fact shape; tolerant to missing columns
            try:
                cur.execute("INSERT INTO market_zip_fact(id, fy, qtr, rsid_prefix, zip5, cbsa_code, market_category, fqma, army_share, potential_remaining, p2p, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (mid, fy, per, rsid, zip5, None, 'SU', fqma, army_share, potential_remaining, p2p, now))
                inserted += 1
            except Exception:
                try:
                    cur.execute("INSERT INTO market_zip_fact(id, fy, qtr, rsid_prefix, zip, cbsa_code, market_category, fqma, army_share, potential_remaining, p2p, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                (mid, fy, per, rsid, zip5, None, 'SU', fqma, army_share, potential_remaining, p2p, now))
                    inserted += 1
                except Exception:
                    continue

            # best-effort cbsa aggregation (if cbsa present)
            try:
                cbsa = None
                if cbsa:
                    ag = cbsa_agg.get(cbsa) or {'fqma': 0, 'contracts': 0, 'potential': 0, 'shares': []}
                    ag['fqma'] = (ag['fqma'] or 0) + (fqma or 0)
                    ag['contracts'] = (ag['contracts'] or 0) + (contracts_i or 0)
                    ag['potential'] = (ag['potential'] or 0) + (potential_remaining or 0)
                    if army_share is not None:
                        ag['shares'].append(army_share)
                    cbsa_agg[cbsa] = ag
            except Exception:
                pass

        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        cbsa_written = 0
        for cbsa, vals in cbsa_agg.items():
            try:
                cid = f"mc_{uuid.uuid4().hex}"
                avg_share = (sum(vals['shares']) / len(vals['shares'])) if vals['shares'] else None
                cur.execute("INSERT INTO market_cbsa_fact(id, fy, qtr, rsid_prefix, cbsa_code, cbsa_name, fqma, contracts, army_share, potential_remaining, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (cid, None, None, None, cbsa, None, vals['fqma'], vals['contracts'], avg_share, vals['potential'], datetime.utcnow().isoformat()))
                cbsa_written += 1
            except Exception:
                continue
        try:
            if cbsa_written:
                conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        return inserted
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return 0


def refresh_mission_from_category(conn: sqlite3.Connection, batch_id: str = None, unit_rsid: str = None):
    """Promote recent `fact_mission_category` rows into a mission_allocation run.

    Creates a lightweight mission_allocation run with `mission_total` equal
    to the sum of metric values found for the given batch. Returns the
    created run_id or None on error.
    """
    try:
        # lazy import to avoid cycles
        from services.api.app.services import mission_allocation_engine
    except Exception:
        mission_allocation_engine = None

    cur = conn.cursor()
    try:
        params = []
        where = ''
        if batch_id:
            where = 'WHERE ingest_run_id = ?'
            params = [batch_id]
        # select metric_value (legacy schema) or value if present in other variants
        # avoid referencing non-existent columns to prevent SQL errors
        try:
            cur.execute(f"SELECT mission_category, metric_value as val FROM fact_mission_category {where}", params)
        except Exception:
            cur.execute(f"SELECT mission_category, value as val FROM fact_mission_category {where}", params)
        rows = cur.fetchall()
        if not rows:
            return None

        total = 0
        for r in rows:
            try:
                v = r[1]
                if v is None or v == '':
                    continue
                total += float(v)
            except Exception:
                continue

        if total <= 0:
            return None

        # create run via engine if available, else insert directly
        run_id = None
        try:
            if mission_allocation_engine:
                run_id = mission_allocation_engine.create_run(unit_rsid or 'USAREC', int(total), notes=f'Imported mission data from {batch_id}')
            else:
                now = datetime.utcnow().isoformat()
                rid = f"mal_{uuid.uuid4().hex}"
                cur.execute('INSERT INTO mission_allocation_runs (run_id, unit_rsid, mission_total, status, notes, created_at) VALUES (?,?,?,?,?,?)', (rid, unit_rsid or 'USAREC', int(total), 'created', f'Imported mission data from {batch_id}', now))
                conn.commit()
                run_id = rid
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return None

        return run_id
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return None


def refresh_org_hierarchy(conn: sqlite3.Connection, batch_id: str = None, unit_rsid: str = None):
    """Normalize recently-loaded org_unit rows so org endpoints return expected fields.

    Ensures `rsid`, `display_name`, and `unit_key` columns exist (populated
    from `unit_rsid`/`name`) and normalizes empty parent_rsid to NULL.
    Returns number of rows touched.
    """
    cur = conn.cursor()
    touched = 0
    try:
        # add rsid/display_name/unit_key columns if missing
        cur.execute("PRAGMA table_info('org_unit')")
        cols = [r[1] for r in cur.fetchall()]
        try:
            if 'rsid' not in cols:
                cur.execute('ALTER TABLE org_unit ADD COLUMN rsid TEXT')
        except Exception:
            pass
        try:
            if 'display_name' not in cols:
                cur.execute('ALTER TABLE org_unit ADD COLUMN display_name TEXT')
        except Exception:
            pass
        try:
            if 'unit_key' not in cols:
                cur.execute('ALTER TABLE org_unit ADD COLUMN unit_key TEXT')
        except Exception:
            pass

        # populate from common columns
        try:
            cur.execute("UPDATE org_unit SET rsid = unit_rsid WHERE (rsid IS NULL OR rsid = '') AND (unit_rsid IS NOT NULL AND unit_rsid != '')")
            cur.execute("UPDATE org_unit SET display_name = name WHERE (display_name IS NULL OR display_name = '') AND (name IS NOT NULL AND name != '')")
            cur.execute("UPDATE org_unit SET unit_key = unit_rsid WHERE (unit_key IS NULL OR unit_key = '') AND (unit_rsid IS NOT NULL AND unit_rsid != '')")
        except Exception:
            pass

        # normalize parent_rsid blanks to NULL
        try:
            cur.execute("UPDATE org_unit SET parent_rsid = NULL WHERE parent_rsid = ''")
        except Exception:
            pass

        try:
            touched = cur.execute('SELECT COUNT(1) FROM org_unit').fetchone()[0] or 0
        except Exception:
            touched = 0

        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        return touched
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return 0


def refresh_all_analytics(conn: sqlite3.Connection, unit_rsid: str = None):
    """Best-effort trigger to refresh higher-level analytics engines.

    This function attempts to run school-targeting, market-health and mission-risk
    recomputations where sensible inputs can be derived from canonical tables.
    It is defensive and will swallow errors so it is safe to call after imports.
    """
    try:
        # lazy imports to avoid circular deps
        from services.api.app.services import school_targeting, market_health_engine, mission_risk_engine
    except Exception:
        return

    cur = conn.cursor()
    # 1) School targeting: if a schools table exists, sample schools to score
    try:
        try:
            cur.execute("SELECT school_id, enrollment, access_score, historical_production FROM school_program_fact LIMIT 200")
            rows = cur.fetchall()
            if rows:
                payloads = []
                for r in rows:
                    try:
                        sid = r[0]
                        enrollment = r[1] if r[1] is not None else 0
                        access = r[2] if r[2] is not None else 0.0
                        hist = r[3] if r[3] is not None else 0
                        payloads.append({'school_id': sid, 'enrollment': enrollment, 'access_score': access, 'historical_production': hist})
                    except Exception:
                        continue
                try:
                    school_targeting.compute_school_targets(payloads, persist=True, unit_rsid=unit_rsid)
                except Exception:
                    pass
        except Exception:
            # fallback: handle legacy/alternative school_program_fact shapes
            try:
                cur.execute("SELECT rsid_prefix, population, available FROM school_program_fact LIMIT 200")
                rows = cur.fetchall()
                if rows:
                    payloads = []
                    for r in rows:
                        try:
                            sid = r[0]
                            population = r[1] if r[1] is not None else 0
                            available = r[2] if r[2] is not None else 0
                            access = (float(available) / float(population)) if population and population > 0 else 0.0
                            payloads.append({'school_id': sid, 'enrollment': population, 'access_score': access, 'historical_production': 0})
                        except Exception:
                            continue
                    try:
                        school_targeting.compute_school_targets(payloads, persist=True, unit_rsid=unit_rsid)
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass

    # 2) Market health: sample market_potential rows and compute market health
    try:
        cur.execute("SELECT geographic_level, geographic_id, army_total_potential, army_contacted FROM market_potential LIMIT 200")
        rows = cur.fetchall()
        if rows:
            for r in rows:
                try:
                    mtype = r[0]
                    mid = r[1]
                    total = r[2] or 0
                    contacted = r[3] or 0
                    # simple signals: market_load = contacted/total (if total>0)
                    market_load = float(contacted) / float(total) if total and total > 0 else 0.0
                    payload = {'market_type': mtype, 'market_id': mid, 'unit_rsid': unit_rsid, 'market_load': market_load}
                    try:
                        market_health_engine.compute_market_health(payload, persist=True)
                    except Exception:
                        pass
                except Exception:
                    continue
    except Exception:
        pass

    # 3) Mission risk: build minimal company inputs from companies table if present
    try:
        cur.execute("SELECT company_id, recruiter_capacity, historical_production FROM companies LIMIT 200")
        rows = cur.fetchall()
        inputs = []
        if rows:
            for r in rows:
                try:
                    cid = r[0]
                    capacity = r[1] if r[1] is not None else 1
                    hist = r[2] if r[2] is not None else 0
                    inputs.append({'company_id': cid, 'recruiter_capacity': capacity, 'historical_production': hist})
                except Exception:
                    continue
            if inputs:
                try:
                    mission_risk_engine.compute_mission_risks(inputs, persist=True, unit_rsid=unit_rsid)
                except Exception:
                    pass
    except Exception:
        pass
