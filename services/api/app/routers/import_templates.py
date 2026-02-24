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
    return {'status':'ok','templates': templates}

@router.get('/import/templates/{dataset_key}')
def get_template(dataset_key: str):
    res = list_templates()
    for t in res['templates']:
        if t['dataset_key'] == dataset_key:
            return {'status':'ok','template': t}
    return {'status':'ok','template': None}
