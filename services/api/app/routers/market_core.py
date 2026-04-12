from fastapi import APIRouter, Depends, HTTPException
from services.api.app.database import get_db
from services.api.app.models_refresh import RefreshSource, DatasetActive, RefreshDatasetRow
from sqlalchemy.orm import Session
from collections import Counter

router = APIRouter()


@router.get('/market_core_vantage/active')
def get_market_core_active(db: Session = Depends(get_db)):
    # Find the registered source by canonical target or name
    src = db.query(RefreshSource).filter(RefreshSource.canonical_target == 'market_core_vantage').first()
    if not src:
        raise HTTPException(status_code=404, detail='Vantage Market Core source not registered')
    active = db.query(DatasetActive).filter(DatasetActive.source_id == src.id).first()
    if not active or not active.version_id:
        raise HTTPException(status_code=404, detail='No active version for market_core_vantage')
    rows = db.query(RefreshDatasetRow).filter(
        RefreshDatasetRow.source_id == src.id,
        RefreshDatasetRow.version_id == active.version_id,
    ).all()
    return [r.row_json for r in rows]


@router.get('/market_core_vantage/mi')
def market_core_mi_active(db: Session = Depends(get_db)):
    """Trusted Market Intelligence read of the active Market Core dataset.

    Returns a clean operator-facing view. Read-only, uses the active
    dataset version. Excludes rows missing `zip` or any assignment chain.
    """
    src = db.query(RefreshSource).filter(RefreshSource.canonical_target == 'market_core_vantage').first()
    if not src:
        raise HTTPException(status_code=404, detail='Vantage Market Core source not registered')
    active = db.query(DatasetActive).filter(DatasetActive.source_id == src.id).first()
    if not active or not active.version_id:
        raise HTTPException(status_code=404, detail='No active version for market_core_vantage')

    q = db.query(RefreshDatasetRow).filter(
        RefreshDatasetRow.source_id == src.id,
        RefreshDatasetRow.version_id == active.version_id,
    )

    # define assignment groups
    enlisted_fields = {
        'enlisted_begin_effective_date','enlisted_end_effective_date','rsid_enlisted','rsid_enlisted_station','rsid_enlisted_company','rsid_enlisted_battalion','rsid_enlisted_brigade','rsid_enlisted_command','lduic_enlisted_station','lduic_enlisted_company','lduic_enlisted_battalion','uic_enlisted_brigade','uic_enlisted_command'
    }
    medical_fields = {
        'medical_begin_effective_date','medical_end_effective_date','rsid_medical','rsid_medical_station','rsid_medical_company','rsid_medical_battalion','rsid_medical_brigade','rsid_medical_command','lduic_medical_station','lduic_medical_company','lduic_medical_battalion','uic_medical_brigade','uic_medical_command'
    }
    chaplain_fields = {
        'chaplain_begin_effective_date','chaplain_end_effective_date','rsid_chaplain','rsid_chaplain_station','rsid_chaplain_company','rsid_chaplain_battalion','rsid_chaplain_brigade','rsid_chaplain_command','lduic_chaplain_station','lduic_chaplain_company','lduic_chaplain_battalion','uic_chaplain_brigade','uic_chaplain_command'
    }

    # recruiting age buckets present in CSV
    recruiting_buckets = [
        'tot_male_15_17_b01001_006e','tot_male_18_19_b01001_007e','tot_male_20_b01001_008e','tot_male_21_b01001_009e','tot_male_22_24_b01001_010e',
        'tot_female_15_17_b01001_030e','tot_female_18_19_b01001_031e','tot_female_20_b01001_032e','tot_female_21_b01001_033e','tot_female_22_24_b01001_034e'
    ]

    def to_int(v):
        if v is None:
            return None
        try:
            s = str(v).strip()
            if s == '':
                return None
            return int(float(s.replace(',', '')))
        except Exception:
            return None

    results = []
    # derive demographic field list from a sample row
    sample = q.first()
    if not sample:
        return []
    all_cols = set(sample.row_json.keys())
    identity_fields = {'zip', '\ufeffzip'}
    assignment_fields = enlisted_fields | medical_fields | chaplain_fields
    demographic_fields = list(all_cols - identity_fields - assignment_fields)

    for r in q.yield_per(200):
        row = r.row_json or {}
        # require zip and at least one assignment chain
        zip_val = row.get('zip') or row.get('\ufeffzip')
        enlisted_present = any(row.get(f) not in (None, '', []) for f in enlisted_fields)
        medical_present = any(row.get(f) not in (None, '', []) for f in medical_fields)
        chaplain_present = any(row.get(f) not in (None, '', []) for f in chaplain_fields)
        assignment_ok = enlisted_present or medical_present or chaplain_present
        if not zip_val or not assignment_ok:
            # skip rows that don't meet minimal trust criteria
            continue

        # compute demo_any for partial flag
        demo_any = any(row.get(f) not in (None, '', []) for f in demographic_fields)
        partial_flag = assignment_ok and not demo_any

        # assemble MI view
        rec = {
            'zip': zip_val,
            'rsid_enlisted': row.get('rsid_enlisted'),
            'rsid_enlisted_station': row.get('rsid_enlisted_station'),
            'rsid_enlisted_company': row.get('rsid_enlisted_company'),
            'rsid_enlisted_battalion': row.get('rsid_enlisted_battalion'),
            'total_population_b01003_001e': to_int(row.get('total_population_b01003_001e')),
            'total_veteran_b21001_002e': to_int(row.get('total_veteran_b21001_002e')),
            'total_nonveteren_b21001_003e': to_int(row.get('total_nonveteren_b21001_003e')),
            'recruiting_age_total': 0,
            'partial_market_data': partial_flag,
        }
        # compute recruiting_age_total
        s = 0
        for cb in recruiting_buckets:
            v = to_int(row.get(cb))
            if v:
                s += v
        rec['recruiting_age_total'] = s
        results.append(rec)

    return results


