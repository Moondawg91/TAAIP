"""Production-ready mission document upload endpoint.

Accepts multipart file uploads for ROP and School Recruiting Plan documents,
validates file type and size, and stores files on local filesystem.

No database persistence is performed here; the endpoint returns metadata
about the stored file for downstream processing.
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional, Dict, Any
import os
from uuid import uuid4

router = APIRouter()

ALLOWED_DOC_TYPES = {"rop", "school_recruiting_plan"}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
STORAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "mission_documents"))


def _ensure_storage_dir():
    os.makedirs(STORAGE_ROOT, exist_ok=True)


def _safe_filename(name: str) -> str:
    return os.path.basename(name)


@router.post("/mission_uploads/real_upload")
async def real_upload(
    document_type: str = Form(...),
    unit: str = Form(...),
    fy: str = Form(...),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    # Validate document_type
    if not document_type or document_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=400, detail={"code": "invalid_document_type", "message": "Unsupported document_type"})

    # Validate filename and extension
    orig_name = _safe_filename(file.filename or "")
    if not orig_name:
        raise HTTPException(status_code=400, detail={"code": "missing_filename", "message": "No filename provided"})
    _, ext = os.path.splitext(orig_name)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail={"code": "invalid_file_type", "message": f"Unsupported file extension: {ext}"})

    # Ensure storage dir exists
    try:
        _ensure_storage_dir()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "storage_unavailable", "message": str(e)})

    upload_id = uuid4().hex
    stored_name = f"{upload_id}_{orig_name}"
    stored_path = os.path.join(STORAGE_ROOT, stored_name)

    # Stream file to disk while enforcing size limit
    total = 0
    try:
        with open(stored_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 64)
                if not chunk:
                    break
                out.write(chunk)
                total += len(chunk)
                if total > MAX_SIZE_BYTES:
                    out.close()
                    try:
                        os.remove(stored_path)
                    except Exception:
                        pass
                    raise HTTPException(status_code=413, detail={"code": "file_too_large", "message": "File exceeds maximum allowed size"})
    except HTTPException:
        raise
    except Exception as e:
        # cleanup and report
        try:
            if os.path.exists(stored_path):
                os.remove(stored_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail={"code": "storage_write_failed", "message": str(e)})

    if total == 0:
        try:
            os.remove(stored_path)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail={"code": "empty_file", "message": "Uploaded file is empty"})

    return {
        "upload_id": upload_id,
        "document_type": document_type,
        "filename": orig_name,
        "stored_path": stored_path,
        "unit": unit,
        "fy": fy,
        "size_bytes": total,
        "status": "uploaded",
    }
