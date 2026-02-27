"""Importer registry (deterministic) for TAAIP ingest pipeline.
This provides a list of ImporterSpec-like dicts and helpers used by ingest.run_import
"""
from typing import List, Optional

# Minimal python representation of ImporterSpec - use plain dicts for simplicity

IMPORTERS = []

def _add(spec: dict):
    IMPORTERS.append(spec)
    return spec

# USAREC G2 — Enlistments by BDE
_add({
    'id': 'usarec_g2_enlistments_bde_v1',
    'displayName': 'USAREC G2 — Enlistments by BDE',
    'sourceSystem': 'USAREC_G2',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'USAREC_G2',
        'sheetNameHints': ['Enlist', 'BDE'],
        'requiredColumnsAnyOf': [
            ['BDE', 'ENLISTMENTS'],
            ['BRIGADE', 'ENLISTMENTS'],
            ['BDE', 'CONTRACTS'],
        ],
    },
    'sheets': [{'nameIncludes': ['Enlist', 'BDE'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'bde_name', 'required': True, 'aliases': ['BDE', 'BRIGADE'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'period', 'required': False, 'aliases': ['MONTH', 'PERIOD', 'FY', 'FISCAL YEAR'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'enlistments', 'required': False, 'aliases': ['ENLISTMENTS', 'CONTRACTS', 'ACCESSIONS'], 'type': 'int', 'clean': ['strip_commas', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'normalize_unit', 'args': {'echelon': 'BDE', 'from': 'bde_name', 'to': 'unit_rsid'}},
        {'fn': 'normalize_dates', 'args': {'from': 'period', 'to': ['period_start', 'period_end']}},
        {'fn': 'derive_grain', 'args': {'grain': 'BDE'}},
        {'fn': 'map_metrics_wide_to_long', 'args': {'map': [{'from': 'enlistments', 'metric': 'enlistments'}]}},
    ],
    'target': {'table': 'fact_enlistments', 'mode': 'upsert', 'primaryKey': ['unit_rsid', 'grain', 'period_start', 'metric_name']},
})

# USAREC G2 — Enlistments by BN
_add({
    'id': 'usarec_g2_enlistments_bn_v1',
    'displayName': 'USAREC G2 — Enlistments by BN',
    'sourceSystem': 'USAREC_G2',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'USAREC_G2',
        'sheetNameHints': ['Enlist', 'BN'],
        'requiredColumnsAnyOf': [['BN', 'ENLISTMENTS'], ['BATTALION', 'CONTRACTS']],
    },
    'sheets': [{'nameIncludes': ['Enlist', 'BN', 'Battalion'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'bn_name', 'required': True, 'aliases': ['BN', 'BATTALION'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'period', 'required': False, 'aliases': ['MONTH', 'PERIOD', 'FY'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'enlistments', 'required': True, 'aliases': ['ENLISTMENTS', 'CONTRACTS', 'ACCESSIONS'], 'type': 'int', 'clean': ['strip_commas', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'normalize_unit', 'args': {'echelon': 'BN', 'from': 'bn_name', 'to': 'unit_rsid'}},
        {'fn': 'normalize_dates', 'args': {'from': 'period', 'to': ['period_start', 'period_end']}},
        {'fn': 'derive_grain', 'args': {'grain': 'BN'}},
        {'fn': 'map_metrics_wide_to_long', 'args': {'map': [{'from': 'enlistments', 'metric': 'enlistments'}]}},
    ],
    'target': {'table': 'fact_enlistments', 'mode': 'upsert', 'primaryKey': ['unit_rsid', 'grain', 'period_start', 'metric_name']},
})

# USAREC G2 — Enlistments by CBSA
_add({
    'id': 'usarec_g2_enlistments_cbsa_v1',
    'displayName': 'USAREC G2 — Enlistments by CBSA',
    'sourceSystem': 'USAREC_G2',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'USAREC_G2',
        'sheetNameHints': ['CBSA', 'Enlist'],
        'requiredColumnsAnyOf': [['CBSA', 'ENLISTMENTS'], ['CBSA CODE', 'CONTRACTS']],
    },
    'sheets': [{'nameIncludes': ['CBSA', 'Enlist'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'cbsa_code', 'required': True, 'aliases': ['CBSA', 'CBSA CODE'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'cbsa_name', 'required': False, 'aliases': ['CBSA NAME', 'MARKET'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'period', 'required': False, 'aliases': ['MONTH', 'PERIOD', 'FY'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'enlistments', 'required': True, 'aliases': ['ENLISTMENTS', 'CONTRACTS'], 'type': 'int', 'clean': ['strip_commas', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'cbsa_lookup', 'args': {'codeField': 'cbsa_code', 'nameField': 'cbsa_name'}},
        {'fn': 'normalize_dates', 'args': {'from': 'period', 'to': ['period_start', 'period_end']}},
        {'fn': 'map_metrics_wide_to_long', 'args': {'map': [{'from': 'enlistments', 'metric': 'enlistments'}]}},
    ],
    'target': {'table': 'fact_enlistments', 'mode': 'upsert', 'primaryKey': ['cbsa_code', 'period_start', 'metric_name']},
})

# USAREC G2 — Urbanicity % by CBSA
_add({
    'id': 'usarec_g2_urbanicity_cbsa_v1',
    'displayName': 'USAREC G2 — Urbanicity % by CBSA',
    'sourceSystem': 'USAREC_G2',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'USAREC_G2',
        'sheetNameHints': ['Urban', 'CBSA'],
        'requiredColumnsAnyOf': [['CBSA', 'URBANICITY'], ['CBSA CODE', '% URBAN']],
    },
    'sheets': [{'nameIncludes': ['Urban', 'CBSA'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'cbsa_code', 'required': True, 'aliases': ['CBSA', 'CBSA CODE'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'cbsa_name', 'required': False, 'aliases': ['CBSA NAME', 'MARKET'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'urbanicity_pct', 'required': True, 'aliases': ['URBANICITY', '% URBAN', 'URBANICITY %'], 'type': 'percent', 'clean': ['percent_to_float', 'empty_to_null']},
    ],
    'transforms': [{'fn': 'cbsa_lookup', 'args': {'codeField': 'cbsa_code', 'nameField': 'cbsa_name'}}],
    'target': {'table': 'dim_market_cbsa', 'mode': 'upsert', 'primaryKey': ['cbsa_code']},
})

# USAREC G2 — Productivity Rates & Foxhole Recruiters
_add({
    'id': 'usarec_g2_productivity_foxhole_v1',
    'displayName': 'USAREC G2 — Productivity Rates & Foxhole Recruiters (2019–Present)',
    'sourceSystem': 'USAREC_G2',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'USAREC_G2',
        'sheetNameHints': ['Product', 'Foxhole', '2019'],
        'requiredColumnsAnyOf': [['RSID', 'PRODUCTIVITY'], ['STATION', 'PRODUCTIVITY RATE'], ['BN', 'PRODUCTIVITY']],
    },
    'sheets': [{'nameIncludes': ['Product', 'Foxhole'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'rsid', 'required': False, 'aliases': ['RSID', 'STN RSID', 'STATION RSID'], 'type': 'string', 'clean': ['trim', 'upper']},
        {'canonical': 'stn_name', 'required': False, 'aliases': ['STATION', 'STN'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'period', 'required': True, 'aliases': ['MONTH', 'DATE', 'PERIOD'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'productivity_rate', 'required': False, 'aliases': ['PRODUCTIVITY', 'PRODUCTIVITY RATE'], 'type': 'float', 'clean': ['strip_commas', 'empty_to_null']},
        {'canonical': 'foxhole_flag', 'required': False, 'aliases': ['FOXHOLE', 'FOXHOLE RECRUITER'], 'type': 'string', 'clean': ['trim', 'upper', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'normalize_unit', 'args': {'echelon': 'STN', 'from': ['rsid', 'stn_name'], 'to': 'unit_rsid'}},
        {'fn': 'normalize_dates', 'args': {'from': 'period', 'to': ['period_start', 'period_end']}},
        {'fn': 'derive_grain', 'args': {'grain': 'STN'}},
        {'fn': 'map_metrics_wide_to_long', 'args': {'map': [
            {'from': 'productivity_rate', 'metric': 'productivity_rate'},
            {'from': 'foxhole_flag', 'metric': 'foxhole_flag'}
        ]}},
    ],
    'target': {'table': 'fact_productivity', 'mode': 'upsert', 'primaryKey': ['unit_rsid', 'period_start', 'metric_name']},
})

# USAREC G2 — Act+Res SAMA ZIP Potential
_add({
    'id': 'usarec_g2_sama_zip_v1',
    'displayName': 'USAREC G2 — Act+Res SAMA ZIP Potential',
    'sourceSystem': 'USAREC_G2',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'USAREC_G2',
        'sheetNameHints': ['SAMA', 'ZIP'],
        'requiredColumnsAnyOf': [['ZIP', 'RSID'], ['ZIP CODE', 'STATION'], ['ZIP', 'CATEGORY']],
    },
    'sheets': [{'nameIncludes': ['SAMA', 'ZIP'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'zip', 'required': True, 'aliases': ['ZIP', 'ZIP CODE'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'rsid', 'required': False, 'aliases': ['RSID', 'STN RSID'], 'type': 'string', 'clean': ['trim', 'upper']},
        {'canonical': 'category', 'required': False, 'aliases': ['CATEGORY', 'SEGMENT'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'value', 'required': False, 'aliases': ['VALUE', 'COUNT', 'POP', 'TOTAL'], 'type': 'float', 'clean': ['strip_commas', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'zip_to_unit_lookup', 'args': {'zipField': 'zip', 'rsidField': 'rsid', 'to': 'unit_rsid'}},
        {'fn': 'map_metrics_wide_to_long', 'args': {'map': [{'from': 'value', 'metric': 'sama_value'}]}},
    ],
    'target': {'table': 'fact_zip_potential', 'mode': 'upsert', 'primaryKey': ['zip', 'category', 'metric_name']},
})

# USAREC G2 — ZIP Code by Category Report
_add({
    'id': 'usarec_g2_zip_category_report_v1',
    'displayName': 'USAREC G2 — ZIP Code by Category Report',
    'sourceSystem': 'USAREC_G2',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'USAREC_G2',
        'sheetNameHints': ['Category', 'ZIP'],
        'requiredColumnsAnyOf': [['ZIP', 'CATEGORY'], ['ZIP CODE', 'CATEGORY']],
    },
    'sheets': [{'nameIncludes': ['Category', 'ZIP'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'zip', 'required': True, 'aliases': ['ZIP', 'ZIP CODE'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'category', 'required': True, 'aliases': ['CATEGORY', 'SEGMENT'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'value', 'required': True, 'aliases': ['VALUE', 'COUNT', 'TOTAL'], 'type': 'float', 'clean': ['strip_commas', 'empty_to_null']},
        {'canonical': 'as_of', 'required': False, 'aliases': ['AS OF', 'THRU', 'RUN DATE'], 'type': 'date', 'clean': ['trim', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'map_metrics_wide_to_long', 'args': {'map': [{'from': 'value', 'metric': 'zip_category_value'}]}},
    ],
    'target': {'table': 'fact_zip_potential', 'mode': 'upsert', 'primaryKey': ['zip', 'category', 'metric_name']},
})

# School Contacts
_add({
    'id': 'school_contacts_v1',
    'displayName': 'Schools — Contacts',
    'sourceSystem': 'OTHER',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'OTHER',
        'sheetNameHints': ['contact', 'school'],
        'requiredColumnsAnyOf': [['SCHOOL', 'CONTACT'], ['SCHOOL NAME', 'EMAIL']],
    },
    'sheets': [{'nameIncludes': ['contact', 'school'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'school_name', 'required': True, 'aliases': ['SCHOOL', 'SCHOOL NAME'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'contact_name', 'required': True, 'aliases': ['CONTACT', 'CONTACT NAME'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'contact_type', 'required': False, 'aliases': ['ROLE', 'TYPE', 'TITLE'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'email', 'required': False, 'aliases': ['EMAIL', 'E-MAIL'], 'type': 'string', 'clean': ['trim', 'lower', 'empty_to_null']},
        {'canonical': 'phone', 'required': False, 'aliases': ['PHONE', 'TELEPHONE'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'city', 'required': False, 'aliases': ['CITY'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'state', 'required': False, 'aliases': ['STATE', 'ST'], 'type': 'string', 'clean': ['trim', 'upper', 'empty_to_null']},
        {'canonical': 'zip', 'required': False, 'aliases': ['ZIP', 'ZIP CODE'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
    ],
    'transforms': [],
    'target': {'table': 'fact_school_contacts', 'mode': 'append', 'primaryKey': []},
})

# School Contracts
_add({
    'id': 'school_contracts_v1',
    'displayName': 'Schools — Contracts',
    'sourceSystem': 'OTHER',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'OTHER',
        'sheetNameHints': ['contract', 'school'],
        'requiredColumnsAnyOf': [['SCHOOL', 'CONTRACT'], ['SCHOOL NAME', 'STATUS']],
    },
    'sheets': [{'nameIncludes': ['contract', 'school'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'school_name', 'required': True, 'aliases': ['SCHOOL', 'SCHOOL NAME'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'contract_type', 'required': False, 'aliases': ['CONTRACT TYPE', 'TYPE'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'status', 'required': False, 'aliases': ['STATUS'], 'type': 'string', 'clean': ['trim', 'upper', 'empty_to_null']},
        {'canonical': 'start_date', 'required': False, 'aliases': ['START', 'START DATE'], 'type': 'date', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'end_date', 'required': False, 'aliases': ['END', 'END DATE'], 'type': 'date', 'clean': ['trim', 'empty_to_null']},
    ],
    'transforms': [],
    'target': {'table': 'fact_school_contracts', 'mode': 'append', 'primaryKey': []},
})

# Mission Category 2
_add({
    'id': 'mission_category_2_v1',
    'displayName': 'Mission — Category 2',
    'sourceSystem': 'FS_MGMT',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'FS_MGMT',
        'sheetNameHints': ['Mission', 'Category'],
        'requiredColumnsAnyOf': [['BN', 'CATEGORY'], ['RSID', 'MISSION']],
    },
    'sheets': [{'nameIncludes': ['Mission', 'Category'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'unit_name', 'required': True, 'aliases': ['BN', 'BATTALION', 'CO', 'COMPANY', 'STATION', 'RSID'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'mission_category', 'required': True, 'aliases': ['CATEGORY', 'MISSION CATEGORY'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'period', 'required': False, 'aliases': ['MONTH', 'PERIOD', 'FY'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'value', 'required': True, 'aliases': ['VALUE', 'COUNT', 'MISSION'], 'type': 'float', 'clean': ['strip_commas', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'normalize_unit', 'args': {'from': 'unit_name', 'to': 'unit_rsid'}},
        {'fn': 'normalize_dates', 'args': {'from': 'period', 'to': ['period_start', 'period_end']}},
        {'fn': 'map_metrics_wide_to_long', 'args': {'map': [{'from': 'value', 'metric': 'mission_value'}]}},
    ],
    'target': {'table': 'fact_mission_category', 'mode': 'upsert', 'primaryKey': ['unit_rsid', 'mission_category', 'period_start', 'metric_name']},
})

# ALRL Data
_add({
    'id': 'alrl_data_v1',
    'displayName': 'ALRL — Loader/Readiness Export',
    'sourceSystem': 'ALRL',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'ALRL',
        'sheetNameHints': ['ALRL', 'Loader', 'Readiness'],
        'requiredColumnsAnyOf': [['RSID', 'VALUE'], ['STATION', 'VALUE'], ['UNIT', 'METRIC']],
    },
    'sheets': [{'nameIncludes': ['ALRL', 'Loader', 'Readiness'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'rsid', 'required': False, 'aliases': ['RSID', 'STN RSID'], 'type': 'string', 'clean': ['trim', 'upper', 'empty_to_null']},
        {'canonical': 'unit_name', 'required': False, 'aliases': ['UNIT', 'STATION', 'STN'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'metric_name', 'required': True, 'aliases': ['METRIC', 'MEASURE', 'KPI'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'metric_value', 'required': True, 'aliases': ['VALUE', 'AMOUNT', 'COUNT'], 'type': 'float', 'clean': ['strip_commas', 'empty_to_null']},
        {'canonical': 'period', 'required': False, 'aliases': ['DATE', 'MONTH', 'PERIOD'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'normalize_unit', 'args': {'echelon': 'STN', 'from': ['rsid', 'unit_name'], 'to': 'unit_rsid'}},
        {'fn': 'normalize_dates', 'args': {'from': 'period', 'to': ['period_start', 'period_end']}},
    ],
    'target': {'table': 'fact_alrl', 'mode': 'upsert', 'primaryKey': ['unit_rsid', 'period_start', 'metric_name']},
})

# EMM Portal
_add({
    'id': 'emm_portal_v1',
    'displayName': 'EMM Portal — Export',
    'sourceSystem': 'EMM_PORTAL',
    'accepts': {'fileTypes': ['xlsx']},
    'fingerprint': {
        'sourceSystem': 'EMM_PORTAL',
        'sheetNameHints': ['EMM', 'Portal'],
        'requiredColumnsAnyOf': [['RSID', 'METRIC'], ['STATION', 'DATE'], ['BN', 'TOTAL']],
    },
    'sheets': [{'nameIncludes': ['EMM', 'Portal'], 'headerRow': 0}],
    'columns': [
        {'canonical': 'rsid', 'required': False, 'aliases': ['RSID', 'STN RSID'], 'type': 'string', 'clean': ['trim', 'upper', 'empty_to_null']},
        {'canonical': 'unit_name', 'required': False, 'aliases': ['STATION', 'BN', 'BATTALION', 'UNIT'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
        {'canonical': 'metric_name', 'required': True, 'aliases': ['METRIC', 'MEASURE', 'KPI'], 'type': 'string', 'clean': ['trim']},
        {'canonical': 'metric_value', 'required': True, 'aliases': ['VALUE', 'TOTAL', 'COUNT'], 'type': 'float', 'clean': ['strip_commas', 'empty_to_null']},
        {'canonical': 'period', 'required': False, 'aliases': ['DATE', 'MONTH', 'PERIOD', 'AS OF'], 'type': 'string', 'clean': ['trim', 'empty_to_null']},
    ],
    'transforms': [
        {'fn': 'normalize_unit', 'args': {'from': ['rsid', 'unit_name'], 'to': 'unit_rsid'}},
        {'fn': 'normalize_dates', 'args': {'from': 'period', 'to': ['period_start', 'period_end']}},
    ],
    'target': {'table': 'fact_emm', 'mode': 'upsert', 'primaryKey': ['unit_rsid', 'period_start', 'metric_name']},
})

# Unknown dataset fallback (staging)
_add({
    'id': 'unknown_dataset_v1',
    'displayName': 'Unknown Dataset (staging)',
    'sourceSystem': 'OTHER',
    'accepts': {'fileTypes': ['xlsx', 'csv']},
    'fingerprint': {'sourceSystem': 'OTHER', 'sheetNameHints': [], 'requiredColumnsAnyOf': []},
    'sheets': [],
    'columns': [],
    'transforms': [],
    'target': {'table': 'stg_raw_dataset', 'mode': 'append', 'primaryKey': []},
})


def get_importer(importer_id: str) -> Optional[dict]:
    for s in IMPORTERS:
        if s['id'] == importer_id:
            return s
    return None


def list_importers() -> List[dict]:
    return IMPORTERS
