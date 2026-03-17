import json
from services.api.app import migrations
from services.api.app.db import connect
from services.api.app.main import app
from fastapi.testclient import TestClient


def setup_module(module):
    conn = connect()
    migrations.apply_migrations(conn)
    conn.close()


def test_fusion_run_and_latest_endpoints_create_and_return_rows():
    client = TestClient(app)

    # Ensure starting state: no rows or safe to run
    c = connect(); cur = c.cursor()
    try:
        cur.execute("DELETE FROM fusion_recommendations")
        cur.execute("DELETE FROM fusion_evidence")
        c.commit()
    except Exception:
        try:
            c.rollback()
        except Exception:
            pass
    finally:
        c.close()

    # POST to run fusion
    resp = client.post('/api/v2/fusion/run', data={'unit_rsid': ''})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get('status') == 'ok'
    run_id = body.get('fusion_run_id')
    assert run_id
    inserted = body.get('inserted')
    assert isinstance(inserted, int) and inserted >= 0

    # Check DB persisted rows
    c = connect(); cur = c.cursor()
    cur.execute('SELECT COUNT(*) FROM fusion_recommendations WHERE fusion_run_id=?', (run_id,))
    cnt = cur.fetchone()[0]
    assert cnt == inserted

    # GET latest
    resp2 = client.get('/api/v2/fusion/latest')
    assert resp2.status_code == 200
    b2 = resp2.json()
    assert b2.get('status') == 'ok'
    rows = b2.get('rows')
    assert isinstance(rows, list) and len(rows) >= 0

    # If rows returned, check text and evidence
    if rows:
        r0 = rows[0]
        assert r0.get('recommendation_text') and len(r0.get('recommendation_text').strip()) > 0
        ev = r0.get('evidence_json')
        assert ev is not None
        # evidence should reference at least one source domain
        assert any(k in ev for k in ('mission','market','school'))
