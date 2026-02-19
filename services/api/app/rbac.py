"""© 2026 TAAIP. Copyright pending.
RBAC helpers for scope normalization and authorization checks.
"""

from typing import Dict
import os
from sqlalchemy.orm import Query
from . import models
from fastapi import HTTPException


def normalize_scope(scope: str) -> Dict:
    if not scope or scope.upper() == 'USAREC':
        return {'type': 'USAREC', 'value': None}
    s = scope.strip()
    L = len(s)
    if L == 1:
        return {'type': 'BDE', 'value': s}
    if L == 2:
        return {'type': 'BN', 'value': s}
    if L == 3:
        return {'type': 'CO', 'value': s}
    if L >= 4:
        return {'type': 'STN', 'value': s[:4]}
    return {'type': 'USAREC', 'value': None}


def _apply_prefix_filter_on_station_rsid(column, prefix: str):
    # SQLAlchemy column.startswith
    return column.startswith(prefix)


def apply_scope_filter(query: Query, model, scope: str) -> Query:
    norm = normalize_scope(scope)
    if norm['type'] == 'USAREC':
        return query
    prefix = norm['value']

    # If model has rsid attribute (Station)
    if hasattr(model, 'rsid'):
        return query.filter(_apply_prefix_filter_on_station_rsid(model.rsid, prefix))

    # If model has station_rsid attribute (StationZipCoverage)
    if hasattr(model, 'station_rsid'):
        # join Station if not already joined - assume caller has not joined
        Station = models.Station
        return query.join(Station, Station.rsid == model.station_rsid).filter(_apply_prefix_filter_on_station_rsid(Station.rsid, prefix))

    # If model has company_prefix / battalion_prefix / brigade_prefix columns
    if hasattr(model, 'company_prefix') and len(prefix) >= 3:
        return query.filter(model.company_prefix == prefix[:3])
    if hasattr(model, 'battalion_prefix') and len(prefix) >= 2:
        return query.filter(model.battalion_prefix == prefix[:2])
    if hasattr(model, 'brigade_prefix') and len(prefix) >= 1:
        return query.filter(model.brigade_prefix == prefix[:1])

    # default: no-op
    return query


def is_rsid_in_scope(user_scope: str, rsid: str) -> bool:
    norm = normalize_scope(user_scope)
    if norm['type'] == 'USAREC':
        return True
    val = norm['value']
    if norm['type'] == 'BDE':
        return rsid.startswith(val)
    if norm['type'] == 'BN':
        return rsid.startswith(val)
    if norm['type'] == 'CO':
        return rsid.startswith(val)
    if norm['type'] == 'STN':
        return rsid == val
    return False


def _role_is_view_only(role_name: str) -> bool:
    if not role_name:
        return True
    return role_name.endswith('_VIEW') or role_name == 'STATION_VIEW'


def can_create_in_scope(user, scope_type: str, scope_value: str) -> bool:
    """Return True if user may create resources in the requested scope."""
    # sysadmin and usarec always allowed
    if not user:
        return False
    role = getattr(user, 'role', None)
    if role and role.name == 'SYSADMIN':
        return True
    if _role_is_view_only(role.name if role else None):
        return False
    norm = normalize_scope(user.scope)
    if norm['type'] == 'USAREC':
        return True
    # value-based prefix checks
    user_val = norm['value']
    if not user_val:
        return False
    # if user's scope is less granular or equal to requested scope -> allowed when prefix matches
    return scope_value.startswith(user_val)


def authorize_create(user, scope_type: str = None, scope_value: str = None, station_rsid: str = None):
    if os.getenv('DEBUG_RBAC', '0') == '1':
        try:
            role_name = getattr(user, 'role').name if hasattr(user, 'role') else str(getattr(user, 'role', None))
        except Exception:
            role_name = str(getattr(user, 'role', None))
        msg = f"authorize_create called user={getattr(user,'username',None)} role={role_name} scope={getattr(user,'scope',None)} station_rsid={station_rsid} scope_type={scope_type} scope_value={scope_value}\n"
        try:
            with open('/tmp/rbac_debug.log', 'a') as f:
                f.write(msg)
        except Exception:
            # best-effort file log
            pass
    # station_rsid maps to STN
    if station_rsid:
        if not is_rsid_in_scope(user.scope, station_rsid):
            raise HTTPException(status_code=403, detail='station outside user scope')
        # station-level writes: deny view-only roles
        if _role_is_view_only(user.role.name):
            raise HTTPException(status_code=403, detail='role not permitted to create at station level')
        return True
    if scope_type and scope_value:
        if not can_create_in_scope(user, scope_type, scope_value):
            raise HTTPException(status_code=403, detail='requested scope outside user permissions')
        return True
    # no scope provided -> deny
    raise HTTPException(status_code=400, detail='no scope provided for create')
