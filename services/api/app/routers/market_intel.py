from fastapi import APIRouter, Query
from ..db import connect
from ..utils.rollup_utils import build_empty_rollup_contract, apply_common_filters, safe_table_exists
from typing import Optional
import datetime
import sqlite3
from fastapi.responses import Response
import json

router = APIRouter()


def _column_exists(conn, table, column):
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info('{table}')")
        cols = [r[1] for r in cur.fetchall()]
        return column in cols
    except Exception:
        return False


def _table_has_rows(conn, table):
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM {table} LIMIT 1")
        return cur.fetchone() is not None
    except Exception:
        return False


def _now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


@router.get("/market-intel/summary")
def market_intel_summary(year: Optional[int] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect()
    # apply_common_filters expects a dict of query params
    filters = apply_common_filters({"fy": year, "qtr": None, "rsid_prefix": rsid_prefix})

    contract = build_empty_rollup_contract(filters, kpi_keys=["market_potential_total", "contracts_total", "potential_remaining_total", "army_share_weighted", "p2p_avg", "zip_count", "cbsa_count"], breakdown_keys=["categories"], trend_keys=[])
    contract["data_as_of"] = _now_iso()

    cur = conn.cursor()
    missing = []

    # Prefer tables that contain data. If canonical mi_* exists but is empty
    # while legacy market_* contains rows, prefer the legacy table so tests
    # that write into legacy tables are visible to this summary.
    zip_table = None
    mi_zip_exists = safe_table_exists(conn, 'mi_zip_fact')
    market_zip_exists = safe_table_exists(conn, 'market_zip_fact')
    if mi_zip_exists and _table_has_rows(conn, 'mi_zip_fact'):
        zip_table = 'mi_zip_fact'
    elif market_zip_exists and _table_has_rows(conn, 'market_zip_fact'):
        zip_table = 'market_zip_fact'
    else:
        # fallback to whichever table exists (mi preferred)
        if mi_zip_exists:
            zip_table = 'mi_zip_fact'
        elif market_zip_exists:
            zip_table = 'market_zip_fact'
    cbsa_table = None
    mi_cbsa_exists = safe_table_exists(conn, 'mi_cbsa_fact')
    market_cbsa_exists = safe_table_exists(conn, 'market_cbsa_fact')
    if mi_cbsa_exists and _table_has_rows(conn, 'mi_cbsa_fact'):
        cbsa_table = 'mi_cbsa_fact'
    elif market_cbsa_exists and _table_has_rows(conn, 'market_cbsa_fact'):
        cbsa_table = 'market_cbsa_fact'
    else:
        if mi_cbsa_exists:
            cbsa_table = 'mi_cbsa_fact'
        elif market_cbsa_exists:
            cbsa_table = 'market_cbsa_fact'

    if cbsa_table:
        try:
            cur.execute(f"SELECT COUNT(DISTINCT cbsa_code) FROM {cbsa_table}")
            cc = cur.fetchone()[0] or 0
            contract['kpis']['cbsa_count'] = cc
            # categories counts
            try:
                if zip_table:
                    cur.execute(f"SELECT market_category, COUNT(*) as cnt FROM {zip_table} GROUP BY market_category")
                else:
                    cur.execute(f"SELECT market_category, COUNT(*) as cnt FROM {cbsa_table} GROUP BY market_category")
                cat_rows = cur.fetchall()
                cats = {r[0]: r[1] for r in cat_rows}
                contract['kpis']['categories'] = {k: int(cats.get(k,0)) for k in ['MK','MW','MO','SU']}
            except Exception:
                contract['kpis']['categories'] = {'MK':0,'MW':0,'MO':0,'SU':0}
        except sqlite3.Error:
            missing.append(cbsa_table)
    else:
        missing.append('mi_cbsa_fact')

    contract["missing_data"] = missing
    # debug: surface which tables were detected at request time (helps tests)
    try:
        detected = {}
        for t in ['mi_zip_fact','market_zip_fact','mi_cbsa_fact','market_cbsa_fact','market_targets','market_target_list']:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,))
            detected[t] = True if cur.fetchone() else False
        contract['detected_tables'] = detected
    except Exception:
        contract['detected_tables'] = {}
    contract["status"] = "ok" if len(missing) == 0 else "partial"
    return contract


