"""Recalibrate raw Recruiting Funnel workbook into normalized artifacts.

Outputs (artifacts/funnel_recalibrated/):
 - person_snapshot.csv
 - funnel_events_long.csv
 - funnel_summary.csv
 - data_quality_report.json

Usage:
  python recalibrate_funnel_workbook.py /path/to/Recruiting\ Funnel\ Enriched.xlsx
"""
import sys
import os
import json
import re
from datetime import datetime
import pandas as pd
from collections import defaultdict

from mapping_config import PERSON_ID_CANDIDATES, map_to_canonical, map_stage, STAGE_MAP, MILESTONE_MAP

OUT_DIR = os.path.join('artifacts','funnel_recalibrated')
os.makedirs(OUT_DIR, exist_ok=True)

# Hard blacklist of known-bad timestamp columns
BAD_TIMESTAMP_COLUMNS = {
    "col_000",
    "col_001",
    "col_071",
    "col_112"
}

def normalize_col(col):
    if pd.isna(col): return ''
    s = str(col).strip()
    s = s.lstrip('\ufeff')
    s = re.sub(r'\s+', ' ', s)
    s = s.replace('%','pct')
    s = s.lower()
    s = re.sub(r'[^0-9a-z_ ]','', s)
    s = s.strip().replace(' ','_')
    return s

def synth_col_name(i):
    return f"col_{i:03d}"

def is_email(s):
    if s is None: return False
    return bool(re.search(r"\S+@\S+\.\S+", str(s)))

def is_epoch_list(s):
    if s is None: return False
    s = str(s)
    # comma-separated tokens that are all long ints
    parts = re.split(r'\s*,\s*|\s*;\s*', s)
    if len(parts) < 2:
        return False
    cnt = 0
    for p in parts:
        if re.match(r'^\d{9,16}$', p.strip()):
            cnt += 1
    return cnt >= max(1, int(0.5 * len(parts)))

def looks_array(s):
    if s is None: return False
    s = str(s)
    return ',' in s or ';' in s

def likely_zip(s):
    if s is None: return False
    return bool(re.match(r'^[0-9]{5}(-[0-9]{4})?$', str(s)))

def likely_sex(s):
    if s is None: return False
    s = str(s).strip().upper()
    return s in ('M','F','MALE','FEMALE')


def choose_person_id(row, cols):
    for c in cols:
        if c in row and pd.notna(row[c]) and str(row[c]).strip()!='':
            return str(row[c])
    return None

def safe_parse_date(x):
    # legacy wrapper: keep compatibility
    ts, _ = normalize_timestamp(x)
    return ts


