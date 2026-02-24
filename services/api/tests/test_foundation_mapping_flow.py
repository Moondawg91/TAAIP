from fastapi.testclient import TestClient
from services.api.app.main import app


def test_foundation_commit_with_messy_headers_applies_mapping_and_summarizes():
    client = TestClient(app)

    # CSV uses non-exact headers: 'Zip Code' instead of 'zip5', 'Population ' with trailing space, 'Avail' for available
    csv_data = (
        "BDE_Name,BN_Code,CO,RS_Prefix,Zip Code,Population ,Avail\n"
        "BDE1,BN1,CO1,RS1,94105,100,50\n"
        "BDE2,BN2,CO2,RS2,94107,200,100\n"
    )

    # Commit without sending explicit mapping: server should fuzzy-match and insert rows
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

    # Summary should aggregate population and available totals
    resp = client.get('/api/school-program/summary')
    assert resp.status_code == 200
    summary = resp.json()
    assert summary['status'] == 'ok'
    assert summary['kpis']['population_total'] == 300
    assert summary['kpis']['available_total'] == 150