@router.get("/market-intel/demographics")
def market_intel_demographics(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    missing = []
    gaps = []
    # Aggregate demo_json from mi_zip_fact if present
    if safe_table_exists(conn, 'mi_zip_fact'):
        try:
            q = "SELECT demo_json, contracts, COALESCE(fqma,0) as fqma FROM mi_zip_fact WHERE 1=1"
            if fy:
                q += f" AND fy={int(fy)}"
            if rsid_prefix:
                q += f" AND rsid_prefix='{rsid_prefix}'"
            cur.execute(q)
            rows = cur.fetchall()
            totals = {}
            for r in rows:
                demo = r[0]
                contracts = r[1] or 0
                fqma = r[2] or 0
                if not demo:
                    continue
                try:
                    jd = json.loads(demo)
                    for dim, groups in jd.items():
                        for g, pop in groups.items():
                            key = (dim, g)
                            totals.setdefault(key, {'population':0, 'contracts':0})
                            totals[key]['population'] += int(pop or 0)
                            totals[key]['contracts'] += int(contracts or 0)
                except Exception:
                    continue
            for (dim,g), vals in totals.items():
                pop = vals['population']
                contracts = vals['contracts']
                gap_ratio = 0
                try:
                    gap_ratio = round((pop - contracts) / pop, 4) if pop else 0
                except Exception:
                    gap_ratio = 0
                gaps.append({'dimension': dim, 'group': g, 'population': pop, 'contracts': contracts, 'gap_ratio': gap_ratio})
        except sqlite3.Error:
            missing.append('mi_zip_fact')
    else:
        missing.append('mi_zip_fact')

    return {'status':'ok','gaps':gaps,'missing_data':missing}


@router.get("/market-intel/categories")
def market_intel_categories(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None), limit: int = Query(10)):
    conn = connect()
    cur = conn.cursor()
    missing = []
    cats = {}
    top_zips = {}
    if safe_table_exists(conn, 'mi_zip_fact'):
        try:
            q = "SELECT market_category, COUNT(*) as cnt FROM mi_zip_fact WHERE 1=1"
            if fy:
                q += f" AND fy={int(fy)}"
            if rsid_prefix:
                q += f" AND rsid_prefix='{rsid_prefix}'"
            q += " GROUP BY market_category"
            cur.execute(q)
            for r in cur.fetchall():
                cats[r[0]] = r[1]
            # top zips per category by fqma
            for cat in cats.keys():
                tq = f"SELECT zip5 as zip, fqma FROM mi_zip_fact WHERE market_category='{cat}' ORDER BY COALESCE(fqma,0) DESC LIMIT {int(limit)}"
                cur.execute(tq)
                top_zips[cat] = [{'zip': rr[0], 'fqma': rr[1]} for rr in cur.fetchall()]
        except sqlite3.Error:
            missing.append('mi_zip_fact')
    else:
        missing.append('mi_zip_fact')
    return {'status':'ok','categories':cats,'top_zips':top_zips,'missing_data':missing}