def normalize_timestamp(raw):
    """Normalize many timestamp formats into pandas.Timestamp or (None).

    Returns: (pd.Timestamp or None, parse_mode_str)
    Supported heuristics:
    - None / empty / 'null' / 'nan' => (None, 'null')
    - 13-digit integer-like => epoch milliseconds
    - 10-digit integer-like => epoch seconds
    - float-like numeric strings => treat as seconds if small, else milliseconds
    - Excel serial date numbers (plausible range) => convert from Excel serial
    - ISO / human datetime strings => parsed by pd.to_datetime
    """
    if raw is None:
        return (None, 'null')
    s = str(raw).strip()
    if s == '' or s.lower() in ('nan','null','nat','none'):
        return (None, 'null')

    # drop surrounding quotes
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1].strip()

    # pure digits (possible epoch)
    digits = re.sub(r'[^0-9\-\.]','', s)
    # try integer epoch detection
    if re.fullmatch(r'\d{13}', digits):
        try:
            return (pd.to_datetime(int(digits), unit='ms', errors='coerce'), 'epoch_ms')
        except Exception:
            pass
    if re.fullmatch(r'\d{10}', digits):
        try:
            return (pd.to_datetime(int(digits), unit='s', errors='coerce'), 'epoch_s')
        except Exception:
            pass

    # floats or large ints: try ms then s
    if re.fullmatch(r'\d{11,16}', digits):
        # ambiguous large number, prefer ms
        try:
            t = pd.to_datetime(int(digits), unit='ms', errors='coerce')
            if pd.notna(t):
                return (t, 'epoch_ms')
        except Exception:
            pass
        try:
            t = pd.to_datetime(int(digits), unit='s', errors='coerce')
            if pd.notna(t):
                return (t, 'epoch_s')
        except Exception:
            pass

    # numeric-looking but with decimal: maybe seconds with fractional
    if re.fullmatch(r'\d+\.\d+', digits) or re.fullmatch(r'\d+\.\d+', s):
        try:
            # treat as seconds float
            return (pd.to_datetime(float(digits), unit='s', errors='coerce'), 'epoch_s_float')
        except Exception:
            pass

    # Excel serial numbers: reasonable serials (e.g., > 20000 and < 50000)
    try:
        if re.fullmatch(r'\d{4,5}(?:\.\d+)?', s):
            val = float(s)
            if 2000 < val < 60000:
                # Excel serial origin
                excel_epoch = pd.Timestamp('1899-12-30')
                try:
                    return (excel_epoch + pd.to_timedelta(val, unit='D'), 'excel_serial')
                except Exception:
                    pass
    except Exception:
        pass

    # Finally try pandas parsing for ISO/human forms
    try:
        t = pd.to_datetime(s, errors='coerce')
        if pd.notna(t):
            return (t, 'datetime_string')
    except Exception:
        pass

    return (None, 'unparsed')


def is_valid_timestamp_series(series):
    """Given a list-like of raw timestamp tokens, return True if >60% parse to datetimes."""
    if series is None:
        return False
    try:
        s = pd.Series(list(series))
        parsed = pd.to_datetime(s, errors='coerce')
        valid_ratio = parsed.notna().mean()
        return valid_ratio > 0.6
    except Exception:
        return False

def split_list_cell(cell):
    if pd.isna(cell): return []
    s = str(cell).strip()
    if s=='' or s.lower() in ('nan','none','[]'): return []
    # split on comma or semicolon, but avoid splitting numbers with commas? assume export is simple
    parts = re.split(r'\s*,\s*|\s*;\s*', s)
    return [p if p!='' else None for p in parts]

