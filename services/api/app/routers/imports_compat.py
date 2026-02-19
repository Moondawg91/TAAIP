from fastapi import APIRouter, Body
from typing import Any, Dict
from .imports import parse_job_v3

router = APIRouter(prefix="/imports", tags=["imports_compat"])


@router.post('/preview')
def preview(payload: Dict[str, Any] = Body(...)):
    """Compatibility preview endpoint that delegates to existing import parse logic.

    Expects payload with `import_job_id`.
    """
    return parse_job_v3(payload)