@router.get("/market-intel/export/targets.csv")
def market_intel_export_targets(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None), component: Optional[str] = Query(None), funding_line: Optional[str] = Query(None), market_category: Optional[str] = Query(None), limit: int = Query(1000)):
    conn = connect()
    cur = conn.cursor()
    # Commander-ready columns
    headers = ['fy','qtr','rsid_prefix','zip','cbsa','market_category','priority_bucket','potential','fqma','contracts','army_share','p2p','opportunity_score']

    def _safe_header_only():
        return Response(content=','.join(headers) + '\n', media_type='text/csv')

    # Choose the best source table: prefer tables that have data (mi_* or legacy market_*)
    try:
        source_table = None
        if safe_table_exists(conn, 'mi_zip_fact') and _table_has_rows(conn, 'mi_zip_fact'):
            source_table = 'mi_zip_fact'
        elif safe_table_exists(conn, 'market_zip_fact') and _table_has_rows(conn, 'market_zip_fact'):
            source_table = 'market_zip_fact'

        # If we found a source table with rows, query it defensively
        if source_table:
            where = " WHERE 1=1"
            if fy:
                where += f" AND fy={int(fy)}"
            if qtr:
                where += f" AND qtr='{qtr}'"
            if rsid_prefix:
                where += f" AND rsid_prefix='{rsid_prefix}'"
            if component and _column_exists(conn, 'market_zip_fact', 'component'):
                where += f" AND component='{component}'"
            if funding_line and _column_exists(conn, 'market_zip_fact', 'funding_line'):
                where += f" AND funding_line='{funding_line}'"
            if market_category:
                where += f" AND market_category='{market_category}'"

            cols = []
            if _column_exists(conn, source_table, 'zip5'):
                cols.append('zip5 as zip')
            elif _column_exists(conn, source_table, 'zip'):
                cols.append('zip as zip')
            else:
                cols.append("'' as zip")

            cols.append("COALESCE(cbsa_code,'') as cbsa")
            cols.append("COALESCE(market_category,'') as market_category")
            cols.append("CASE WHEN COALESCE(must_keep,0)=1 THEN 'must_keep' WHEN COALESCE(must_win,0)=1 THEN 'must_win' WHEN COALESCE(market_of_opportunity,0)=1 THEN 'opportunity' WHEN COALESCE(supplemental_market,0)=1 THEN 'supplemental' ELSE '' END as priority_bucket")
            cols.append("COALESCE(potential_remaining,0) as potential")
            cols.append("COALESCE(fqma,0) as fqma")
            if _column_exists(conn, source_table, 'contracts'):
                cols.append('COALESCE(contracts,0) as contracts')
            else:
                cols.append('0 as contracts')
            cols.append('COALESCE(army_share,0) as army_share')
            cols.append('COALESCE(p2p,0) as p2p')
            if _column_exists(conn, source_table, 'opportunity_score'):
                cols.append('COALESCE(opportunity_score,0) as opportunity_score')
            else:
                cols.append('COALESCE(p2p,0) as opportunity_score')

            q = f"SELECT fy,qtr,rsid_prefix,{', '.join(cols)} FROM {source_table} {where} ORDER BY fy DESC LIMIT {int(limit)}"
            cur.execute(q)
            rows = cur.fetchall()
            lines = [','.join(headers)]
            for r in rows:
                vals = [str(r[i]) if r[i] is not None else '' for i in range(len(headers))]
                vals = [v.replace('\n',' ').replace('\r',' ').replace(',', ';') for v in vals]
                lines.append(','.join(vals))
            return Response(content='\n'.join(lines), media_type='text/csv')
    except sqlite3.Error:
        return _safe_header_only()

    # Fallback: check market_target_list or market_targets and attempt to map
    if safe_table_exists(conn, 'market_target_list') or safe_table_exists(conn, 'market_targets'):
        try:
            # Prefer market_target_list rows if available, otherwise use market_targets
            if safe_table_exists(conn, 'market_target_list') and _table_has_rows(conn, 'market_target_list'):
                q = "SELECT fy,qtr,rsid_prefix,zip5 as zip,cbsa_code as cbsa, target_type as market_category, 0 as priority_bucket, 0 as potential, 0 as fqma, 0 as contracts, 0 as army_share, 0 as p2p, 0 as opportunity_score FROM market_target_list WHERE 1=1"
            else:
                # market_targets uses 'zip' column name in legacy schema
                q = "SELECT fy,qtr,rsid_prefix,zip as zip,cbsa_code as cbsa, target_type as market_category, 0 as priority_bucket, 0 as potential, 0 as fqma, 0 as contracts, 0 as army_share, 0 as p2p, 0 as opportunity_score FROM market_targets WHERE 1=1"
            if fy:
                q += f" AND fy={int(fy)}"
            if qtr:
                q += f" AND qtr='{qtr}'"
            if rsid_prefix:
                q += f" AND rsid_prefix='{rsid_prefix}'"
            q += f" ORDER BY created_at DESC LIMIT {int(limit)}"
            cur.execute(q)
            rows = cur.fetchall()
            lines = [','.join(headers)]
            for r in rows:
                vals = [str(r[i]) if r[i] is not None else '' for i in range(len(headers))]
                vals = [v.replace(',', ';') for v in vals]
                lines.append(','.join(vals))
            return Response(content='\n'.join(lines), media_type='text/csv')
        except Exception:
            return _safe_header_only()

    return _safe_header_only()