@router.get('/market_core_vantage/validation')
def validate_market_core_active(db: Session = Depends(get_db)):
    """Run lightweight validation/reporting over the active Market Core dataset.

    Validation rules:
    - require `zip` (non-empty)
    - require at least one populated assignment chain (enlisted, medical, chaplain)
    - rows with assignment but no demographic metrics populated are flagged as `partial_market_data`
    """
    src = db.query(RefreshSource).filter(RefreshSource.canonical_target == 'market_core_vantage').first()
    if not src:
        raise HTTPException(status_code=404, detail='Vantage Market Core source not registered')
    active = db.query(DatasetActive).filter(DatasetActive.source_id == src.id).first()
    if not active or not active.version_id:
        raise HTTPException(status_code=404, detail='No active version for market_core_vantage')

    q = db.query(RefreshDatasetRow).filter(
        RefreshDatasetRow.source_id == src.id,
        RefreshDatasetRow.version_id == active.version_id,
    )

    total = 0
    valid = 0
    invalid = 0
    partial = 0
    enlisted_battalion = Counter()
    enlisted_company = Counter()
    enlisted_station = Counter()

    # canonical assignment groups (as requested)
    enlisted_fields = {
        'enlisted_begin_effective_date','enlisted_end_effective_date','rsid_enlisted','rsid_enlisted_station','rsid_enlisted_company','rsid_enlisted_battalion','rsid_enlisted_brigade','rsid_enlisted_command','lduic_enlisted_station','lduic_enlisted_company','lduic_enlisted_battalion','uic_enlisted_brigade','uic_enlisted_command'
    }
    medical_fields = {
        'medical_begin_effective_date','medical_end_effective_date','rsid_medical','rsid_medical_station','rsid_medical_company','rsid_medical_battalion','rsid_medical_brigade','rsid_medical_command','lduic_medical_station','lduic_medical_company','lduic_medical_battalion','uic_medical_brigade','uic_medical_command'
    }
    chaplain_fields = {
        'chaplain_begin_effective_date','chaplain_end_effective_date','rsid_chaplain','rsid_chaplain_station','rsid_chaplain_company','rsid_chaplain_battalion','rsid_chaplain_brigade','rsid_chaplain_command','lduic_chaplain_station','lduic_chaplain_company','lduic_chaplain_battalion','uic_chaplain_brigade','uic_chaplain_command'
    }

    # Determine demographic metric columns by fetching a sample row keys
    sample_row = q.first()
    if not sample_row:
        return {'total': 0, 'valid': 0, 'invalid': 0, 'partial_market_data': 0}
    all_cols = set(sample_row.row_json.keys())
    identity_fields = {'zip', '\ufeffzip'}
    assignment_fields = enlisted_fields | medical_fields | chaplain_fields
    demographic_fields = sorted(list(all_cols - identity_fields - assignment_fields))

    for r in q.yield_per(200):
        total += 1
        row = r.row_json or {}
        # rule 1: require zip (handle BOM-prefixed header as well)
        zip_ok = bool(row.get('zip') or row.get('\ufeffzip'))

        # rule 2: at least one assignment chain present (any non-empty in that group)
        enlisted_present = any(row.get(f) not in (None, '', []) for f in enlisted_fields)
        medical_present = any(row.get(f) not in (None, '', []) for f in medical_fields)
        chaplain_present = any(row.get(f) not in (None, '', []) for f in chaplain_fields)
        assignment_ok = enlisted_present or medical_present or chaplain_present

        # rule 3: demographic metrics all null/empty
        demo_any = any(row.get(f) not in (None, '', []) for f in demographic_fields)

        if not zip_ok or not assignment_ok:
            invalid += 1
            continue

        # If assignment exists but demographics are all empty, mark partial
        if assignment_ok and not demo_any:
            partial += 1
        else:
            valid += 1

        # tally enlisted breakdowns
        eb = row.get('rsid_enlisted') or row.get('lduic_enlisted_station') or row.get('rsid_enlisted_station')
        if eb:
            enlisted_station[eb] += 1
        ec = row.get('rsid_enlisted_company') or row.get('lduic_enlisted_company')
        if ec:
            enlisted_company[ec] += 1
        ebn = row.get('rsid_enlisted_battalion') or row.get('lduic_enlisted_battalion')
        if ebn:
            enlisted_battalion[ebn] += 1

    summary = {
        'total': total,
        'valid': valid,
        'invalid': invalid,
        'partial_market_data': partial,
        'enlisted_battalion_counts': dict(enlisted_battalion.most_common()),
        'enlisted_company_counts': dict(enlisted_company.most_common()),
        'enlisted_station_counts': dict(enlisted_station.most_common()),
        'demographic_fields_sample': demographic_fields[:20],
    }
    return summary


