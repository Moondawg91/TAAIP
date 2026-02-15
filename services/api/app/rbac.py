from typing import Dict
from sqlalchemy.orm import Query
from . import models


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
