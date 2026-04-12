from fastapi import APIRouter, Body

router = APIRouter(prefix="/commander_intent", tags=["commander_intent_ingest"])

from services.api.app.data import commander_intent_store as store


@router.post('/rop_ingest')
def rop_ingest(payload: dict = Body(...)):
    store.save_rop(payload)
    return {
        'status': 'stored',
        'source_type': payload.get('source_type', 'ROP'),
        'fy': payload.get('fy')
    }


@router.post('/school_plan_ingest')
def school_plan_ingest(payload: dict = Body(...)):
    store.save_school_plan(payload)
    return {
        'status': 'stored',
        'source_type': payload.get('source_type', 'SCHOOL_PLAN'),
        'fy': payload.get('fy')
    }


@router.get('/current')
def get_current_intent():
    return store.get_current_intent()
