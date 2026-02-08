"""
Mapping profiles for DoD datasets.
"""
DOD_STN_ZIP_SERVICE_LOOKUP = {
    'profile_id': 'dod_stn_zip_service_v1',
    'dataset_type': 'DOD_STN_ZIP_SERVICE_LOOKUP',
    'synonyms': {
        'org': ['org', 'organization', 'command'],
        'station': ['station', 'station_name'],
        'zip_code': ['zip', 'zip code', 'zipcode'],
        'service': ['service', 'svc'],
        'stn': ['stn', 'station_code']
    },
    'required_fields': ['org', 'station', 'zip_code']
}

DEFAULT_PROFILES = {
    'DOD_STN_ZIP_SERVICE_LOOKUP': DOD_STN_ZIP_SERVICE_LOOKUP,
}
