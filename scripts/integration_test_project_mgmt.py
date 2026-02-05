#!/usr/bin/env python3
"""Integration test for Project Management endpoints.
Usage: set DROPLET=http://129.212.185.3 and run.
"""
import os
import sys
import requests
import time

BASE = os.environ.get('DROPLET', 'http://127.0.0.1:8000')

def run():
    print('Running Project Management integration test against', BASE)
    s = requests.Session()
    # migrations
    r = s.post(f'{BASE}/api/v2/projects_pm/init_migrations')
    print('migrations:', r.status_code, r.text)
    # create project
    payload = {
        'name': 'Integration Test Project',
        'description': 'Created by integration_test_project_mgmt',
        'total_budget': 10000,
        'estimated_benefit': 20000,
        'metadata': {'benefit_per_participant': 25}
    }
    r = s.post(f'{BASE}/api/v2/projects_pm/projects', json=payload)
    print('create project:', r.status_code, r.text)
    if r.status_code != 200:
        print('FAILED to create project')
        sys.exit(2)
    pid = r.json().get('project_id')
    # add participant
    # send both query param and JSON body for compatibility with different router versions
    params = {'person_id': 'p1'}
    r = s.post(f'{BASE}/api/v2/projects_pm/projects/{pid}/participants', params=params, json={'person_id':'p1','role':'recruiter','unit':'1-101','attendance':1})
    print('add participant:', r.status_code, r.text)
    # add budget transaction
    r = s.post(f'{BASE}/api/v2/projects_pm/projects/{pid}/budget/transaction', params={'type':'event','description':'integration','amount':500,'category':'events'})
    print('add txn:', r.status_code, r.text)
    # fetch project detail
    r = s.get(f'{BASE}/api/v2/projects_pm/projects/{pid}')
    print('project detail:', r.status_code, r.text)
    proj = r.json().get('project',{})
    # add emm mapping
    r = s.post(f'{BASE}/api/v2/projects_pm/projects/{pid}/emm/import', json={'emm_event_id':'emm_123','payload':{'foo':'bar'}})
    print('emm import:', r.status_code, r.text)
    if r.status_code == 404:
        # try alternate path used by some deployments
        r = s.post(f'{BASE}/api/v2/projects/{pid}/emm/import', json={'emm_event_id':'emm_123','payload':{'foo':'bar'}})
        print('emm import (alternate):', r.status_code, r.text)
    # list emm
    r = s.get(f'{BASE}/api/v2/projects_pm/projects/{pid}/emm')
    print('emm list:', r.status_code, r.text)
    if r.status_code == 404:
        r = s.get(f'{BASE}/api/v2/projects/{pid}/emm')
        print('emm list (alternate):', r.status_code, r.text)
    print('Integration test complete')

if __name__ == '__main__':
    run()