def recalibrate(path, sheet_name=None):
    xl = pd.ExcelFile(path)
    if sheet_name is None:
        sheet_name = xl.sheet_names[0]

    # Read workbook as headerless positional columns
    df = pd.read_excel(xl, sheet_name=sheet_name, header=None, dtype=object)

    # assign synthetic positional column names
    col_count = df.shape[1]
    synthetic_cols = [synth_col_name(i) for i in range(col_count)]
    df.columns = synthetic_cols

    # profile columns (sample first 100 rows)
    sample = df.head(100)
    col_profiles = {}
    for c in synthetic_cols:
        series = sample[c]
        nonnull = series.dropna().astype(str)
        null_ratio = float((series.isna() | (series.astype(str).str.strip()=='' )).sum()) / max(1, len(series))
        examples = list(nonnull.head(5).unique())
        col_profiles[c] = {
            'null_ratio': null_ratio,
            'example_values': examples
        }

    # detect timeline-like columns and identity-like columns by positional heuristics
    timeline_cols = []
    identity_candidates = []
    inferred_roles = {}
    # check full column for patterns
    for c in synthetic_cols:
        col = df[c].astype(object)
        # timeline if many values look like arrays or epoch lists
        array_like_count = col.dropna().astype(str).str.contains(r',|;|\[|\]').sum()
        epoch_like_count = col.dropna().astype(str).str.match(r'^\d{9,16}(,\s*\d{9,16})*$').sum()
        email_count = col.dropna().astype(str).str.contains(r'@').sum()
        zip_count = col.dropna().astype(str).str.match(r'^[0-9]{5}(-[0-9]{4})?$').sum()
        sex_count = col.dropna().astype(str).str.upper().isin(['M','F','MALE','FEMALE']).sum()
        unique_vals = col.dropna().astype(str).nunique()
        total_vals = max(1, len(col))

        if array_like_count >= max(1, int(0.05 * total_vals)) or epoch_like_count >= max(1, int(0.02 * total_vals)):
            timeline_cols.append(c)
            inferred_roles[c] = 'timeline_array'
        elif email_count >= max(1, int(0.02 * total_vals)):
            identity_candidates.append(c)
            inferred_roles[c] = 'email'
        elif (unique_vals >= max(50, int(0.5 * total_vals))) and col.dropna().astype(str).str.match(r'^\d+$').sum() >= max(1, int(0.1*total_vals)):
            # high-cardinality numeric id
            identity_candidates.append(c)
            inferred_roles[c] = 'high_cardinality_id'
        elif sex_count >= max(1, int(0.02 * total_vals)):
            inferred_roles[c] = 'sex'
        elif zip_count >= max(1, int(0.02 * total_vals)):
            inferred_roles[c] = 'zip'
        else:
            inferred_roles[c] = 'text'

    person_rows = []
    events = []
    quality = {
        'row_count': int(len(df)),
        'missing_person_id': [],
        'invalid_timestamps': 0,
        'unknown_stage_mappings': 0,
        'inferred_roles': inferred_roles,
        'positional_profile_top100': col_profiles,
        'inferred_aliases': {},
        # new timeline quality counters
        'missing_timestamp_rows': [],
        'missing_timestamp_events': 0,
        'partial_events_count': 0,
        'fully_aligned_events_count': 0,
        # timestamp candidate diagnostics
        'timestamp_candidates_tested': [],
        'timestamp_source_usage_counts': {},
        'parsed_timestamp_count': 0,
        'unparsed_timestamp_count': 0,
        'rows_using_fallback_timestamp_source': 0,
        'rows_still_missing_timestamp_source': 0
    }

    # choose primary person id candidate (prefer email then high_cardinality_id then PERSON_ID_CANDIDATES by synthetic name mapping if present)
    chosen_person_id_col = None
    if identity_candidates:
        # prefer emails
        emails = [c for c in identity_candidates if inferred_roles.get(c)=='email']
        if emails:
            chosen_person_id_col = emails[0]
        else:
            chosen_person_id_col = identity_candidates[0]
    # fallback: search for synthetic columns matching known names (if any)
    if chosen_person_id_col is None:
        for pat in PERSON_ID_CANDIDATES:
            for c in synthetic_cols:
                if pat in c.lower():
                    chosen_person_id_col = c
                    break
            if chosen_person_id_col:
                break

    # populate inferred alias into quality
    quality['inferred_aliases']['person_id_candidate_source_col'] = chosen_person_id_col

    # infer timeline roles: try to pick likely timestamp / lifecycle / activity / outcome columns among timeline_cols
    chosen_timeline_timestamp = None
    chosen_timeline_lifecycle = None
    chosen_timeline_activity_code = None
    chosen_timeline_activity_label = None
    chosen_timeline_outcome = None
    chosen_timeline_notes = None

    for c in timeline_cols:
        # heuristics based on example values
        ex = ' '.join([str(x) for x in col_profiles.get(c,{}).get('example_values',[])])
        if is_epoch_list(ex) and chosen_timeline_timestamp is None:
            chosen_timeline_timestamp = c
        elif 'stage' in ex.lower() or 'prospect' in ex.lower() or 'applicant' in ex.lower():
            if chosen_timeline_lifecycle is None:
                chosen_timeline_lifecycle = c
        elif any(k in ex.lower() for k in ('activity','appointment','test','face to face','fs')):
            if chosen_timeline_activity_label is None:
                chosen_timeline_activity_label = c
        else:
            # fallback: if contains many short codes (2-3 chars comma-separated)
            vals = df[c].dropna().astype(str)
            sample_vals = vals.head(50)
            short_code_frac = (sample_vals.str.split(r',').apply(lambda parts: all(len(p.strip())<=3 for p in parts if p.strip()))).sum()
            if short_code_frac >= 1 and chosen_timeline_activity_code is None:
                chosen_timeline_activity_code = c

    quality['inferred_aliases'].update({
        'timeline_timestamp_source_col': chosen_timeline_timestamp,
        'timeline_lifecycle_source_col': chosen_timeline_lifecycle,
        'timeline_activity_code_source_col': chosen_timeline_activity_code,
        'timeline_activity_label_source_col': chosen_timeline_activity_label,
        'timeline_outcome_source_col': chosen_timeline_outcome,
        'timeline_notes_source_col': chosen_timeline_notes
    })

    # Now iterate rows and expand timelines using timestamp as the anchor
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        # choose person id
        person_id = None
        if chosen_person_id_col:
            v = row_dict.get(chosen_person_id_col)
            if v is not None and str(v).strip()!='':
                person_id = str(v)
        # fallback heuristics
        if person_id is None:
            # look for any email-like in row
            for c in synthetic_cols:
                if is_email(row_dict.get(c)):
                    person_id = str(row_dict.get(c))
                    quality['inferred_aliases']['person_id_candidate_source_col'] = c
                    break
        if person_id is None:
            # high-cardinality numeric
            for c in synthetic_cols:
                v = row_dict.get(c)
                if v is None: continue
                s = str(v).strip()
                if s.isdigit() and len(set(df[c].dropna().astype(str)))>50:
                    person_id = s
                    quality['inferred_aliases']['person_id_candidate_source_col'] = c
                    break
        if person_id is None:
            person_id = f'gen_{idx}'
            quality['missing_person_id'].append(int(idx))

        # snapshot
        snapshot = {'_internal_row_index': int(idx), 'person_id_candidate': person_id}
        # add raw positional columns into snapshot (preserve provenance)
        for c in synthetic_cols:
            snapshot[c+'_raw'] = row_dict.get(c)
        # also add chosen aliases as separate columns (do not remove raw)
        snapshot['person_id_candidate_source_col'] = quality['inferred_aliases'].get('person_id_candidate_source_col')
        snapshot['sex_source_col'] = next((c for c,r in inferred_roles.items() if r=='sex'), None)
        snapshot['dob_source_col'] = None
        snapshot['zip_source_col'] = next((c for c,r in inferred_roles.items() if r=='zip'), None)

        person_rows.append(snapshot)
        # build timeline arrays (preserve raw arrays)
        arrays = {c: split_list_cell(row_dict.get(c)) for c in timeline_cols}

        # determine timestamp anchor for this row using candidate scoring
        primary_ts = quality['inferred_aliases'].get('timeline_timestamp_source_col')
        candidates = []
        tested = []

        # priority a) explicit inferred timestamp source
        if primary_ts:
            # skip known-bad columns
            if primary_ts not in BAD_TIMESTAMP_COLUMNS:
                # ensure candidate has sufficient valid timestamp parse rate
                cand_arr = arrays.get(primary_ts, []) if primary_ts in arrays else ([row_dict.get(primary_ts)] if row_dict.get(primary_ts) is not None else [])
                if is_valid_timestamp_series(cand_arr):
                    candidates.append(primary_ts)

        # b) any timeline_cols that are arrays in this row
        for c in timeline_cols:
            if c in BAD_TIMESTAMP_COLUMNS:
                continue
            arr = arrays.get(c, [])
            if len(arr) > 0 and is_valid_timestamp_series(arr):
                candidates.append(c)

        # c) any timeline_cols with parseable datetime strings in this row
        for c in timeline_cols:
            if c in candidates: continue
            if c in BAD_TIMESTAMP_COLUMNS:
                continue
            arr = arrays.get(c, [])
            if len(arr) > 0 and any(normalize_timestamp(x)[0] is not None for x in arr) and is_valid_timestamp_series(arr):
                candidates.append(c)

        # d) any single-value timestamp-like columns (non-array) as fallback
        if not candidates:
            for c in synthetic_cols:
                if c in timeline_cols: continue
                if c in BAD_TIMESTAMP_COLUMNS:
                    continue
                v = row_dict.get(c)
                if v is None: continue
                # if this single value parses and passes validation, add as candidate
                ts_parsed, _ = normalize_timestamp(v)
                single_series = [v]
                if ts_parsed is not None and is_valid_timestamp_series(single_series):
                    candidates.append(c)

        # score candidates per-row
        best = None
        best_score = None
        for c in candidates:
            # skip blacklisted candidates defensively
            if c in BAD_TIMESTAMP_COLUMNS:
                continue
            arr = arrays.get(c, []) if c in arrays else ([row_dict.get(c)] if row_dict.get(c) is not None else [])
            # enforce per-candidate series validity before scoring
            if not is_valid_timestamp_series(arr):
                # record tested but skip
                tested.append({'col': c, 'parseable_count': 0, 'array_len': len(arr), 'null_ratio': col_profiles.get(c, {}).get('null_ratio', 1.0), 'skipped_invalid_series': True})
                continue
            parseable_count = sum(1 for x in arr if normalize_timestamp(x)[0] is not None)
            array_len = len(arr)
            null_ratio = col_profiles.get(c, {}).get('null_ratio', 1.0)
            score = (parseable_count, array_len, -null_ratio)
            tested.append({'col': c, 'parseable_count': parseable_count, 'array_len': array_len, 'null_ratio': null_ratio})
            if best_score is None or score > best_score:
                best_score = score
                best = c

        quality['timestamp_candidates_tested'].append({'row_index': int(idx), 'tested': tested})

        if best is None:
            # no timestamp source for this row
            other_counts = sum(len(v) for k,v in arrays.items())
            if other_counts > 0:
                quality['missing_timestamp_rows'].append(int(idx))
                quality['missing_timestamp_events'] += other_counts
            quality['rows_still_missing_timestamp_source'] += 1
            continue

        # record if fallback used
        if primary_ts and best != primary_ts:
            quality['rows_using_fallback_timestamp_source'] += 1

        # increment usage counts
        quality['timestamp_source_usage_counts'][best] = quality['timestamp_source_usage_counts'].get(best, 0) + 1

        ts_col = best
        ts_array = arrays.get(ts_col, []) if ts_col in arrays else ([row_dict.get(ts_col)] if row_dict.get(ts_col) is not None else [])

        # create one event per timestamp (timestamps anchor event count)
        event_count = len(ts_array)
        for i in range(event_count):
            ev = {
                'person_id_candidate': person_id,
                'event_sequence_index_raw': i,
                '_internal_row_index': int(idx),
                'timestamp_col_used': ts_col
            }
            # timestamp value
            ts_raw = ts_array[i] if i < len(ts_array) else None
            ev[ (ts_col + '_raw') if ts_col else 'timestamp_raw'] = ts_raw
            parsed_ts, parse_mode = normalize_timestamp(ts_raw) if ts_raw is not None else (None, 'null')
            if parsed_ts is None and ts_raw is not None:
                quality['unparsed_timestamp_count'] = quality.get('unparsed_timestamp_count',0) + 1
            if parsed_ts is not None:
                quality['parsed_timestamp_count'] = quality.get('parsed_timestamp_count',0) + 1
            ev['event_timestamp_parsed'] = parsed_ts.isoformat() if parsed_ts is not None else None
            ev['timestamp_source_type'] = ('array' if isinstance(arrays.get(ts_col, None), list) and len(arrays.get(ts_col, []))>1 else 'single')
            ev['timestamp_parse_mode'] = parse_mode

            # compute event alignment confidence
            confidence = 'low'
            if parsed_ts is not None:
                confidence = 'medium'
            if parsed_ts is not None and ev.get('lifecycle_stage_mapped') is not None:
                confidence = 'high'
            ev['event_alignment_confidence'] = confidence

            # for other timeline columns, take same index if exists, else None
            # track if event is fully aligned (all requested fields present)
            fields_present = 0
            fields_total = 0
            # lifecycle
            lc_col = quality['inferred_aliases'].get('timeline_lifecycle_source_col')
            life_raw = arrays.get(lc_col, [])[i] if lc_col and i < len(arrays.get(lc_col, [])) else None
            ev['lifecycle_stage_raw'] = life_raw
            # normalize before mapping (force uppercase then lookup)
            mapped_stage = None
            if life_raw is not None:
                try:
                    raw_stage_norm = str(life_raw).strip().upper()
                    mapped_stage = STAGE_MAP.get(raw_stage_norm)
                    if mapped_stage is None:
                        # fallback to map_stage for best-effort
                        mapped_stage = map_stage(life_raw)
                except Exception:
                    mapped_stage = map_stage(life_raw)
            ev['lifecycle_stage_mapped'] = mapped_stage
            if life_raw is not None:
                fields_present += 1
            if lc_col:
                fields_total += 1

            # activity code
            ac_col = quality['inferred_aliases'].get('timeline_activity_code_source_col')
            act_code_raw = arrays.get(ac_col, [])[i] if ac_col and i < len(arrays.get(ac_col, [])) else None
            ev['activity_code_raw'] = act_code_raw
            if ac_col:
                fields_total += 1
                if act_code_raw is not None:
                    fields_present += 1

            # activity label
            al_col = quality['inferred_aliases'].get('timeline_activity_label_source_col')
            act_label_raw = arrays.get(al_col, [])[i] if al_col and i < len(arrays.get(al_col, [])) else None
            ev['activity_label_raw'] = act_label_raw
            if al_col:
                fields_total += 1
                if act_label_raw is not None:
                    fields_present += 1

            # outcome
            out_col = quality['inferred_aliases'].get('timeline_outcome_source_col')
            outcome_raw = arrays.get(out_col, [])[i] if out_col and i < len(arrays.get(out_col, [])) else None
            ev['outcome_raw'] = outcome_raw
            if out_col:
                fields_total += 1
                if outcome_raw is not None:
                    fields_present += 1

            # notes
            notes_col = quality['inferred_aliases'].get('timeline_notes_source_col')
            notes_raw = arrays.get(notes_col, [])[i] if notes_col and i < len(arrays.get(notes_col, [])) else None
            ev['notes_raw'] = notes_raw
            if notes_col:
                fields_total += 1
                if notes_raw is not None:
                    fields_present += 1

            # count partial vs fully aligned
            if fields_total == 0:
                # no non-timestamp fields inferred — consider fully aligned for timestamp-only events
                quality['fully_aligned_events_count'] += 1
            else:
                if fields_present == fields_total:
                    quality['fully_aligned_events_count'] += 1
                else:
                    quality['partial_events_count'] += 1

            # preserve original arrays for audit (store as <col>_array_raw)
            for c in timeline_cols:
                ev[c + '_array_raw'] = arrays.get(c, [])

            events.append(ev)

    # Build person snapshot CSV (one row per original row)
    persons_df = pd.DataFrame(person_rows)
    persons_out = os.path.join(OUT_DIR,'person_snapshot.csv')
    persons_df.to_csv(persons_out, index=False)

    # Events long
    events_df = pd.DataFrame(events)
    # Ensure final columns for TAAIP and stable ordering
    required_event_cols = [
        'person_id_candidate',
        'event_timestamp_parsed',
        'lifecycle_stage_mapped',
        'activity_label_raw',
        'event_alignment_confidence'
    ]
    for c in required_event_cols:
        if c not in events_df.columns:
            events_df[c] = None
    final_event_cols = required_event_cols + [c for c in events_df.columns if c not in required_event_cols]
    events_df = events_df[final_event_cols]
    events_out = os.path.join(OUT_DIR,'funnel_events_long.csv')
    events_df.to_csv(events_out, index=False)

    # Summary derivation per person
    summary_rows = []
    grouped = events_df.groupby('person_id_candidate') if not events_df.empty else []
    for pid, g in grouped:
        # attempt to compute first/last seen — coerce to timezone-aware UTC to avoid mixed-type reductions
        times = pd.to_datetime(g['event_timestamp_parsed'], errors='coerce', utc=True)
        # ensure we only reduce over datetime64-like values
        if len(times.dropna()) == 0:
            first_seen = None
            last_seen = None
        else:
            first_seen = times.min()
            last_seen = times.max()
        latest_stage = g.sort_values(['event_sequence_index_raw']).iloc[-1]['lifecycle_stage_mapped'] if len(g)>0 else None
        terminal_outcome = g.sort_values(['event_sequence_index_raw']).iloc[-1].get('outcome_raw') if len(g)>0 else None
        def first_stage_time(stage_name):
            mask = g['lifecycle_stage_mapped'] == stage_name
            if mask.any():
                times_masked = pd.to_datetime(g[mask]['event_timestamp_parsed'], errors='coerce', utc=True)
                if len(times_masked.dropna()) == 0:
                    return None
                return times_masked.min()
            return None

        fs_appt = first_stage_time('Appointment')
        fs_test = first_stage_time('Test')
        fs_contract = first_stage_time('Contract')
        fs_ship = first_stage_time('Ship')

        def first_event(events_df, stage):
            subset = events_df[events_df['lifecycle_stage_mapped'] == stage]
            if subset.empty:
                return None
            times = pd.to_datetime(subset['event_timestamp_parsed'], errors='coerce', utc=True)
            if len(times.dropna()) == 0:
                return None
            return times.min()

        def days_between(a, b):
            if a is None or b is None: return None
            try:
                return int((pd.to_datetime(b) - pd.to_datetime(a)).days)
            except Exception:
                return None

        # derive milestone times
        person_events = g
        lead_at = first_event(person_events, 'Lead')
        app_at = first_event(person_events, 'Applicant')
        dep_at = first_event(person_events, 'DEP')
        ship_at = first_event(person_events, 'Ship')

        summary_rows.append({
            'person_id_candidate': pid,
            'lead_at': lead_at.isoformat() if lead_at is not None and pd.notna(lead_at) else None,
            'applicant_at': app_at.isoformat() if app_at is not None and pd.notna(app_at) else None,
            'dep_at': dep_at.isoformat() if dep_at is not None and pd.notna(dep_at) else None,
            'ship_at': ship_at.isoformat() if ship_at is not None and pd.notna(ship_at) else None,
            'days_to_applicant': days_between(lead_at, app_at),
            'days_to_dep': days_between(lead_at, dep_at),
            'days_to_ship': days_between(lead_at, ship_at),
            'event_count': int(len(g)),
        })

    summary_df = pd.DataFrame(summary_rows)
    # Ensure summary contains milestone columns expected by TAAIP
    required_summary_cols = [
        'person_id_candidate',
        'lead_at',
        'applicant_at',
        'dep_at',
        'ship_at',
        'days_to_applicant',
        'days_to_dep',
        'days_to_ship'
    ]
    for c in required_summary_cols:
        if c not in summary_df.columns:
            summary_df[c] = None
    final_summary_cols = required_summary_cols + [c for c in summary_df.columns if c not in required_summary_cols]
    summary_df = summary_df[final_summary_cols]
    summary_out = os.path.join(OUT_DIR,'funnel_summary.csv')
    summary_df.to_csv(summary_out, index=False)

    # finalize quality report
    quality['dropped_columns'] = []
    quality['inferred_mappings'] = list({v['column']: v['mapped_to'] for v in quality.get('inferred_mappings',[]) }.items())
    quality['row_count_persons'] = int(len(persons_df))
    quality['row_count_events'] = int(len(events_df))

    qout = os.path.join(OUT_DIR,'data_quality_report.json')
    with open(qout,'w') as f:
        json.dump(quality, f, indent=2, default=str)

    print('Wrote artifacts to', OUT_DIR)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: recalibrate_funnel_workbook.py /path/to/file.xlsx')
        sys.exit(1)
    recalibrate(sys.argv[1])
