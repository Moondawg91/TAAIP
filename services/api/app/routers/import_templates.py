from fastapi import APIRouter

router = APIRouter()

@router.get('/import/templates')
def list_templates():
    templates = [
        {
            'dataset_key': 'SAMA_ZIP_FACT',
            'table_name': 'market_sama_zip_fact',
            'required_columns': ['zip_code','army_potential','dod_potential'],
            'optional_columns': ['station_rsid','zip_category','contracts','potential_remaining','p2p'],
            'column_aliases': { 'ZIP': 'zip_code', 'ARMY_POT': 'army_potential', 'POT_REMAIN':'potential_remaining' }
        },
        {
            'dataset_key': 'CBSA_FACT',
            'table_name': 'market_cbsa_fact',
            'required_columns': ['cbsa_code','value'],
            'optional_columns': ['cbsa_name','dma_name','p2p','market_category'],
            'column_aliases': { 'CBSA':'cbsa_code', 'VALUE':'value' }
        },
        {
            'dataset_key': 'DEMOGRAPHICS_FACT',
            'table_name': 'market_demographics_fact',
            'required_columns': ['geo_type','geo_id','population_type','population_value'],
            'optional_columns': ['race_ethnicity','gender','production_value','p2p'],
            'column_aliases': { 'GEO':'geo_type', 'GEOID':'geo_id' }
        },
        {
            'dataset_key': 'GEOTARGET_ZONES',
            'table_name': 'market_geotarget_zone',
            'required_columns': ['name','zone_type'],
            'optional_columns': ['zip_list','cbsa_list','geojson','rsid_prefix'],
            'column_aliases': { 'NAME':'name', 'ZIPS':'zip_list' }
        }
    ]
    # school recruiting templates
    templates.extend([
        {
            'dataset_key': 'SCHOOL_DIM',
            'table_name': 'schools',
            'required_columns': ['id','school_name','school_type','city','state','zip_code'],
            'optional_columns': ['district','latitude','longitude'],
            'example': { 'id': 'SCH-0001', 'school_name': 'Central High', 'school_type': 'HS', 'city': 'Columbus', 'state': 'OH', 'zip_code': '43004' }
        },
        {
            'dataset_key': 'SCHOOL_ACCOUNTS',
            'table_name': 'school_accounts',
            'required_columns': ['id','school_id','assigned_station_rsid'],
            'optional_columns': ['assigned_company_prefix','assigned_battalion_prefix','assigned_brigade_prefix','last_contacted_at','status','notes'],
            'example': { 'id': 'SA-1', 'school_id': 'SCH-0001', 'assigned_station_rsid': 'STN-001', 'status': 'active' }
        },
        {
            'dataset_key': 'SCHOOL_CONTACTS',
            'table_name': 'school_contacts',
            'required_columns': ['id','school_id','contact_name','contact_role'],
            'optional_columns': ['email','phone'],
            'example': { 'id': 'SC-1', 'school_id': 'SCH-0001', 'contact_name': 'Jane Doe', 'contact_role': 'Guidance Counselor', 'email': 'jane@example.com' }
        },
        {
            'dataset_key': 'SCHOOL_ACTIVITIES',
            'table_name': 'school_activities',
            'required_columns': ['id','school_id','activity_type','activity_date'],
            'optional_columns': ['station_rsid','outcome','notes'],
            'example': { 'id': 'SACT-1', 'school_id': 'SCH-0001', 'activity_type': 'visit', 'activity_date': '2026-03-01T12:00:00Z' }
        },
        {
            'dataset_key': 'SCHOOL_MILESTONES',
            'table_name': 'school_milestones',
            'required_columns': ['id','school_id','milestone_type','milestone_date'],
            'optional_columns': ['linked_event_id'],
            'example': { 'id': 'M-1', 'school_id': 'SCH-0001', 'milestone_type': 'FAFSA Night', 'milestone_date': '2026-10-01' }
        },
        {
            'dataset_key': 'SCHOOL_PROGRAM_LEADS',
            'table_name': 'school_program_leads',
            'required_columns': ['id','lead_id','school_id'],
            'optional_columns': ['source_tag'],
            'example': { 'id': 'L-1', 'lead_id': 'LEAD-1', 'school_id': 'SCH-0001', 'source_tag': 'career_fair' }
        }
    ])
    return {'status':'ok','templates': templates}

@router.get('/import/templates/{dataset_key}')
def get_template(dataset_key: str):
    res = list_templates()
    for t in res['templates']:
        if t['dataset_key'] == dataset_key:
            return {'status':'ok','template': t}
    return {'status':'ok','template': None}
