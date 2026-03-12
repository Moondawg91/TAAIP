import os
import io
import tempfile
import pytest

from fastapi.testclient import TestClient

from importlib import reload
from services.api.app.db import get_db_path, get_documents_path, _ensure_db_dir


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    # Use a temporary DB path and documents path for tests
    db_file = tmp_path / "test_taaip.sqlite3"
    docs_dir = tmp_path / "docs"
    monkeypatch.setenv('TAAIP_DB_PATH', str(db_file))
    monkeypatch.setenv('TAAIP_DOCUMENTS_PATH', str(docs_dir))
    # ensure dirs exist
    _ensure_db_dir(str(db_file))
    if not docs_dir.exists():
        docs_dir.mkdir()
    # ensure schema initialized for the test DB
    try:
        from services.api.app import db as db_mod
        db_mod.init_db()
    except Exception:
        pass
    yield


def test_upload_list_download_roundtrip():
    # import app after env vars have been set by fixture so init_db uses the test DB
    from services.api.app import main as main_mod
    reload(main_mod)
    client = TestClient(main_mod.app)
    # create a small text file
    content = b'Hello TAAIP\nThis is a test file.'
    files = {'file': ('test.txt', io.BytesIO(content), 'text/plain')}
    data = {'title': 'Test upload', 'description': 'desc', 'tags': 'test'}
    resp = client.post('/api/documents/upload', files=files, data=data)
    assert resp.status_code == 200
    body = resp.json()
    assert 'id' in body
    doc_id = body['id']

    # list
    resp2 = client.get('/api/documents')
    assert resp2.status_code == 200
    items = resp2.json()
    assert any(i['id'] == doc_id for i in items)

    # download
    resp3 = client.get(f'/api/documents/{doc_id}/download')
    assert resp3.status_code == 200
    assert resp3.content == content