@router.get('/market_core_vantage/top_stations')
def market_core_top_stations(limit: int = 10, exclude_partial: bool = False, db: Session = Depends(get_db)):
    rows = _get_market_core_active_rows(db)
    agg = {}
    for r in rows:
        norm = _normalize_market_core_row(r.row_json)
        if exclude_partial and norm.get('partial_market_data'):
            continue
        station = norm.get('rsid_enlisted_station') or 'UNKNOWN'
        comp = norm.get('rsid_enlisted_company')
        batt = norm.get('rsid_enlisted_battalion')
        entry = agg.setdefault(station, {
            'rsid_enlisted_station': station,
            'rsid_enlisted_company_counts': Counter(),
            'rsid_enlisted_battalion_counts': Counter(),
            'zips': set(),
            'total_population': 0,
            'recruiting_age_total': 0,
            'veteran_total': 0,
            'partial_zip_count': 0,
        })
        if norm.get('zip'):
            entry['zips'].add(norm.get('zip'))
        if norm.get('total_population_b01003_001e'):
            entry['total_population'] += norm.get('total_population_b01003_001e')
        entry['recruiting_age_total'] += norm.get('recruiting_age_total') or 0
        if norm.get('total_veteran_b21001_002e'):
            entry['veteran_total'] += norm.get('total_veteran_b21001_002e')
        if norm.get('partial_market_data'):
            entry['partial_zip_count'] += 1
        if comp:
            entry['rsid_enlisted_company_counts'][comp] += 1
        if batt:
            entry['rsid_enlisted_battalion_counts'][batt] += 1

    out = []
    for station, v in agg.items():
        company = None
        battalion = None
        if v['rsid_enlisted_company_counts']:
            company = v['rsid_enlisted_company_counts'].most_common(1)[0][0]
        if v['rsid_enlisted_battalion_counts']:
            battalion = v['rsid_enlisted_battalion_counts'].most_common(1)[0][0]
        zip_count = len(v['zips'])
        out.append({
            'rsid_enlisted_station': station,
            'rsid_enlisted_company': company,
            'rsid_enlisted_battalion': battalion,
            'zip_count': len(v['zips']),
            'total_population': v['total_population'],
            'recruiting_age_total': v['recruiting_age_total'],
            'veteran_total': v['veteran_total'],
            'partial_zip_count': v['partial_zip_count'],
            'quality_score': 1 - (v['partial_zip_count'] / zip_count if zip_count else 0),
        })

    out.sort(key=lambda x: (x.get('recruiting_age_total') or 0, x.get('total_population') or 0), reverse=True)
    return out[:limit]


