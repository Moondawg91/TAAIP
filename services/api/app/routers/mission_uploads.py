"""Placeholder router for mission document upload tracking (stubs only).
No persistence, no file handling. Self-contained.
"""
from typing import Dict, Any
from fastapi import APIRouter, Body
import uuid

router = APIRouter()


@router.get("/mission_uploads/status")
def upload_status() -> Dict[str, Any]:
    return {
        "upload_enabled": False,
        "supported_document_types": ["rop", "school_recruiting_plan"],
        "supported_file_types": [".pdf", ".docx"],
        "status": "upload_placeholder_ready",
    }


@router.post("/mission_uploads/register_upload_stub")
def register_upload_stub(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    doc_type = payload.get("document_type")
    filename = payload.get("filename")
    fy = payload.get("fy")
    unit = payload.get("unit")

    upload_id = f"upload-{uuid.uuid4().hex[:12]}"

    return {
        "upload_id": upload_id,
        "document_type": doc_type,
        "filename": filename,
        "fy": fy,
        "unit": unit,
        "status": "upload_stub_registered",
    }


@router.post("/mission_uploads/validate_stub")
def validate_stub(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    filename = payload.get("filename") or ""
    accepted = [".pdf", ".docx"]
    lower = filename.lower()
    is_valid = any(lower.endswith(ext) for ext in accepted)

    return {
        "document_type": payload.get("document_type"),
        "filename": filename,
        "is_valid_type": bool(is_valid),
        "accepted_types": accepted,
        "status": "validation_stub_ready",
    }
