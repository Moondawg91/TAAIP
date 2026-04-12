"""Mission extraction placeholder router.

Provides a simple, heuristic extraction endpoint that converts plain
document text into a structured mission-alignment-like object. This is
intentionally lightweight: no AI, no persistence, no upload handling.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()


class ExtractionRequest(BaseModel):
    document_type: str
    document_text: str


@router.post("/mission_extraction/extract_stub")
def extract_stub(payload: ExtractionRequest) -> Dict[str, Any]:
    text = (payload.document_text or "").lower()

    extracted = {
        "commander_intent": "",
        "mission_statement": "",
        "priorities": [],
        "loes": [],
        "targeting_guidance": [],
        "school_recruiting_guidance": [],
    }

    # Simple keyword-based heuristics (no AI)
    if "commander intent" in text:
        extracted["commander_intent"] = "extracted commander intent placeholder"

    if "mission statement" in text:
        extracted["mission_statement"] = "extracted mission statement placeholder"

    if "priority" in text or "priorities" in text:
        extracted["priorities"].append("detected_priority")

    if "loe" in text or "line of effort" in text:
        extracted["loes"].append("detected_loe")

    if "targeting guidance" in text:
        extracted["targeting_guidance"].append("detected_targeting_guidance")

    if "school recruiting guidance" in text or "school engagement" in text:
        extracted["school_recruiting_guidance"].append("detected_school_guidance")

    return {
        "document_type": payload.document_type,
        "extracted_alignment": extracted,
        "status": "extraction_stub_ready",
    }