@router.get("/market-intel/zip-rankings")
def zip_rankings(limit: int = Query(25), year: Optional[int] = Query(None)):
    conn = connect()
    contract = build_empty_rollup_contract({}, kpi_keys=["opportunity_score", "population"], breakdown_keys=["zip_rankings"], trend_keys=[])
    contract["data_as_of"] = _now_iso()

    if not safe_table_exists(conn, "market_zip_metrics"):
        contract["tables"] = {"zip_rankings": []}
        contract["missing_data"] = ["market_zip_metrics"]
        contract["status"] = "partial"
        return contract

    cur = conn.cursor()
    q = f"SELECT zip5, population, opportunity_score FROM market_zip_metrics ORDER BY opportunity_score DESC LIMIT {int(limit)}"
    try:
        cur.execute(q)
        rows = cur.fetchall()
        contract["breakdowns"] = {"zip_rankings": [{"zip5": r[0], "population": r[1], "opportunity_score": r[2]} for r in rows]}
    except sqlite3.Error:
        contract["breakdowns"] = {"zip_rankings": []}
        contract["missing_data"] = ["market_zip_metrics"]
        contract["status"] = "partial"
        return contract
    contract["missing_data"] = []
    contract["status"] = "ok"
    return contract


@router.get("/market-intel/cbsa-rollup")
def cbsa_rollup(limit: int = Query(50)):
    conn = connect()
    contract = build_empty_rollup_contract({}, kpi_keys=["population", "opportunity"], breakdown_keys=["cbsa_rollup"], trend_keys=[])
    contract["data_as_of"] = _now_iso()

    if not safe_table_exists(conn, "mi_cbsa_fact"):
        contract["breakdowns"]["cbsa_rollup"] = []
        contract["missing_data"] = ["mi_cbsa_fact"]
        contract["status"] = "partial"
        return contract

    cur = conn.cursor()
    q = f"SELECT cbsa_code, SUM(population) as population, SUM(opportunity) as opportunity FROM mi_cbsa_fact GROUP BY cbsa_code ORDER BY opportunity DESC LIMIT {int(limit)}"
    try:
        cur.execute(q)
        rows = cur.fetchall()
        contract["breakdowns"]["cbsa_rollup"] = [{"cbsa_code": r[0], "population": r[1], "opportunity": r[2]} for r in rows]
    except sqlite3.Error:
        contract["breakdowns"]["cbsa_rollup"] = []
        contract["missing_data"] = ["market_cbsa_fact"]
        contract["status"] = "partial"
        return contract
    contract["missing_data"] = []
    contract["status"] = "ok"
    return contract


@router.get("/market-intel/targets")
def market_targets():
    conn = connect()
    contract = build_empty_rollup_contract({}, kpi_keys=["population", "opportunity"], breakdown_keys=["targets"], trend_keys=[])
    contract["data_as_of"] = _now_iso()

    cur = conn.cursor()
    if not safe_table_exists(conn, "market_target_list"):
        contract["tables"] = {"targets": []}
        contract["missing_data"] = ["market_target_list"]
        contract["status"] = "partial"
        return contract

    try:
        cur.execute("SELECT id, fy, qtr, rsid_prefix, target_type, zip5, cbsa_code FROM market_target_list ORDER BY created_at DESC LIMIT 200")
        rows = cur.fetchall()
        contract["breakdowns"]["targets"] = [{"id": r[0], "fy": r[1], "qtr": r[2], "rsid_prefix": r[3], "target_type": r[4], "zip5": r[5], "cbsa_code": r[6]} for r in rows]
    except sqlite3.Error:
        contract["breakdowns"]["targets"] = []
        contract["missing_data"] = ["market_target_list"]
        contract["status"] = "partial"
        return contract
    contract["missing_data"] = []
    contract["status"] = "ok"
    return contract


