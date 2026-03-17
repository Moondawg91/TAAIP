from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from ..services import fusion_engine
from .rbac import require_perm

router = APIRouter()


@router.post('/v2/fusion/run')
def run_fusion(unit_rsid: Optional[str] = None, as_of_date: Optional[str] = None, user: dict = Depends(require_perm('pages.command_center.view'))):
    try:
        out = fusion_engine.run_fusion(unit_rsid=unit_rsid, as_of_date=as_of_date)
        return {'status': 'ok', 'fusion_run_id': out.get('fusion_run_id'), 'inserted': out.get('inserted'), 'rows': out.get('rows')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/v2/fusion/latest')
def get_latest(unit_rsid: Optional[str] = None, as_of_date: Optional[str] = None, limit: int = 100, user: dict = Depends(require_perm('pages.command_center.view'))):
    try:
        rows = fusion_engine.latest_recommendations(unit_rsid=unit_rsid, as_of_date=as_of_date, limit=limit)
        return {'status': 'ok', 'count': len(rows), 'rows': rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
