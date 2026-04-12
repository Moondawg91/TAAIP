from fastapi import APIRouter, Response

router = APIRouter()

@router.get('/debug/org_test')
def org_test_page():
    html = '''<!doctype html>
<html><head><meta charset="utf-8"><title>Org Test</title></head><body>
<script>
// set selection in localStorage then redirect to command-center
const sel = {
  root_rsid: 'USAREC',
  bde: { rsid: '1BDE', display_name: '1st Recruiting Brigade', echelon: 'BDE' },
  bn: null, co: null, stn: null,
  active: { rsid: '1BDE', display_name: '1st Recruiting Brigade', echelon: 'BDE' },
  effective_rsid: '1BDE'
};
try{ localStorage.setItem('taaip.unitSelection.v1', JSON.stringify(sel)); }catch(e){}
location.href = '/command-center';
</script>
</body></html>'''
    return Response(content=html, media_type='text/html')