@router.get('/market_core_vantage/top_companies')
def market_core_top_companies(limit: int = 10, exclude_partial: bool = False, db: Session = Depends(get_db)):
    rows = _get_market_core_active_rows(db)
    agg = {}
    for r in rows:
        norm = _normalize_market_core_row(r.row_json)
        if exclude_partial and norm.get('partial_market_data'):
            continue
        comp = norm.get('rsid_enlisted_company') or 'UNKNOWN'
        batt = norm.get('rsid_enlisted_battalion')
        entry = agg.setdefault(comp, {
            'rsid_enlisted_company': comp,
            'rsid_enlisted_battalion_counts': Counter(),
            'zips': set(),
            'total_population': 0,
            'recruiting_age_total': 0,
            'veteran_total': 0,
            'partial_zip_count': 0,
        })
        if norm.get('zip'):
            entry['zips'].add(norm.get('zip'))
        if norm.get('total_population_b01003_001e'):
            entry['total_population'] += norm.get('total_population_b01003_001e')
        entry['recruiting_age_total'] += norm.get('recruiting_age_total') or 0
        if norm.get('total_veteran_b21001_002e'):
            entry['veteran_total'] += norm.get('total_veteran_b21001_002e')
        if norm.get('partial_market_data'):
            entry['partial_zip_count'] += 1
        if batt:
            entry['rsid_enlisted_battalion_counts'][batt] += 1

    out = []
    for comp, v in agg.items():
        battalion = None
        if v['rsid_enlisted_battalion_counts']:
            battalion = v['rsid_enlisted_battalion_counts'].most_common(1)[0][0]
        zip_count = len(v['zips'])
        out.append({
            'rsid_enlisted_company': comp,
            'rsid_enlisted_battalion': battalion,
            'zip_count': len(v['zips']),
            'total_population': v['total_population'],
            'recruiting_age_total': v['recruiting_age_total'],
            'veteran_total': v['veteran_total'],
            'partial_zip_count': v['partial_zip_count'],
            'quality_score': 1 - (v['partial_zip_count'] / zip_count if zip_count else 0),
        })

    out.sort(key=lambda x: (x.get('recruiting_age_total') or 0, x.get('total_population') or 0), reverse=True)
    return out[:limit]


@router.get('/market_core_vantage/zip_summary')
def market_core_zip_summary(exclude_partial: bool = False, db: Session = Depends(get_db)):
    rows = _get_market_core_active_rows(db)
    out = []
    for r in rows:
        norm = _normalize_market_core_row(r.row_json)
        if exclude_partial and norm.get('partial_market_data'):
            continue
        out.append({
            'zip': norm.get('zip'),
            'rsid_enlisted_station': norm.get('rsid_enlisted_station'),
            'rsid_enlisted_company': norm.get('rsid_enlisted_company'),
            'rsid_enlisted_battalion': norm.get('rsid_enlisted_battalion'),
            'total_population_b01003_001e': norm.get('total_population_b01003_001e'),
            'total_veteran_b21001_002e': norm.get('total_veteran_b21001_002e'),
            'total_nonveteren_b21001_003e': norm.get('total_nonveteren_b21001_003e'),
            'recruiting_age_total': norm.get('recruiting_age_total'),
            'partial_market_data': norm.get('partial_market_data'),
        })
    return out


@router.get('/market_core_vantage/data_quality')
def market_core_data_quality(db: Session = Depends(get_db)):
    rows = _get_market_core_active_rows(db)
    total = 0
    complete = 0
    partial = 0
    missing_zip = 0
    missing_assignment = 0
    for r in rows:
        total += 1
        norm = _normalize_market_core_row(r.row_json)
        if not norm.get('zip'):
            missing_zip += 1
        if not norm.get('has_assignment'):
            missing_assignment += 1
        if norm.get('partial_market_data'):
            partial += 1
        else:
            # consider complete if has assignment and demographics
            if norm.get('has_assignment') and not norm.get('partial_market_data'):
                complete += 1

    partial_rate = (partial / total) if total else None
    return {
        'total_rows': total,
        'complete_rows': complete,
        'partial_rows': partial,
        'missing_zip_rows': missing_zip,
        'missing_assignment_rows': missing_assignment,
        'partial_rate': partial_rate,
    }
