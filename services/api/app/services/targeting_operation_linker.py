from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Dict, Optional

from .. import db


def _text(value: Any) -> str:
    return str(value or '').strip()


def _normalized(value: Any) -> str:
    return _text(value).lower().replace('-', '_').replace(' ', '_')


def _to_number(value: Any) -> Optional[float]:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except Exception:
        try:
            cleaned = str(value).replace('$', '').replace(',', '').strip()
            return float(cleaned)
        except Exception:
            return None


def _to_int(value: Any) -> Optional[int]:
    n = _to_number(value)
    if n is None:
        return None
    return int(round(n))


def _ensure_operation_linkage_columns(conn: sqlite3.Connection) -> None:
    db.safe_add_column(conn, 'targeting_board_decisions', 'operation_id', 'TEXT')
    db.safe_add_column(conn, 'targeting_board_decisions', 'operation_created_at', 'TEXT')

    db.safe_add_column(conn, 'operations_records', 'source_nomination_id', 'TEXT')
    db.safe_add_column(conn, 'operations_records', 'source_board_decision_id', 'TEXT')
    db.safe_add_column(conn, 'operations_records', 'origin_title', 'TEXT')
    db.safe_add_column(conn, 'operations_records', 'origin_type', 'TEXT')
    db.safe_add_column(conn, 'operations_records', 'approved_budget', 'REAL')
    db.safe_add_column(conn, 'operations_records', 'fund_source', 'TEXT')
    db.safe_add_column(conn, 'operations_records', 'expected_leads', 'INTEGER')
    db.safe_add_column(conn, 'operations_records', 'expected_engagements', 'INTEGER')
    db.safe_add_column(conn, 'operations_records', 'expected_contracts', 'INTEGER')


def _map_operation_type(nomination_type: str) -> str:
    key = _normalized(nomination_type)
    mapping = {
        'event': 'Event Operation',
        'engagement_campaign': 'Engagement Campaign',
        'campaign': 'Engagement Campaign',
        'school_engagement': 'School Engagement',
        'territory_recovery': 'Territory Recovery',
        'special_population': 'Special Population',
        'market_expansion': 'Market Expansion',
        'resource_shift': 'Resource Reallocation',
    }
    return mapping.get(key, nomination_type or 'Targeting-Driven Operation')


def create_operation_from_board_decision(decision_id: str) -> Dict[str, Any]:
    conn = db.connect()
    try:
        cur = conn.cursor()
        _ensure_operation_linkage_columns(conn)

        cur.execute('SELECT * FROM targeting_board_decisions WHERE decision_id=?', (decision_id,))
        decision = db.row_to_dict(cur, cur.fetchone())
        if not decision:
            return {'status': 'not_found', 'reason': 'decision_not_found', 'decision_id': decision_id}

        decision_state = _normalized(decision.get('decision'))
        if decision_state not in {'approved', 'modified'}:
            return {
                'status': 'skipped',
                'reason': 'decision_not_actionable',
                'decision_id': decision_id,
                'decision': decision_state,
            }

        chain_id = _text(decision.get('chain_id'))
        cur.execute('SELECT * FROM targeting_pipeline_records WHERE chain_id=?', (chain_id,))
        nomination = db.row_to_dict(cur, cur.fetchone())
        if not nomination:
            return {
                'status': 'skipped',
                'reason': 'nomination_not_found',
                'decision_id': decision_id,
                'chain_id': chain_id,
            }

        existing: Optional[Dict[str, Any]] = None
        cur.execute('SELECT * FROM operations_records WHERE source_board_decision_id=? LIMIT 1', (decision_id,))
        existing = db.row_to_dict(cur, cur.fetchone())
        if not existing and chain_id:
            cur.execute('SELECT * FROM operations_records WHERE source_nomination_id=? LIMIT 1', (chain_id,))
            existing = db.row_to_dict(cur, cur.fetchone())

        op_id = _text((existing or {}).get('op_id')) or f'op_{uuid.uuid4().hex[:10]}'
        now = db.now_iso()

        nomination_title = _text(nomination.get('title')) or f'Nomination {chain_id}'
        nomination_type = _text(nomination.get('nomination_type'))
        objective = (
            _text(nomination.get('recommended_next_action'))
            or _text(nomination.get('recommended_focus_90_day'))
            or _text(nomination.get('problem_statement'))
            or nomination_title
        )

        approved_budget = _to_number(decision.get('approved_budget'))
        expected_leads = _to_int(nomination.get('expected_leads'))
        expected_engagements = _to_int(nomination.get('expected_engagements'))
        expected_contracts = _to_int(nomination.get('expected_contracts'))

        mapped: Dict[str, Any] = {
            'op_id': op_id,
            'operation_name': nomination_title,
            'operation_type': _map_operation_type(nomination_type),
            'objective': objective,
            'company': _text(nomination.get('submitting_unit')),
            'rsid': _text(nomination.get('impacted_scope')),
            'status': 'Planned',
            'mission_alignment': _text(nomination.get('priority')) or 'Aligned',
            'execution_gap': '',
            'progress_pct': 0,
            'budget_used': 0,
            'approved_budget': approved_budget,
            'fund_source': _text(nomination.get('fund_source')),
            'expected_leads': expected_leads,
            'expected_engagements': expected_engagements,
            'expected_contracts': expected_contracts,
            'source_nomination_id': chain_id,
            'source_board_decision_id': decision_id,
            'origin_title': nomination_title,
            'origin_type': 'Targeting Board',
            'updated_at': now,
        }

        if existing:
            assignments = []
            values = []
            for key, value in mapped.items():
                if key == 'op_id':
                    continue
                assignments.append(f'{key}=?')
                values.append(value)
            values.append(op_id)
            cur.execute(f"UPDATE operations_records SET {', '.join(assignments)} WHERE op_id=?", tuple(values))
            result = 'updated'
        else:
            mapped['created_at'] = now
            columns = ', '.join(mapped.keys())
            placeholders = ', '.join(['?'] * len(mapped))
            cur.execute(f'INSERT INTO operations_records ({columns}) VALUES ({placeholders})', tuple(mapped.values()))
            result = 'created'

        cur.execute(
            '''
            UPDATE targeting_board_decisions
            SET operation_id=?, operation_created_at=?, updated_at=?
            WHERE decision_id=?
            ''',
            (op_id, now, now, decision_id),
        )

        conn.commit()
        return {
            'status': 'ok',
            'result': result,
            'operation_id': op_id,
            'decision_id': decision_id,
            'chain_id': chain_id,
        }
    finally:
        conn.close()
