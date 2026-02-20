from fastapi import APIRouter
from typing import List, Dict

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get('/routes')
def list_routes() -> Dict[str, List[str]]:
    """Return registered route paths for introspection."""
    try:
        from services.api.app import main as mainmod
        paths = [r.path for r in mainmod.app.routes]
        return {'routes': sorted(list(set(paths)))}
    except Exception:
        return {'routes': []}


@router.get('/funding_sources')
def funding_sources():
    # Return canonical funding source taxonomy and optional permission hints
    return {
        'funding_sources': [
            {'key': 'USAREC_BDE_FUNDS', 'label': 'USAREC / BDE Funds'},
            {'key': 'BATTALION_FUNDS', 'label': 'Battalion Funds'},
            {'key': 'LOCAL_AMP_LAMP', 'label': 'Local AMP / LAMP'},
            {'key': 'DIRECT_AMP_DAMP', 'label': 'Direct AMP / DAMP'},
            {'key': 'DIRECT_FUNDS_LOCAL', 'label': 'Direct Funds (Local)'},
            {'key': 'ADVERTISING_FUNDS_NATIONAL', 'label': 'Advertising Funds (National)', 'permission': 'advertising_access'}
        ]
    }
