import os
import hashlib
import uuid
from pathlib import Path
from fastapi import UploadFile


BASE = os.path.join(os.path.dirname(__file__), '.data', 'resources')
os.makedirs(BASE, exist_ok=True)


def _ensure_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


async def save_upload(file: UploadFile) -> dict:
    """Save an UploadFile to local storage with a hashed filename.

    Returns metadata: {'stored_path','sha256','size','stored_name','original_name'}
    """
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    ext = os.path.splitext(file.filename or '')[1] or ''
    stored_name = f"{sha256}_{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(BASE, stored_name)
    _ensure_dir(stored_path)
    with open(stored_path, 'wb') as fh:
        fh.write(content)
    return {
        'stored_path': stored_path,
        'sha256': sha256,
        'size': len(content),
        'stored_name': stored_name,
        'original_name': file.filename,
    }
