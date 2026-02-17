"""
Mapping profiles for USAREC datasets.
"""
USAREC_ZIP_CATEGORY_REPORT = {
    'profile_id': 'usarec_zip_category_v1',
    'dataset_type': 'USAREC_ZIP_CATEGORY_REPORT',
    'synonyms': {
        'org': ['org', 'organization', 'command'],
        'stn': ['stn', 'station', 'station_code'],
        'zip_code': ['zip', 'zip code', 'zipcode', 'postal code'],
        'category': ['category', 'cat', 'zip category'],
        'contracts': ['contracts', 'contract_count', 'contract'],
        'share_pct': ['share', '% share', 'market share', 'share_pct'],
        'report_through_date': ['report through date', 'through', 'report_date']
    },
    'required_fields': ['org', 'stn', 'zip_code', 'category']
}

USAREC_MARKET_CONTRACTS_SHARE = {
    'profile_id': 'usarec_market_contracts_v1',
    'dataset_type': 'USAREC_MARKET_CONTRACTS_SHARE',
    'synonyms': {
        'org': ['org', 'organization', 'command'],
        'stn': ['stn', 'station', 'station_code'],
        'zip_code': ['zip', 'zip code', 'zipcode'],
        'service': ['service', 'svc'],
        'contracts': ['contracts', 'contract_count'],
        'share_pct': ['share', '% share', 'market share', 'share_pct'],
        'fy': ['fy', 'fiscal_year'],
        'ry': ['ry', 'report_year']
    },
    'required_fields': ['org', 'stn', 'zip_code', 'service']
}

DEFAULT_PROFILES = {
    'USAREC_ZIP_CATEGORY_REPORT': USAREC_ZIP_CATEGORY_REPORT,
    'USAREC_MARKET_CONTRACTS_SHARE': USAREC_MARKET_CONTRACTS_SHARE,
}