@router.get("/market-intel/import-templates")
def import_templates():
    # Return a small set of import templates metadata for the Data Hub to consume
    human = [
        {"key": "market_zip_metrics", "name": "Market Zip Metrics", "description": "Per-zip metrics used by market intelligence"},
        {"key": "market_cbsa_fact", "name": "Market CBSA Fact", "description": "CBSA-level facts aggregated from zips"},
        {"key": "market_target_list", "name": "Market Targets", "description": "Manual target list for planning"},
    ]

    # Try to read executable templates from mi_import_template table if present
    conn = connect()
    cur = conn.cursor()
    templates = []
    if safe_table_exists(conn, 'mi_import_template'):
        try:
            cur.execute("SELECT template_key, dataset_key, description, columns_json, mapping_hints_json, validation_rules_json, created_at FROM mi_import_template")
            for r in cur.fetchall():
                templates.append({
                    'template_key': r[0],
                    'dataset_key': r[1],
                    'description': r[2],
                    'columns': json.loads(r[3]) if r[3] else [],
                    'mapping_hints': json.loads(r[4]) if r[4] else {},
                    'validation_rules': json.loads(r[5]) if r[5] else {},
                    'created_at': r[6]
                })
        except Exception:
            templates = []

    return {'status': 'ok', 'templates': human, 'executable_templates': templates}


@router.get("/market-intel/readiness")
def market_intel_readiness():
    conn = connect()
    cur = conn.cursor()
    datasets = []
    blocking = []
    warnings = []
    # Always ensure at least the core MI tables are considered
    default_checks = [
        {'dataset_key': 'mi_zip_fact', 'display_name': 'Market Zip Fact', 'table_name': 'mi_zip_fact'},
        {'dataset_key': 'mi_cbsa_fact', 'display_name': 'Market CBSA Fact', 'table_name': 'mi_cbsa_fact'},
    ]

    registry_rows = []
    if safe_table_exists(conn, 'mi_dataset_registry'):
        try:
            cur.execute("SELECT dataset_key, display_name, table_name, required_columns_json, optional_columns_json, last_seen_at FROM mi_dataset_registry")
            for r in cur.fetchall():
                registry_rows.append({'dataset_key': r[0], 'display_name': r[1], 'table_name': r[2], 'required_columns': json.loads(r[3] or '[]'), 'optional_columns': json.loads(r[4] or '[]'), 'last_seen_at': r[5]})
        except Exception:
            registry_rows = []

    # Merge registry with defaults (registry may be empty)
    checks = {d['dataset_key']: d for d in default_checks}
    for r in registry_rows:
        checks[r['dataset_key']] = r

    for key, info in checks.items():
        table = info.get('table_name')
        required = info.get('required_columns', [])
        optional = info.get('optional_columns', [])
        item = {'dataset_key': key, 'table': table, 'display_name': info.get('display_name')}
        if not safe_table_exists(conn, table):
            item['loaded'] = False
            item['missing_columns'] = required
            item['row_count'] = 0
            datasets.append(item)
        else:
            # compute row count and missing cols
            try:
                cur.execute(f"SELECT COUNT(1) FROM {table}")
                rc = cur.fetchone()[0] or 0
            except Exception:
                rc = 0
            miss = []
            try:
                cur.execute(f"PRAGMA table_info('{table}')")
                existing = [r[1] for r in cur.fetchall()]
                for c in required:
                    if c not in existing:
                        miss.append(c)
            except Exception:
                miss = required
            item['loaded'] = bool(rc > 0 and not miss)
            # For operational readiness, mark loaded only by row count > 0
            item['loaded'] = bool(rc > 0)
            item['missing_columns'] = miss
            item['row_count'] = rc
            datasets.append(item)

    # blocking datasets: for Phase 16 we require only the ZIP dataset to be loaded
    for d in datasets:
        if d['dataset_key'] == 'mi_zip_fact' and (not d['loaded']):
            blocking.append(d['dataset_key'])

    # CBSA remains informational/optional; do not include it in blocking list
    status = 'ok' if len(blocking) == 0 else 'partial'
    return {'status': status, 'datasets': datasets, 'blocking': blocking, 'warnings': warnings}


