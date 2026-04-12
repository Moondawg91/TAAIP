from fastapi import APIRouter

router = APIRouter(prefix="/emm_sync", tags=["emm_sync"])


@router.get("/calendar")
def get_emm_calendar_sync():
    return {
        "synced": [],
        "source": "stub",
        "purpose": "command calendar / event schedule"
    }


@router.get("/budget")
def get_emm_budget_sync():
    return {
        "synced": [],
        "source": "stub",
        "purpose": "event budget / marketing spend / funding trace"
    }


@router.get("/leads")
def get_emm_leads_sync():
    return {
        "synced": [],
        "source": "stub",
        "purpose": "lead import for ROI + funnel linkage"
    }


@router.get("/roi")
def get_emm_roi_sync():
    return {
        "synced": [],
        "source": "stub",
        "purpose": "event effectiveness / ROI linkage"
    }
