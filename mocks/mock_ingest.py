"""
Mock ingestion script to post sample survey, census, and social signals to the running
TAAIP service for local testing.

Run: python3 mocks/mock_ingest.py
"""
import requests
import os

BASE = os.environ.get('TAAIP_BASE', 'http://localhost:8000')

def post_survey():
    payload = {
        "lead_id": "lead_demo_100",
        "survey_id": "sv_demo_100",
        "responses": {"age": "27", "interest": "engineering"}
    }
    r = requests.post(f"{BASE}/api/v2/ingest/survey", json=payload)
    print('survey', r.status_code, r.text)

def post_census():
    payload = {"geography_code": "99999", "attributes": {"median_income": 60000}}
    r = requests.post(f"{BASE}/api/v2/ingest/census", json=payload)
    print('census', r.status_code, r.text)

def post_social():
    payload = {"external_id": "ig_500", "handle": "@demo", "signals": {"followers": 3000}}
    r = requests.post(f"{BASE}/api/v2/ingest/social", json=payload)
    print('social', r.status_code, r.text)

if __name__ == '__main__':
    post_survey()
    post_census()
    post_social()
