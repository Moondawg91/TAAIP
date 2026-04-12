from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any

from .. import auth

router = APIRouter()


@router.get('/v2/ai-lms/recommendations/{source}/latest')
def get_latest_recommendations(source: str, limit: int = 50, db=Depends(auth.get_db)):
    """Return latest recommendations from a given source (e.g., 'fusion') with explanations and doctrine refs.
    """
    conn = None
    try:
        # tests and runtime use sqlite3 connection helpers; reuse DB connection from SQLAlchemy engine
        from ..db import connect
        conn = connect()
        from ..services.ai_lms import fetch_recommendations_with_annotations
        tbl = f"{source}_recommendations" if not source.endswith('_recommendations') else source
        rows = fetch_recommendations_with_annotations(conn, tbl, limit)
        return {'recommendations': rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@router.post('/v2/ai-lms/decisions')
def post_decision(payload: Dict[str, Any], user=Depends(auth.get_current_user)):
    """Save a user decision/response to a recommendation.

    Expected payload: { recommendation_table: str, recommendation_id: int, action: 'accepted'|'rejected'|'modified'|'ignored', notes?: str }
    """
    required = ('recommendation_table', 'recommendation_id', 'action')
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field {k}")
    try:
        from ..db import connect
        conn = connect()
        from ..services.ai_lms import persist_user_decision
        user_id = getattr(user, 'username', None) or getattr(user, 'sub', None) or None
        did = persist_user_decision(conn, payload['recommendation_table'], int(payload['recommendation_id']), payload['action'], payload.get('notes'), user_id)
        return {'decision_id': did}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/v2/ai-lms/outcomes')
def post_outcome(payload: Dict[str, Any], user=Depends(auth.get_current_user)):
    """Save a simple outcome record linked to a recommendation or decision.

    Expected payload: { recommendation_table: str, recommendation_id: int, decision_id?: int, outcome_type: str, outcome_value: str, observed_at?: str, notes?: str }
    """
    required = ('recommendation_table', 'recommendation_id', 'outcome_type', 'outcome_value')
    for k in required:
        if k not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field {k}")
    try:
        from ..db import connect
        conn = connect()
        from ..services.ai_lms import persist_outcome
        decision_id = payload.get('decision_id')
        oid = persist_outcome(conn, payload['recommendation_table'], int(payload['recommendation_id']), int(decision_id) if decision_id is not None else None, payload['outcome_type'], str(payload['outcome_value']), payload.get('observed_at'), payload.get('notes'))
        return {'outcome_id': oid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/v2/ai-lms/decision-history')
def get_decision_history(unit_rsid: Optional[str] = None, limit: int = 50):
    """Return recent decision history rows with parsed notes and linked outcome."""
    try:
        from ..db import connect
        conn = connect()
        from ..services.ai_lms import fetch_decision_history
        rows = fetch_decision_history(conn, unit_rsid=unit_rsid, limit=limit)
        return {'items': rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/v2/ai-lms/decision-summary')
def get_decision_summary(unit_rsid: Optional[str] = None):
    """Return small aggregated LMS summary for decisions/outcomes."""
    try:
        from ..db import connect
        conn = connect()
        from ..services.ai_lms import compute_decision_summary
        s = compute_decision_summary(conn, unit_rsid=unit_rsid)
        return s
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@router.get('/v2/ai-lms/decisions')
def get_decisions_compat(unit_rsid: Optional[str] = None, limit: int = 50):
    """Compatibility shim: older clients call GET /v2/ai-lms/decisions to list recent decisions.
    Map to the `decision-history` implementation so GET works.
    """
    try:
        from ..db import connect
        conn = connect()
        from ..services.ai_lms import fetch_decision_history
        rows = fetch_decision_history(conn, unit_rsid=unit_rsid, limit=limit)
        return {'items': rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
