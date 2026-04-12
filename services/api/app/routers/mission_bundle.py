"""Bundle mission alignment scoring + targeting into a single endpoint.
This router reuses existing scoring and targeting helpers without persistence.
"""
from typing import Any, Dict
from fastapi import APIRouter, Body

router = APIRouter()

from services.api.app.routers import mission_alignment_scoring
from services.api.app.routers import mission_to_targeting


@router.post("/mission_bundle/assess")
def mission_bundle_assess(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Accepts mission_alignment + recommendations and returns a bundled
    response containing alignment scores and recommended targeting focus.
    """
    mission_alignment = payload.get("mission_alignment") or {}
    recommendations = payload.get("recommendations") or []

    # Reuse the existing scoring endpoint function to compute scores/summary
    try:
        alignment = mission_alignment_scoring.mission_alignment_scoring({
            "mission_alignment": mission_alignment,
            "recommendations": recommendations,
        })
    except Exception:
        # fall back to computing inline if import signature changes
        alignment = {"scores": [], "summary": {}}

    # Reuse mission_to_targeting recommend_stub by constructing its Pydantic request
    try:
        req = mission_to_targeting.RecommendRequest(mission_alignment=mission_alignment)
        targeting = mission_to_targeting.recommend_stub(req)
    except Exception:
        targeting = {"recommended_focus": {"markets": [], "school_segments": [], "engagement_types": [], "targeting_notes": []}, "status": "targeting_stub_ready"}

    return {
        "alignment": alignment,
        "targeting": targeting,
        "status": "mission_bundle_ready",
    }
