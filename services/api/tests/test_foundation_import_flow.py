from fastapi.testclient import TestClient
from services.api.app.main import app


def test_school_program_foundation_import_preview_commit_and_summary():
    client = TestClient(app)

    csv_data = (
        "bde,bn,co,rsid_prefix,population,available\n"
        "BDE1,BN1,CO1,RS1,100,50\n"
        "BDE2,BN2,CO2,RS2,200,100\n"
    )

    # Preview should detect columns and report 2 rows
    resp = client.post(
        "/api/imports/foundation/preview",
        data={'dataset_key': 'school_program_fact'},
        files={'file': ('school.csv', csv_data, 'text/csv')},
    )
    assert resp.status_code == 200
    preview = resp.json()
    assert preview['dataset_key'] == 'school_program_fact'
    assert preview['missing_required'] == []
    assert preview['row_count'] == 2

    # Commit (replace) should insert 2 rows
    resp = client.post(
        "/api/imports/foundation/commit",
        data={'dataset_key': 'school_program_fact', 'mode': 'replace'},
        files={'file': ('school.csv', csv_data, 'text/csv')},
    )
    assert resp.status_code == 200
    commit = resp.json()
    assert 'inserted' in commit and commit['inserted'] == 2

    # Readiness should report loaded true
    resp = client.get('/api/school-program/readiness')
    assert resp.status_code == 200
    ready = resp.json()
    assert ready['status'] == 'ok'
    assert any(d['dataset_key'] == 'school_program_fact' and d['loaded'] for d in ready['datasets'])

    # Summary should aggregate population and available totals
    resp = client.get('/api/school-program/summary')
    assert resp.status_code == 200
    summary = resp.json()
    assert summary['status'] == 'ok'
    assert summary['kpis']['population_total'] == 300
    assert summary['kpis']['available_total'] == 150
