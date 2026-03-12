from fastapi import APIRouter
import os
from ..routers.rbac import get_current_user

router = APIRouter()


@router.get('/v2/auth/status')
def auth_status():
    mode = os.getenv('AUTH_MODE') or os.getenv('LOCAL_DEV_AUTH_BYPASS') and 'dev' or 'unknown'
    enabled = (mode != 'unknown')
    user = None
    try:
        # best-effort: if a dev bypass is enabled return a synthetic user
        user = get_current_user.__wrapped__({}) if hasattr(get_current_user, '__wrapped__') else None
    except Exception:
        user = None
    return {'enabled': enabled, 'mode': mode, 'user': user}
