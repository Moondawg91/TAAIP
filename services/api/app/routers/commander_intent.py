from fastapi import APIRouter

router = APIRouter(prefix="/commander_intent", tags=["commander_intent"])


@router.post("/rop")
def upload_rop():
    return {
        "status": "received",
        "parsed": False,
        "source": "stub"
    }


@router.post("/school_plan")
def upload_school_plan():
    return {
        "status": "received",
        "parsed": False,
        "source": "stub"
    }


@router.get("")
def get_commander_intent():
    return {
        "loes": [],
        "priorities": [],
        "focus_markets": [],
        "target_population": [],
        "source": "stub"
    }
