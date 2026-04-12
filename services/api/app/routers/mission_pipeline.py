"""Orchestration router: extract from document text, then run mission bundle assessment.

This is a lightweight, in-process pipeline that reuses the extraction and
bundle assessment stubs. No AI, no persistence, no uploads.
"""
from typing import Any, Dict
from fastapi import APIRouter, Body

router = APIRouter()

from services.api.app.routers import mission_extraction
from services.api.app.routers import mission_bundle


@router.post("/mission_pipeline/assess_from_text")
def assess_from_text(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Accepts raw document text, runs extraction, then runs the mission bundle.

    Expected input: { document_type, document_text, recommendations }
    """
    document_type = payload.get("document_type")
    document_text = payload.get("document_text", "")
    recommendations = payload.get("recommendations", []) or []

    # Reuse extraction stub
    try:
        req = mission_extraction.ExtractionRequest(document_type=document_type or "", document_text=document_text)
        extraction = mission_extraction.extract_stub(req)
    except Exception:
        extraction = {"document_type": document_type, "extracted_alignment": {}, "status": "extraction_stub_ready"}

    # Prepare mission_bundle payload: mission_alignment + recommendations
    try:
        bundle_payload = {"mission_alignment": extraction.get("extracted_alignment") or {}, "recommendations": recommendations}
        assessment = mission_bundle.mission_bundle_assess(bundle_payload)
    except Exception:
        assessment = {"alignment": {"scores": [], "summary": {}}, "targeting": {"recommended_focus": {"markets": [], "school_segments": [], "engagement_types": [], "targeting_notes": []}, "status": "targeting_stub_ready"}, "status": "mission_bundle_ready"}

    return {
        "extraction": extraction,
        "assessment": assessment,
        "status": "mission_pipeline_ready",
    }
