from typing import Any, Dict
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException

router = APIRouter()


@router.get("/mission_documents/types")
def mission_document_types() -> Dict[str, Any]:
    return {"document_types": ["rop", "school_recruiting_plan"]}


@router.post("/mission_documents/register_stub")
def register_stub(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    doc_type = payload.get("document_type")
    title = payload.get("title")
    fy = payload.get("fy")
    unit = payload.get("unit")
    notes = payload.get("notes")

    if doc_type not in ("rop", "school_recruiting_plan"):
        raise HTTPException(status_code=400, detail="unsupported document_type")
    if not title or not fy or not unit:
        raise HTTPException(status_code=400, detail="missing required fields (title, fy, unit)")

    document_id = f"stub-{uuid4().hex}"
    return {
        "document_id": document_id,
        "document_type": doc_type,
        "title": title,
        "fy": fy,
        "unit": unit,
        "notes": notes,
        "status": "registered_stub",
    }


def _has_keyword(text: str, kws) -> bool:
    if not text: return False
    t = text.lower()
    for k in kws:
        if k.lower() in t:
            return True
    return False


@router.post("/mission_documents/analyze_stub")
def analyze_stub(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    doc_type = payload.get("document_type")
    text = payload.get("document_text") or ""

    if doc_type not in ("rop", "school_recruiting_plan"):
        raise HTTPException(status_code=400, detail="unsupported document_type")

    # simple keyword presence checks
    extractable = {
        "commander_intent": _has_keyword(text, ["commander intent", "commander:'", "commander:" , "commander's intent"]),
        "mission_statement": _has_keyword(text, ["mission statement", "mission:", "mission statement:"] ),
        "priorities": _has_keyword(text, ["priority", "priorities"]),
        "loes": _has_keyword(text, ["loe", "line of effort", "lines of effort"]),
        "targeting_guidance": _has_keyword(text, ["targeting guidance", "targeting", "target guidance", "target"]),
        "school_recruiting_guidance": _has_keyword(text, ["school recruit", "school recruiting", "school recruitment", "school recruiting guidance"]),
    }

    return {
        "document_type": doc_type,
        "status": "analysis_stub_ready",
        "extractable_sections": extractable,
    }
