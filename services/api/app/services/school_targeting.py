"""School Targeting Engine skeleton.

This module provides a scaffold for computing prioritized school targets
that will feed the Targeting Board and inform Mission Allocation supportability.
"""
from typing import Any, Dict, List, Optional
from services.api.app.db import connect
import uuid
from datetime import datetime
import json


def _now_iso():
    return datetime.utcnow().isoformat()


def normalize_inputs(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw signals for use in scoring.

    Keep this minimal for now; refine signals after initial integration.
    """
    return {
        'school_id': raw.get('school_id'),
        'enrollment': float(raw.get('enrollment') or 0),
        'access_score': float(raw.get('access_score') or 0.0),
        'historical_production': float(raw.get('historical_production') or 0),
    }


def score_school(norm: Dict[str, Any]) -> float:
    """Simple weighted score placeholder (0.0 - 1.0).

    We will replace weights with tuned values after gathering signals.
    """
    try:
        e = norm.get('enrollment', 0)
        a = norm.get('access_score', 0.0)
        h = norm.get('historical_production', 0)
        # normalize by some simple transforms
        e_s = min(1.0, e / 2000.0)
        h_s = min(1.0, h / 100.0)
        return max(0.0, min(1.0, 0.5 * a + 0.3 * e_s + 0.2 * h_s))
    except Exception:
        return 0.0


def compute_school_targets(payloads: List[Dict[str, Any]], persist: bool = False) -> List[Dict[str, Any]]:
    """Compute prioritized scores for a list of schools.

    If `persist` is True, persist results into a `school_targeting_scores` table
    (migration for that table will be added next).
    """
    results = []
    for p in payloads:
        norm = normalize_inputs(p)
        score = score_school(norm)
        entry = {
            'school_id': norm.get('school_id'),
            'score': score,
            'components': norm,
        }
        results.append(entry)

    if persist:
        conn = connect(); cur = conn.cursor()
        now = _now_iso()
        for r in results:
            cur.execute('INSERT INTO school_targeting_scores (school_id, score, components_json, created_at) VALUES (?,?,?,?)', (r['school_id'], r['score'], json.dumps(r.get('components')), now))
        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    return results
