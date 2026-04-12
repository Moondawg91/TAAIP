from services.api.app.routers.v2_coa_compare import coa_compare

if __name__ == '__main__':
    out = coa_compare(unit_rsid='STN_DEMO_01')
    import json
    print(json.dumps(out, indent=2, default=str))
