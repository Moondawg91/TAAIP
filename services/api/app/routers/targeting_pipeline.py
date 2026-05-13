from fastapi import APIRouter, Body, HTTPException
from typing import Any, Dict, List, Optional
import json
import uuid

from .. import db
from ..db import row_to_dict
from ..services.targeting_operation_linker import create_operation_from_board_decision


router = APIRouter(prefix='/v2/targeting-pipeline', tags=['targeting-pipeline'])

DEFAULT_BOARD_ID = 'targeting-board-q-plus-3'
FUSION_STAGES = {'fusion_issue'}
TWG_STAGES = {'twg_nomination', 'board_ready', 'board_decision', 'follow_on_action'}
BOARD_STAGES = {'board_ready', 'board_decision', 'follow_on_action'}
ACTIVE_FUSION_STATUSES = {'active', 'ready', 'ready_for_twg'}
BOARD_DECISION_REQUIRED_ACTIONS = {'approved', 'modified', 'deferred'}


def _now() -> str:
    return db.now_iso()


def _json_dumps(value: Any) -> str:
    try:
        return json.dumps(value or [])
    except Exception:
        return '[]'


def _json_loads(value: Any) -> Any:
    if value is None:
        return []
    if isinstance(value, (list, dict)):
        return value
    text = str(value).strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except Exception:
        return [part.strip() for part in text.split(',') if part.strip()]


def _coerce_number(value: Any) -> Optional[float]:
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


def _text(value: Any) -> str:
    return str(value or '').strip()


def _normalized(value: Any) -> str:
    return _text(value).lower().replace('-', '_').replace(' ', '_')


def _json_list(value: Any) -> List[str]:
    loaded = _json_loads(value)
    if isinstance(loaded, list):
        return [_text(part) for part in loaded if _text(part)]
    if isinstance(loaded, dict):
        return [_text(part) for part in loaded.values() if _text(part)]
    text = _text(loaded)
    return [text] if text else []