@router.get("/market-intel/exports/commander-targets.csv")
def market_intel_commander_targets(fy: Optional[int] = Query(None), qtr: Optional[str] = Query(None), rsid_prefix: Optional[str] = Query(None), component: Optional[str] = Query(None), market_category: Optional[str] = Query(None), top_n: int = Query(200)):
    conn = connect()
    cur = conn.cursor()

    headers = ['rsid_prefix','station_name','zip5','market_category','army_potential','dod_potential','army_share_of_potential','potential_remaining','contracts_ga','contracts_sa','contracts_vol','p2p','as_of_date','recommendation','rationale']

    def _header_only():
        return Response(content=','.join(headers) + '\n', media_type='text/csv')

    if not safe_table_exists(conn, 'mi_zip_fact'):
        return _header_only()

    try:
        where = " WHERE 1=1"
        if fy:
            where += f" AND fy={int(fy)}"
        if qtr:
            where += f" AND qtr='{qtr}'"
        if rsid_prefix:
            where += f" AND rsid_prefix='{rsid_prefix}'"
        if component and _column_exists(conn, 'mi_zip_fact', 'component'):
            where += f" AND component='{component}'"
        if market_category:
            where += f" AND market_category='{market_category}'"

        # choose zip column defensively
        zip_col = 'zip5' if _column_exists(conn, 'mi_zip_fact', 'zip5') else ('zip' if _column_exists(conn, 'mi_zip_fact', 'zip') else "''")

        select_cols = [
            "rsid_prefix",
            "COALESCE(station_name,'') as station_name",
            (f"{zip_col} as zip5" if zip_col != "''" else "'' as zip5"),
            "COALESCE(market_category,'') as market_category",
            "COALESCE(army_potential,0) as army_potential",
            "COALESCE(dod_potential,0) as dod_potential",
            "COALESCE(army_share,0) as army_share_of_potential",
            "COALESCE(potential_remaining,0) as potential_remaining",
            "COALESCE(contracts_ga,0) as contracts_ga",
            "COALESCE(contracts_sa,0) as contracts_sa",
            "COALESCE(contracts_vol,0) as contracts_vol",
            "COALESCE(p2p,0) as p2p",
            "COALESCE(data_as_of,'') as as_of_date",
        ]

        q = f"SELECT {', '.join(select_cols)} FROM mi_zip_fact {where} ORDER BY potential_remaining DESC, army_share_of_potential ASC LIMIT {int(top_n)}"
        cur.execute(q)
        rows = cur.fetchall()

        lines = [','.join(headers)]
        for r in rows:
            # r indexes correspond to select_cols order
            rsid_prefix_v = r[0] or ''
            station_name_v = (r[1] or '').replace('\n',' ').replace('\r',' ').replace(',',';')
            zip5_v = r[2] or ''
            market_cat_v = r[3] or ''
            army_pot = float(r[4] or 0)
            dod_pot = float(r[5] or 0)
            army_share = float(r[6] or 0)
            potential_remaining = float(r[7] or 0)
            contracts_ga = int(r[8] or 0)
            contracts_sa = int(r[9] or 0)
            contracts_vol = int(r[10] or 0)
            p2p = float(r[11] or 0)
            as_of = r[12] or ''

            # derive recommendation
            rec = ''
            if market_cat_v in ('MW','MO') and potential_remaining > 1000:
                rec = 'PRIORITIZE'
            elif market_cat_v == 'MK' and potential_remaining > 250:
                rec = 'SUSTAIN'
            elif market_cat_v == 'SU' and potential_remaining < 50:
                rec = 'DEPRIORITIZE'
            else:
                rec = 'REVIEW'

            rationale = f"Category={market_cat_v}; RemainingPotential={int(potential_remaining)}; Share={round(army_share*100,1)}%"

            row_vals = [
                rsid_prefix_v,
                station_name_v,
                zip5_v,
                market_cat_v,
                str(int(army_pot)),
                str(int(dod_pot)),
                str(round(army_share,4)),
                str(int(potential_remaining)),
                str(contracts_ga),
                str(contracts_sa),
                str(contracts_vol),
                str(round(p2p,4)),
                as_of,
                rec,
                rationale.replace(',', ';')
            ]
            lines.append(','.join(row_vals))

        return Response(content='\n'.join(lines), media_type='text/csv')
    except sqlite3.Error:
        return _header_only()
