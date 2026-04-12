"""Upload -> Extraction orchestration router.

Accepts upload metadata plus extracted document text and runs the
mission extraction logic (the existing heuristic `extract_stub`) and
returns a combined response containing upload metadata and the
extracted alignment object.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()


class UploadExtractionRequest(BaseModel):
    document_type: str
    filename: str
    stored_path: str
    document_text: str


@router.post("/mission_upload_pipeline/run_extraction")
def run_extraction(payload: UploadExtractionRequest) -> Dict[str, Any]:
    """Run the mission extraction logic against uploaded document text.

    Returns a JSON payload with the original upload metadata and the
    extraction result from the heuristic `extract_stub` endpoint.
    """
    try:
        # import the local extraction helper and model
        from .mission_extraction import ExtractionRequest, extract_stub
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load extraction logic: {e}")

    try:
        req = ExtractionRequest(document_type=payload.document_type, document_text=payload.document_text)
        extraction = extract_stub(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")

    return {
        "upload_metadata": {
            "document_type": payload.document_type,
            "filename": payload.filename,
            "stored_path": payload.stored_path,
        },
        "extraction": extraction,
        "status": "mission_upload_pipeline_ready",
    }
