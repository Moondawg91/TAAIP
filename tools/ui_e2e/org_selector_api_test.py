import urllib.request, json, sys
import pytest

BASE='http://127.0.0.1:8000/api/v2/org'

def fetch(path):
    url = BASE + path
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print('ERROR', url, e)
        return None

print('Fetching root...')
root = fetch('/root')
print(json.dumps(root, indent=2)[:1000])

brigades = root.get('brigades', []) if isinstance(root, dict) else []
if not brigades:
    print('No brigades found')
    pytest.skip('No brigades found from org API; skipping environment-dependent e2e test', allow_module_level=True)

first_bde = brigades[0]
rsid = first_bde.get('rsid') or first_bde.get('unit_rsid') or first_bde.get('unit_key')
print('First brigade rsid:', rsid)

bde_children = fetch(f'/units?parent_key={rsid}&echelon=BDE')
print('BDE children:', json.dumps(bde_children, indent=2)[:1000])

# next level BN
bn_list = bde_children.get('units') if bde_children else []
if bn_list:
    bn_rsid = bn_list[0].get('rsid')
    print('First BN rsid:', bn_rsid)
    bn_children = fetch(f'/units?parent_key={bn_rsid}&echelon=BN')
    print('BN children:', json.dumps(bn_children, indent=2)[:1000])
else:
    print('No BN units found under brigade')

print('Done')
