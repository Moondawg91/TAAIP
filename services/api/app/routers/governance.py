from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
import datetime
import os
import sqlite3
import uuid

from ..db import get_db_path, connect
from .admin_v2 import require_admin_manage


router = APIRouter(prefix='/v2/governance', tags=['governance'])


def _backup_dir() -> str:
    d = os.getenv('TAAIP_GOVERNANCE_BACKUP_DIR', 'services/api/.data/governance_backups')
    os.makedirs(d, exist_ok=True)
    return d


def _audit(actor: str, action: str, meta: Optional[Dict[str, Any]] = None) -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        if not cur.fetchone():
            return
        cur.execute(
            'INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)',
            (actor or 'system', action, 'governance', None, __import__('json').dumps(meta or {}), datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


@router.get('/backups')
def governance_backups(current_user: Dict[str, Any] = Depends(require_admin_manage), limit: int = 50):
    backups = []
    bdir = _backup_dir()
    files = [f for f in os.listdir(bdir) if f.endswith('.sqlite3')]
    for name in sorted(files, reverse=True)[:max(1, min(limit, 500))]:
        path = os.path.join(bdir, name)
        try:
            stat = os.stat(path)
            backup_id = ''
            parts = name.rsplit('_', 1)
            if len(parts) == 2:
                backup_id = parts[1].replace('.sqlite3', '')
            backups.append({
                'backup_id': backup_id,
                'file': name,
                'created_at': datetime.datetime.utcfromtimestamp(stat.st_mtime).isoformat() + 'Z',
                'size_bytes': stat.st_size,
            })
        except Exception:
            continue
    return {'status': 'ok', 'backups': backups}


@router.post('/backup')
def governance_backup(current_user: Dict[str, Any] = Depends(require_admin_manage)):
    db_path = get_db_path()
    if not os.path.isfile(db_path):
        raise HTTPException(status_code=500, detail='database file not found')

    backup_id = uuid.uuid4().hex
    stamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    filename = f'taaip_backup_{stamp}_{backup_id}.sqlite3'
    dst = os.path.join(_backup_dir(), filename)

    try:
        src_conn = sqlite3.connect(db_path)
        dst_conn = sqlite3.connect(dst)
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'backup failed: {e}')

    _audit(
        actor=current_user.get('username', 'admin'),
        action='governance.backup',
        meta={'backup_id': backup_id, 'file': filename},
    )
    return {'status': 'ok', 'backup_id': backup_id, 'file': filename}


@router.post('/restore')
def governance_restore(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(require_admin_manage)):
    backup_id = str(payload.get('backup_id') or '').strip()
    if not backup_id:
        raise HTTPException(status_code=400, detail='backup_id required')

    # Strictly resolve by ID from managed backup directory only.
    bdir = _backup_dir()
    candidates = [f for f in os.listdir(bdir) if backup_id in f and f.endswith('.sqlite3')]
    if not candidates:
        raise HTTPException(status_code=404, detail='backup not found')
    if len(candidates) > 1:
        raise HTTPException(status_code=409, detail='backup_id is ambiguous')
    backup_file = os.path.join(bdir, candidates[0])
    if not os.path.isfile(backup_file):
        raise HTTPException(status_code=404, detail='backup file missing')

    live_db = get_db_path()
    if not os.path.isfile(live_db):
        raise HTTPException(status_code=500, detail='live database file not found')

    try:
        src_conn = sqlite3.connect(backup_file)
        dst_conn = sqlite3.connect(live_db)
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'restore failed: {e}')

    _audit(
        actor=current_user.get('username', 'admin'),
        action='governance.restore',
        meta={'backup_id': backup_id, 'file': os.path.basename(backup_file)},
    )
    return {'status': 'ok', 'restored_backup_id': backup_id}
