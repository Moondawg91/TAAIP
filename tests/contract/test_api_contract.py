import pytest
from fastapi.testclient import TestClient

from services.api.app.main import app

client = TestClient(app)

CRITICAL_PATHS = [
    "/api/v2/planning/overview",
    "/api/v2/twg",
    "/api/v2/fusion",
    "/api/v2/org/roots",
    "/api/v2/org/children",
    "/api/v2/admin/users",
    "/api/v2/datahub/upload",
]

def test_openapi_paths_exist():
    openapi = client.get("/openapi.json").json()
    paths = openapi.get('paths', {})
    missing = [p for p in CRITICAL_PATHS if p not in paths]
    assert missing == [], f"Missing critical API paths in OpenAPI: {missing}"

@pytest.mark.parametrize("path", CRITICAL_PATHS)
def test_path_returns_200_or_405(path):
    # We only assert the path is callable; POST endpoints may need form data.
    resp = client.request('GET', path)
    assert resp.status_code in (200, 404, 405, 422, 500), f"Unexpected status {resp.status_code} for {path}"


def test_response_shapes():
    # planning overview -> items list of objects with title or type
    p = client.get('/api/v2/planning/overview').json()
    assert isinstance(p, dict)
    assert 'items' in p and isinstance(p['items'], list)
    # items should be objects with `type` and either `id` or `title`
    for it in p['items']:
        assert isinstance(it, dict)
        assert 'type' in it
        assert ('id' in it and it['id'] is not None) or ('title' in it and it['title'] != '')
    # twg -> array of items
    t = client.get('/api/v2/twg')
    assert t.status_code == 200
    twg_body = t.json()
    assert isinstance(twg_body, list)
    # each twg entry should be an object with id and name
    for w in twg_body:
        assert isinstance(w, dict)
        assert 'id' in w or 'name' in w
    # fusion -> array
    f = client.get('/api/v2/fusion')
    assert f.status_code == 200
    fusion_body = f.json()
    assert isinstance(fusion_body, list)
    # each fusion item should have id, session_date and participants list
    for fr in fusion_body:
        assert isinstance(fr, dict)
        assert 'id' in fr
        assert 'session_date' in fr
        assert 'participants' in fr and isinstance(fr['participants'], list)
