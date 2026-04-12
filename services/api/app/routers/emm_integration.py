from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/emm", tags=["emm"])


def get_emm_status():
    return {
        "emm_available": True,
        "emm_portal_available": True,
        "last_sync": None,
        "data_source": "stub"
    }


@router.get("/status")
def emm_status_endpoint():
    return get_emm_status()


@router.get("/events")
def get_emm_events():
    return {
        "events": [],
        "source": "stub",
        "note": "EMM integration not yet connected"
    }


@router.get("/roi")
def get_emm_roi():
    return {
        "roi_data": [],
        "source": "stub"
    }


@router.get("/assets")
def get_emm_assets():
    return {
        "available_assets": [],
        "source": "stub"
    }
