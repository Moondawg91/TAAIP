from fastapi import APIRouter, Depends
from typing import Optional
from .rbac import require_scope
from . import tasks as tasks_module

router = APIRouter()


@router.post('/tasks/', summary='Create task (compat)')
def create_task_compat(payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    # Delegate to existing tasks.create_task implementation
    return tasks_module.create_task(payload, allowed_orgs)


@router.get('/tasks', summary='List tasks (compat)')
def list_tasks_compat(project_id: Optional[int] = None, owner: Optional[str] = None, limit: int = 200,
                      allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    return tasks_module.list_tasks(project_id=project_id, owner=owner, limit=limit, allowed_orgs=allowed_orgs)
