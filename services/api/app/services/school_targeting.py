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


def compute_school_targets(payloads: List[Dict[str, Any]], persist: bool = False, unit_rsid: Optional[str] = None, as_of_date: Optional[str] = None, compute_run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Compute prioritized scores for a list of schools.

    If `persist` is True, persist results into `school_targeting_scores` table.
    Additional metadata such as `unit_rsid`, `as_of_date`, and `compute_run_id`
    will be stored for lineage.
    """
    results = []
    for p in payloads:
        norm = normalize_inputs(p)
        score = score_school(norm)
        # derive component-level signals for persistence
        access = norm.get('access_score')
        population = min(1.0, norm.get('enrollment', 0) / 2000.0)
        historical = min(1.0, norm.get('historical_production', 0) / 100.0)
        competition = float(p.get('competition_score') or 0.0)
        risk = float(p.get('risk_penalty') or 0.0)

        entry = {
            'school_id': norm.get('school_id'),
            'priority_score': score,
            'confidence_score': min(1.0, 0.3 + 0.12 * len([k for k in ('enrollment','access_score','historical_production') if p.get(k) is not None])),
            'access_score': access,
            'population_score': population,
            'historical_yield_score': historical,
            'competition_score': competition,
            'risk_penalty': risk,
            'components': norm,
        }
        results.append(entry)

    if persist:
        conn = connect(); cur = conn.cursor()
        # Ensure table exists (defensive: create if migrations not yet applied)
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS school_targeting_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compute_run_id TEXT,
                school_id TEXT,
                unit_rsid TEXT,
                as_of_date TEXT,
                priority_score REAL,
                confidence_score REAL,
                access_score REAL,
                population_score REAL,
                historical_yield_score REAL,
                competition_score REAL,
                risk_penalty REAL,
                components_json TEXT,
                created_at TEXT
            );
            ''')
        except Exception:
            pass
        now = _now_iso()
        run_id = compute_run_id or f"str_{uuid.uuid4().hex}"
        for r in results:
            try:
                cur.execute('''INSERT INTO school_targeting_scores (compute_run_id, school_id, unit_rsid, as_of_date, priority_score, confidence_score, access_score, population_score, historical_yield_score, competition_score, risk_penalty, components_json, created_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                    run_id,
                    r['school_id'],
                    unit_rsid,
                    as_of_date,
                    r.get('priority_score'),
                    r.get('confidence_score'),
                    r.get('access_score'),
                    r.get('population_score'),
                    r.get('historical_yield_score'),
                    r.get('competition_score'),
                    r.get('risk_penalty'),
                    json.dumps(r.get('components')),
                    now
                ))
            except Exception:
                pass
        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    return results
