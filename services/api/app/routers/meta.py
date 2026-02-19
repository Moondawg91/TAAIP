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
