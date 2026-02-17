import sys
import os
import json
sys.path.insert(0, os.path.abspath('.'))

from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)


def test_boards_and_sessions_flow():
    # create board
    r = client.post('/api/boards/', json={'name': 'Test Board', 'org_unit_id': 1, 'description': 'Tst'})
    assert r.status_code == 200
    b = r.json()
    assert 'id' in b
    board_id = b['id']

    # create session
    r2 = client.post(f'/api/boards/{board_id}/sessions', json={'fy': 2026, 'qtr': 1, 'session_dt': '2026-02-01T00:00:00', 'notes': 'Notes'})
    assert r2.status_code == 200
    s = r2.json()
    assert s.get('board_id') == board_id

    # list sessions
    r3 = client.get(f'/api/boards/{board_id}/sessions')
    assert r3.status_code == 200
    arr = r3.json()
    assert isinstance(arr, list)


def test_tasks_flow():
    # create a compat project
    r = client.post('/api/projects', json={'name': 'Test Project', 'org_unit_id': 1})
    assert r.status_code == 200
    p = r.json()
    project_id = p['id']

    # create a task
    r2 = client.post('/api/tasks/', json={'project_id': project_id, 'title': 'Do thing', 'owner': 'alice'})
    assert r2.status_code == 200
    t = r2.json()
    assert t.get('project_id') == project_id

    # list tasks by project
    r3 = client.get(f'/api/tasks?project_id={project_id}')
    assert r3.status_code == 200
    tasks = r3.json()
    assert isinstance(tasks, list)


def test_task_update_comment_assign_delete():
    r = client.post('/api/projects', json={'name': 'Test Project 2', 'org_unit_id': 1})
    assert r.status_code == 200
    project_id = r.json()['id']
    r2 = client.post('/api/tasks/', json={'project_id': project_id, 'title': 'Task Update', 'owner': 'bob'})
    assert r2.status_code == 200
    task = r2.json()
    tid = task['id']

    # update
    ru = client.patch(f'/api/tasks/{tid}', json={'title': 'Task Updated', 'percent_complete': 50})
    assert ru.status_code == 200
    assert ru.json().get('title') == 'Task Updated'

    # comment
    rc = client.post(f'/api/tasks/{tid}/comments', json={'commenter': 'carol', 'comment': 'Looks good'})
    assert rc.status_code == 200

    # assign
    ra = client.post(f'/api/tasks/{tid}/assign', json={'assignee': 'dave', 'percent_expected': 20})
    assert ra.status_code == 200

    # delete
    rd = client.delete(f'/api/tasks/{tid}')
    assert rd.status_code == 200
