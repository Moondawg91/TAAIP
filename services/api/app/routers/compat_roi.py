from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix='/roi', tags=['compat'])


@router.api_route('', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
async def _root(request: Request):
    # preserve querystring
    q = request.url.query
    target = '/api/v1/roi'
    if q:
        target = f"{target}?{q}"
    return RedirectResponse(target, status_code=307)


@router.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
async def _proxy(path: str, request: Request):
    # preserve path and querystring
    q = request.url.query
    target = f'/api/v1/roi/{path}'
    if q:
        target = f"{target}?{q}"
    return RedirectResponse(target, status_code=307)