def _merge_record(existing: Optional[Dict[str, Any]], payload: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(existing or {})
    merged.update(payload)
    if 'requested_funding' in merged:
        merged['requested_funding'] = _coerce_number(merged.get('requested_funding'))
    if 'requested_budget' in merged:
        merged['requested_budget'] = _coerce_number(merged.get('requested_budget'))
    if not merged.get('created_by') and merged.get('updated_by'):
        merged['created_by'] = merged.get('updated_by')
    return merged


def _resource_request_present(source: Dict[str, Any]) -> bool:
    return bool(_text(source.get('requested_resources')) or _coerce_number(source.get('requested_funding')) is not None)


def _fusion_actionable_missing(source: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if not _text(source.get('title')):
        missing.append('title / issue name')
    if not _text(source.get('problem_statement')):
        missing.append('problem statement')
    if not _text(source.get('projected_impact')):
        missing.append('why it matters / impact')
    if not _text(source.get('recommended_focus_90_day')):
        missing.append('recommended focus')
    if not _text(source.get('recommended_next_action')):
        missing.append('recommended action / next step')
    if not _text(source.get('impacted_scope')):
        missing.append('owning scope')
    if not _text(source.get('created_by')):
        missing.append('created by')
    return missing


def _fusion_promotion_missing(source: Dict[str, Any]) -> List[str]:
    missing = list(_fusion_actionable_missing(source))
    if _normalized(source.get('status')) not in ACTIVE_FUSION_STATUSES:
        missing.append('status set to active/ready')
    if not (_text(source.get('recommended_next_action')) or _text(source.get('recommended_focus_90_day'))):
        missing.append('recommendation or supportable next step')
    if not _text(source.get('source_context')):
        missing.append('source context')
    return missing


def _twg_trackable_missing(source: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if not _text(source.get('title')):
        missing.append('nomination name')
    if not _text(source.get('nomination_type')):
        missing.append('nomination type')
    if not _text(source.get('origin')):
        missing.append('origin')
    if not _text(source.get('rationale')):
        missing.append('rationale / justification')
    if not _resource_request_present(source):
        missing.append('requested funding/resources')
    if not _text(source.get('submitting_unit')):
        missing.append('requesting unit / company / station')
    if not _text(source.get('owner_lead')):
        missing.append('owner / action lead')
    if not _text(source.get('due_date')):
        missing.append('due / suspense date')
    if not _text(source.get('created_by')) and not _text(source.get('updated_by')):
        missing.append('created by')
    return missing


def _twg_readiness_blockers(source: Dict[str, Any]) -> List[str]:
    return _json_list(source.get('readiness_blockers_json') or source.get('readiness_blockers'))


def _twg_promotion_missing(source: Dict[str, Any]) -> List[str]:
    missing = list(_twg_trackable_missing(source))
    if _normalized(source.get('validation_status')) != 'complete':
        missing.append('validation status complete')
    if not _text(source.get('board_recommendation')):
        missing.append('recommendation to board')
    if _normalized(source.get('status')) not in {'validated', 'ready_for_board', 'board_ready'}:
        missing.append('board-ready status explicitly set')
    if _twg_readiness_blockers(source):
        missing.append('unresolved blocking readiness flags')
    return missing


def _stage_entered_at(source: Dict[str, Any]) -> Optional[str]:
    stage = _normalized(source.get('current_stage'))
    if stage == 'fusion_issue':
        return source.get('created_at')
    if stage == 'twg_nomination':
        return source.get('promoted_to_twg_at') or source.get('created_at')
    if stage == 'board_ready':
        return source.get('promoted_to_board_at') or source.get('updated_at') or source.get('created_at')
    if stage in {'board_decision', 'follow_on_action'}:
        return source.get('decision_recorded_at') or source.get('updated_at') or source.get('created_at')
    return source.get('updated_at') or source.get('created_at')


def _build_readiness(source: Dict[str, Any]) -> Dict[str, Any]:
    stage = _normalized(source.get('current_stage'))
    missing_fields: List[str] = []
    blocking_flags: List[str] = []
    ready = False
    label = 'Discipline state unavailable'
    if stage == 'fusion_issue':
        missing_fields = _fusion_promotion_missing(source)
        ready = not missing_fields
        label = 'Ready for TWG' if ready else 'Not ready for TWG'
    elif stage == 'twg_nomination':
        missing_fields = _twg_promotion_missing(source)
        blocking_flags = _twg_readiness_blockers(source)
        ready = not missing_fields and not blocking_flags
        label = 'Ready for Board' if ready else 'Missing validation or board prep'
    elif stage == 'board_ready':
        ready = True
        label = 'Awaiting commander decision'
    elif stage == 'board_decision':
        ready = True
        label = f"Board decided: {_text(source.get('status')) or _text(source.get('board_decision')) or 'recorded'}"
    elif stage == 'follow_on_action':
        ready = _normalized(source.get('status')) in {'action_complete', 'completed'}
        label = 'Follow-on action complete' if ready else 'Follow-on action open'
    return {
        'ready': ready,
        'label': label,
        'missing_fields': missing_fields,
        'blocking_flags': blocking_flags,
        'stage_entered_at': _stage_entered_at(source),
    }


def _board_decision_missing(record: Dict[str, Any], payload: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    decision = _normalized(payload.get('decision'))
    if not decision or decision == 'pending':
        missing.append('decision status')
    if not _text(payload.get('decided_at')):
        missing.append('decision date')
    if not _text(payload.get('decision_authority')):
        missing.append('decision authority')
    if not _text(payload.get('decided_by')):
        missing.append('decision recorder')
    if decision in {'approved', 'modified'}:
        if _coerce_number(record.get('requested_funding')) is not None and _coerce_number(payload.get('approved_funding')) is None:
            missing.append('approved funding')
        if _text(record.get('requested_resources')) and not _text(payload.get('approved_resources')):
            missing.append('approved resources')
    if decision in BOARD_DECISION_REQUIRED_ACTIONS:
        if not _text(payload.get('follow_on_action_title')):
            missing.append('follow-on action')
        if not _text(payload.get('action_owner')):
            missing.append('assigned follow-on owner')
        if not _text(payload.get('action_due_date')):
            missing.append('follow-on due date')
    return missing


def _require(payload: Dict[str, Any], fields: List[str]) -> None:
    missing = [field for field in fields if not str(payload.get(field) or '').strip()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing)}")


def _record_to_api(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    out['contributing_factors'] = _json_loads(out.get('contributing_factors_json'))
    out['staff_inputs'] = _json_loads(out.get('staff_inputs_json'))
    out['readiness_blockers'] = _json_loads(out.get('readiness_blockers_json'))
    out.pop('contributing_factors_json', None)
    out.pop('staff_inputs_json', None)
    out.pop('readiness_blockers_json', None)
    out['stage_entered_at'] = _stage_entered_at(out)
    out['readiness'] = _build_readiness(out)
    return out


def _get_record(cur, chain_id: str) -> Dict[str, Any]:
    cur.execute('SELECT * FROM targeting_pipeline_records WHERE chain_id=?', (chain_id,))
    row = row_to_dict(cur, cur.fetchone())
    if not row:
        raise HTTPException(status_code=404, detail='targeting record not found')
    return row


def _append_history(
    conn,
    chain_id: str,
    stage: str,
    action: str,
    actor: Optional[str],
    from_status: Optional[str],
    to_status: Optional[str],
    details: Optional[Dict[str, Any]] = None,
) -> None:
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO targeting_pipeline_history(
            chain_id, stage, action, from_status, to_status, actor, details_json, created_at
        ) VALUES (?,?,?,?,?,?,?,?)
        ''',
        (
            chain_id,
            stage,
            action,
            from_status,
            to_status,
            actor,
            json.dumps(details or {}),
            _now(),
        ),
    )


def _create_pipeline_record(conn, payload: Dict[str, Any], current_stage: str, origin: str) -> Dict[str, Any]:
    cur = conn.cursor()
    chain_id = payload.get('chain_id') or f'tgt_{uuid.uuid4().hex[:12]}'
    now = _now()
    status = payload.get('status') or 'active'
    active_flag = 0 if status in {'inactive', 'closed'} else int(payload.get('active_flag', 1))
    columns = [
        'chain_id', 'origin_stage', 'current_stage', 'pipeline_stage', 'record_type', 'title',
        'issue_category', 'problem_statement', 'observed_pattern', 'mission_gap', 'impacted_scope',
        'impacted_entity', 'recommended_focus_90_day', 'contributing_factors_json',
        'staff_inputs_json', 'staff_input_notes', 'recommended_next_action', 'owner_lead',
        'status', 'active_flag', 'inactive_reason', 'source_fusion_id', 'origin', 'nomination_type',
        'requested_quarter', 'submitting_unit', 'briefer_submitter', 'requested_resources',
        'requested_funding', 'requested_budget', 'projected_impact', 'source_context', 'rationale', 'due_date',
        'validation_status', 'board_recommendation', 'readiness_blockers_json', 'board_id', 'board_notes',
        'board_decision', 'decision_authority', 'fund_source', 'budget_category', 'priority', 'created_by', 'updated_by', 'created_at', 'updated_at'
    ]
    values = [
        chain_id,
        payload.get('origin_stage') or current_stage,
        current_stage,
        payload.get('pipeline_stage') or current_stage,
        payload.get('record_type') or payload.get('nomination_type') or 'issue',
        payload.get('title'),
        payload.get('issue_category'),
        payload.get('problem_statement'),
        payload.get('observed_pattern'),
        payload.get('mission_gap'),
        payload.get('impacted_scope'),
        payload.get('impacted_entity'),
        payload.get('recommended_focus_90_day'),
        _json_dumps(payload.get('contributing_factors')),
        _json_dumps(payload.get('staff_inputs')),
        payload.get('staff_input_notes'),
        payload.get('recommended_next_action'),
        payload.get('owner_lead'),
        status,
        active_flag,
        payload.get('inactive_reason'),
        payload.get('source_fusion_id'),
        origin,
        payload.get('nomination_type'),
        payload.get('requested_quarter'),
        payload.get('submitting_unit'),
        payload.get('briefer_submitter'),
        payload.get('requested_resources'),
        _coerce_number(payload.get('requested_funding')),
        _coerce_number(payload.get('requested_budget')),
        payload.get('projected_impact'),
        payload.get('source_context'),
        payload.get('rationale'),
        payload.get('due_date'),
        payload.get('validation_status'),
        payload.get('board_recommendation'),
        _json_dumps(payload.get('readiness_blockers')),
        payload.get('board_id'),
        payload.get('board_notes'),
        payload.get('board_decision'),
        payload.get('decision_authority') or 'Battalion Commander',
        payload.get('fund_source'),
        payload.get('budget_category'),
        payload.get('priority'),
        payload.get('created_by') or 'system',
        payload.get('updated_by') or payload.get('created_by') or 'system',
        now,
        now,
    ]
    placeholders = ','.join(['?'] * len(columns))
    cur.execute(
        f"INSERT INTO targeting_pipeline_records({', '.join(columns)}) VALUES ({placeholders})",
        tuple(values),
    )
    _append_history(conn, chain_id, current_stage, 'create', payload.get('created_by') or 'system', None, status, {'origin': origin})
    conn.commit()
    return _record_to_api(_get_record(cur, chain_id))


def _update_record_fields(conn, chain_id: str, payload: Dict[str, Any], allowed_fields: Dict[str, str]) -> Dict[str, Any]:
    cur = conn.cursor()
    existing = _get_record(cur, chain_id)
    assignments: List[str] = []
    values: List[Any] = []
    for api_field, db_field in allowed_fields.items():
        if api_field not in payload:
            continue
        value = payload[api_field]
        if api_field in {'contributing_factors', 'staff_inputs', 'readiness_blockers'}:
            value = _json_dumps(value)
        if api_field in {'requested_funding', 'requested_budget'}:
            value = _coerce_number(value)
        assignments.append(f'{db_field}=?')
        values.append(value)
    if payload.get('status') == 'inactive' and 'inactive_reason' not in payload:
        assignments.append('inactive_reason=?')
        values.append(existing.get('inactive_reason') or 'Marked inactive')
    if 'status' in payload:
        assignments.append('active_flag=?')
        values.append(0 if payload.get('status') in {'inactive', 'closed'} else 1)
    assignments.extend(['updated_by=?', 'updated_at=?'])
    values.extend([payload.get('updated_by') or 'system', _now()])
    values.append(chain_id)
    if assignments:
        cur.execute(f"UPDATE targeting_pipeline_records SET {', '.join(assignments)} WHERE chain_id=?", tuple(values))
        _append_history(
            conn,
            chain_id,
            payload.get('current_stage') or existing.get('current_stage') or 'fusion_issue',
            payload.get('history_action') or 'update',
            payload.get('updated_by') or 'system',
            existing.get('status'),
            payload.get('status') or existing.get('status'),
            {'fields': list(payload.keys())},
        )
        conn.commit()
    return _record_to_api(_get_record(cur, chain_id))


@router.get('/fusion/issues')
def list_fusion_issues(limit: int = 50, status: Optional[str] = None):
    conn = db.connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM targeting_pipeline_records WHERE current_stage IN (\'fusion_issue\')'
        params: List[Any] = []
        if status:
            sql += ' AND status=?'
            params.append(status)
        sql += ' ORDER BY updated_at DESC LIMIT ?'
        params.append(max(1, min(limit, 200)))
        cur.execute(sql, tuple(params))
        return {'status': 'ok', 'items': [_record_to_api(row_to_dict(cur, row)) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.post('/fusion/issues')
def create_fusion_issue(payload: Dict[str, Any] = Body(...)):
    merged = _merge_record(None, payload)
    missing = _fusion_actionable_missing(merged)
    if _normalized(merged.get('status') or 'active') in ACTIVE_FUSION_STATUSES and missing:
        raise HTTPException(status_code=400, detail=f"Fusion actionable save blocked. Missing required fields: {', '.join(missing)}")
    conn = db.connect()
    try:
        record = _create_pipeline_record(conn, payload, 'fusion_issue', 'fusion')
        return {'status': 'ok', 'item': record}
    finally:
        conn.close()


@router.patch('/fusion/issues/{chain_id}')
def update_fusion_issue(chain_id: str, payload: Dict[str, Any] = Body(...)):
    conn = db.connect()
    try:
        existing = _get_record(conn.cursor(), chain_id)
        merged = _merge_record(existing, payload)
        if _normalized(merged.get('status')) in ACTIVE_FUSION_STATUSES:
            missing = _fusion_actionable_missing(merged)
            if missing:
                raise HTTPException(status_code=400, detail=f"Fusion actionable save blocked. Missing required fields: {', '.join(missing)}")
        item = _update_record_fields(
            conn,
            chain_id,
            payload,
            {
                'title': 'title',
                'issue_category': 'issue_category',
                'problem_statement': 'problem_statement',
                'observed_pattern': 'observed_pattern',
                'mission_gap': 'mission_gap',
                'impacted_scope': 'impacted_scope',
                'impacted_entity': 'impacted_entity',
                'recommended_focus_90_day': 'recommended_focus_90_day',
                'contributing_factors': 'contributing_factors_json',
                'staff_inputs': 'staff_inputs_json',
                'staff_input_notes': 'staff_input_notes',
                'recommended_next_action': 'recommended_next_action',
                'owner_lead': 'owner_lead',
                'status': 'status',
                'inactive_reason': 'inactive_reason',
                'projected_impact': 'projected_impact',
                'source_context': 'source_context',
            },
        )
        return {'status': 'ok', 'item': item}
    finally:
        conn.close()


@router.post('/fusion/issues/{chain_id}/comments')
def add_fusion_issue_comment(chain_id: str, payload: Dict[str, Any] = Body(...)):
    _require(payload, ['comment_text'])
    conn = db.connect()
    try:
        cur = conn.cursor()
        record = _get_record(cur, chain_id)
        cur.execute(
            '''
            INSERT INTO targeting_pipeline_comments(
                chain_id, stage, comment_type, comment_text, author_role, author_name, created_by, created_at
            ) VALUES (?,?,?,?,?,?,?,?)
            ''',
            (
                chain_id,
                record.get('current_stage') or 'fusion_issue',
                payload.get('comment_type') or 'supporting_comment',
                payload.get('comment_text'),
                payload.get('author_role'),
                payload.get('author_name'),
                payload.get('created_by') or payload.get('author_name') or 'system',
                _now(),
            ),
        )
        _append_history(conn, chain_id, record.get('current_stage') or 'fusion_issue', 'comment.added', payload.get('created_by') or 'system', record.get('status'), record.get('status'), {'comment_type': payload.get('comment_type') or 'supporting_comment'})
        conn.commit()
        return {'status': 'ok', 'comment_id': cur.lastrowid}
    finally:
        conn.close()


@router.post('/fusion/issues/{chain_id}/promote')
def promote_fusion_issue(chain_id: str, payload: Dict[str, Any] = Body(...)):
    _require(payload, ['promotion_type', 'requested_quarter', 'updated_by'])
    conn = db.connect()
    try:
        cur = conn.cursor()
        record = _get_record(cur, chain_id)
        if record.get('current_stage') not in FUSION_STAGES:
            raise HTTPException(status_code=400, detail='Only Fusion issues can be promoted to TWG from this endpoint')
        merged = _merge_record(record, payload)
        missing = _fusion_promotion_missing(merged)
        if missing:
            raise HTTPException(status_code=400, detail=f"Fusion to TWG promotion blocked. Missing required fields: {', '.join(missing)}")
        now = _now()
        cur.execute(
            '''
            UPDATE targeting_pipeline_records
            SET current_stage='twg_nomination',
                pipeline_stage=?,
                origin='promoted_from_fusion',
                nomination_type=?,
                requested_quarter=?,
                submitting_unit=?,
                briefer_submitter=?,
                requested_resources=?,
                requested_funding=?,
                projected_impact=?,
                source_context=?,
                status=?,
                updated_by=?,
                updated_at=?,
                promoted_to_twg_at=?
            WHERE chain_id=?
            ''',
            (
                payload.get('pipeline_stage') or 'twg_review',
                payload.get('promotion_type'),
                payload.get('requested_quarter'),
                payload.get('submitting_unit') or record.get('submitting_unit'),
                payload.get('briefer_submitter') or record.get('owner_lead'),
                payload.get('requested_resources'),
                _coerce_number(payload.get('requested_funding')),
                payload.get('projected_impact'),
                payload.get('source_context') or record.get('source_context'),
                payload.get('status') or 'active',
                payload.get('updated_by'),
                now,
                now,
                chain_id,
            ),
        )
        _append_history(conn, chain_id, 'twg_nomination', 'promote.to_twg', payload.get('updated_by'), record.get('status'), payload.get('status') or 'active', {'promotion_type': payload.get('promotion_type')})
        conn.commit()
        return {'status': 'ok', 'item': _record_to_api(_get_record(cur, chain_id))}
    finally:
        conn.close()


@router.get('/twg/items')
def list_twg_items(limit: int = 50, stage: Optional[str] = None):
    conn = db.connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM targeting_pipeline_records WHERE current_stage IN (\'twg_nomination\', \'board_ready\', \'board_decision\', \'follow_on_action\')'
        params: List[Any] = []
        if stage:
            sql += ' AND current_stage=?'
            params.append(stage)
        sql += ' ORDER BY updated_at DESC LIMIT ?'
        params.append(max(1, min(limit, 200)))
        cur.execute(sql, tuple(params))
        return {'status': 'ok', 'items': [_record_to_api(row_to_dict(cur, row)) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.post('/twg/items')
def create_twg_item(payload: Dict[str, Any] = Body(...)):
    normalized_payload = dict(payload)
    normalized_payload['created_by'] = normalized_payload.get('created_by') or normalized_payload.get('updated_by')
    missing = _twg_trackable_missing(_merge_record(None, normalized_payload))
    if _normalized(normalized_payload.get('status') or 'draft') in {'active', 'validated', 'ready_for_board', 'board_ready'} and missing:
        raise HTTPException(status_code=400, detail=f"TWG board-trackable save blocked. Missing required fields: {', '.join(missing)}")
    conn = db.connect()
    try:
        record = _create_pipeline_record(conn, normalized_payload, 'twg_nomination', payload.get('origin') or 'direct_twg_submission')
        return {'status': 'ok', 'item': record}
    finally:
        conn.close()


@router.patch('/twg/items/{chain_id}')
def update_twg_item(chain_id: str, payload: Dict[str, Any] = Body(...)):
    conn = db.connect()
    try:
        existing = _get_record(conn.cursor(), chain_id)
        merged = _merge_record(existing, payload)
        if _normalized(merged.get('status')) in {'active', 'validated', 'ready_for_board', 'board_ready'}:
            missing = _twg_trackable_missing(merged)
            if missing:
                raise HTTPException(status_code=400, detail=f"TWG board-trackable save blocked. Missing required fields: {', '.join(missing)}")
        item = _update_record_fields(
            conn,
            chain_id,
            payload,
            {
                'title': 'title',
                'nomination_type': 'nomination_type',
                'origin': 'origin',
                'requested_quarter': 'requested_quarter',
                'pipeline_stage': 'pipeline_stage',
                'submitting_unit': 'submitting_unit',
                'briefer_submitter': 'briefer_submitter',
                'requested_resources': 'requested_resources',
                'requested_funding': 'requested_funding',
                'requested_budget': 'requested_budget',
                'projected_impact': 'projected_impact',
                'source_context': 'source_context',
                'rationale': 'rationale',
                'due_date': 'due_date',
                'validation_status': 'validation_status',
                'board_recommendation': 'board_recommendation',
                'readiness_blockers': 'readiness_blockers_json',
                'owner_lead': 'owner_lead',
                'status': 'status',
                'staff_input_notes': 'staff_input_notes',
                'fund_source': 'fund_source',
                'budget_category': 'budget_category',
                'priority': 'priority',
            },
        )
        return {'status': 'ok', 'item': item}
    finally:
        conn.close()


@router.post('/twg/items/{chain_id}/promote')
def promote_twg_item_to_board(chain_id: str, payload: Dict[str, Any] = Body(...)):
    _require(payload, ['updated_by'])
    conn = db.connect()
    try:
        cur = conn.cursor()
        record = _get_record(cur, chain_id)
        if record.get('current_stage') not in TWG_STAGES:
            raise HTTPException(status_code=400, detail='Only TWG-stage items can be promoted to the board')
        merged = _merge_record(record, payload)
        missing = _twg_promotion_missing(merged)
        if missing:
            raise HTTPException(status_code=400, detail=f"TWG to Board promotion blocked. Missing required fields: {', '.join(missing)}")
        now = _now()
        board_id = payload.get('board_id') or record.get('board_id') or DEFAULT_BOARD_ID
        cur.execute(
            '''
            UPDATE targeting_pipeline_records
            SET current_stage='board_ready',
                pipeline_stage=?,
                board_id=?,
                board_notes=?,
                status=?,
                updated_by=?,
                updated_at=?,
                promoted_to_board_at=?
            WHERE chain_id=?
            ''',
            (
                payload.get('pipeline_stage') or 'board_ready',
                board_id,
                payload.get('board_notes'),
                payload.get('status') or 'board-ready',
                payload.get('updated_by'),
                now,
                now,
                chain_id,
            ),
        )
        _append_history(conn, chain_id, 'board_ready', 'promote.to_board', payload.get('updated_by'), record.get('status'), payload.get('status') or 'board-ready', {'board_id': board_id})
        conn.commit()
        return {'status': 'ok', 'item': _record_to_api(_get_record(cur, chain_id))}
    finally:
        conn.close()


@router.get('/board/items')
def list_board_items(limit: int = 50):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT * FROM targeting_pipeline_records
            WHERE current_stage IN ('board_ready', 'board_decision', 'follow_on_action')
            ORDER BY COALESCE(promoted_to_board_at, updated_at, created_at) DESC
            LIMIT ?
            ''',
            (max(1, min(limit, 200)),),
        )
        return {'status': 'ok', 'items': [_record_to_api(row_to_dict(cur, row)) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.get('/board/decisions')
def list_board_decisions(limit: int = 100):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM targeting_board_decisions ORDER BY decided_at DESC, created_at DESC LIMIT ?', (max(1, min(limit, 300)),))
        return {'status': 'ok', 'items': [row_to_dict(cur, row) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.post('/board/decisions')
def record_board_decision(payload: Dict[str, Any] = Body(...)):
    _require(payload, ['chain_id', 'decision', 'decided_by'])
    conn = db.connect()
    try:
        cur = conn.cursor()
        db.safe_add_column(conn, 'targeting_board_decisions', 'operation_id', 'TEXT')
        db.safe_add_column(conn, 'targeting_board_decisions', 'operation_created_at', 'TEXT')
        record = _get_record(cur, payload.get('chain_id'))
        if record.get('current_stage') != 'board_ready':
            raise HTTPException(status_code=400, detail='Only board-ready items can receive a board decision')
        missing = _board_decision_missing(record, payload)
        if missing:
            raise HTTPException(status_code=400, detail=f"Board decision submission blocked. Missing required fields: {', '.join(missing)}")
        now = _now()
        decision_id = payload.get('decision_id') or f'dec_{uuid.uuid4().hex[:10]}'
        cur.execute(
            '''
            INSERT INTO targeting_board_decisions(
                decision_id, chain_id, board_id, nomination_title, decision, decision_reason,
                approved_funding, approved_budget, approved_resources, commander_notes, decided_by, decided_at,
                created_by, updated_by, created_at, updated_at, status, operation_id, operation_created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''',
            (
                decision_id,
                payload.get('chain_id'),
                payload.get('board_id') or record.get('board_id') or DEFAULT_BOARD_ID,
                record.get('title'),
                _normalized(payload.get('decision')),
                payload.get('decision_reason'),
                _coerce_number(payload.get('approved_funding')),
                _coerce_number(payload.get('approved_budget')),
                payload.get('approved_resources'),
                payload.get('commander_notes'),
                payload.get('decided_by'),
                payload.get('decided_at') or now,
                payload.get('created_by') or payload.get('decided_by'),
                payload.get('updated_by') or payload.get('decided_by'),
                now,
                now,
                payload.get('status') or 'recorded',
                None,
                None,
            ),
        )

        action_id = None
        next_stage = 'board_decision'
        next_status = _normalized(payload.get('decision'))
        if str(payload.get('follow_on_action_title') or '').strip() or str(payload.get('follow_on_action_details') or '').strip():
            action_id = payload.get('action_id') or f'act_{uuid.uuid4().hex[:10]}'
            cur.execute(
                '''
                INSERT INTO targeting_follow_on_actions(
                    action_id, chain_id, decision_id, board_id, action_title, action_details,
                    owner, owner_role, support_requirements, due_date, status, execution_notes,
                    created_by, updated_by, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''',
                (
                    action_id,
                    payload.get('chain_id'),
                    decision_id,
                    payload.get('board_id') or record.get('board_id') or DEFAULT_BOARD_ID,
                    payload.get('follow_on_action_title') or record.get('title'),
                    payload.get('follow_on_action_details') or payload.get('commander_notes') or payload.get('decision_reason') or '',
                    payload.get('action_owner'),
                    payload.get('action_owner_role'),
                    payload.get('support_requirements'),
                    payload.get('action_due_date'),
                    payload.get('action_status') or 'open',
                    payload.get('execution_notes'),
                    payload.get('created_by') or payload.get('decided_by'),
                    payload.get('updated_by') or payload.get('decided_by'),
                    now,
                    now,
                ),
            )
            next_stage = 'follow_on_action'
            next_status = 'action complete' if _normalized(payload.get('action_status')) in {'completed', 'action_complete'} else 'action open'

        cur.execute(
            '''
            UPDATE targeting_pipeline_records
            SET current_stage=?, pipeline_stage=?, board_id=?, board_notes=?,
                board_decision=?, decision_authority=?, decision_recorded_at=?, status=?,
                updated_by=?, updated_at=?
            WHERE chain_id=?
            ''',
            (
                next_stage,
                'follow_on_action' if next_stage == 'follow_on_action' else 'board_decision',
                payload.get('board_id') or record.get('board_id') or DEFAULT_BOARD_ID,
                payload.get('commander_notes') or payload.get('decision_reason'),
                _normalized(payload.get('decision')),
                payload.get('decision_authority') or 'Battalion Commander',
                payload.get('decided_at') or now,
                next_status,
                payload.get('updated_by') or payload.get('decided_by'),
                now,
                payload.get('chain_id'),
            ),
        )
        _append_history(conn, payload.get('chain_id'), next_stage, 'board.decision.recorded', payload.get('decided_by'), record.get('status'), next_status, {'decision': _normalized(payload.get('decision')), 'action_id': action_id})
        conn.commit()

        operation_linkage = create_operation_from_board_decision(decision_id)
        return {
            'status': 'ok',
            'decision_id': decision_id,
            'action_id': action_id,
            'operation_linkage': operation_linkage,
            'item': _record_to_api(_get_record(cur, payload.get('chain_id'))),
        }
    finally:
        conn.close()


@router.get('/board/actions')
def list_follow_on_actions(limit: int = 100):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM targeting_follow_on_actions ORDER BY updated_at DESC, created_at DESC LIMIT ?', (max(1, min(limit, 300)),))
        return {'status': 'ok', 'items': [row_to_dict(cur, row) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.patch('/board/actions/{action_id}')
def update_follow_on_action(action_id: str, payload: Dict[str, Any] = Body(...)):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM targeting_follow_on_actions WHERE action_id=?', (action_id,))
        action = row_to_dict(cur, cur.fetchone())
        if not action:
            raise HTTPException(status_code=404, detail='follow-on action not found')
        assignments: List[str] = []
        values: List[Any] = []
        field_map = {
            'action_title': 'action_title',
            'action_details': 'action_details',
            'owner': 'owner',
            'owner_role': 'owner_role',
            'support_requirements': 'support_requirements',
            'due_date': 'due_date',
            'status': 'status',
            'execution_notes': 'execution_notes',
        }
        for api_field, db_field in field_map.items():
            if api_field in payload:
                assignments.append(f'{db_field}=?')
                values.append(payload.get(api_field))
        if _normalized(payload.get('status')) in {'completed', 'action_complete'}:
            assignments.append('completed_at=?')
            values.append(payload.get('completed_at') or _now())
        assignments.extend(['updated_by=?', 'updated_at=?'])
        values.extend([payload.get('updated_by') or 'system', _now()])
        values.append(action_id)
        if assignments:
            cur.execute(f"UPDATE targeting_follow_on_actions SET {', '.join(assignments)} WHERE action_id=?", tuple(values))
            pipeline_status = 'action complete' if _normalized(payload.get('status')) in {'completed', 'action_complete'} else 'action open'
            cur.execute(
                'UPDATE targeting_pipeline_records SET current_stage=\'follow_on_action\', status=?, updated_by=?, updated_at=? WHERE chain_id=?',
                (pipeline_status, payload.get('updated_by') or 'system', _now(), action.get('chain_id')),
            )
            _append_history(conn, action.get('chain_id'), 'follow_on_action', 'action.updated', payload.get('updated_by') or 'system', action.get('status'), pipeline_status, {'action_id': action_id})
            conn.commit()
        cur.execute('SELECT * FROM targeting_follow_on_actions WHERE action_id=?', (action_id,))
        return {'status': 'ok', 'item': row_to_dict(cur, cur.fetchone())}
    finally:
        conn.close()


@router.get('/{chain_id}/comments')
def list_comments(chain_id: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM targeting_pipeline_comments WHERE chain_id=? ORDER BY created_at DESC', (chain_id,))
        return {'status': 'ok', 'items': [row_to_dict(cur, row) for row in cur.fetchall()]}
    finally:
        conn.close()


@router.get('/{chain_id}/history')
def list_history(chain_id: str):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM targeting_pipeline_history WHERE chain_id=? ORDER BY created_at DESC, id DESC', (chain_id,))
        rows = []
        for row in cur.fetchall():
            item = row_to_dict(cur, row)
            item['details'] = _json_loads(item.get('details_json'))
            item.pop('details_json', None)
            rows.append(item)
        return {'status': 'ok', 'items': rows}
    finally:
        conn.close()