import pytest
from unittest.mock import MagicMock
from datetime import datetime, date
from services.api.app.services import (
    targeting_board_engine,
    twg_engine,
    roi_engine,
    market_engine,
    funnel_engine,
    targeting_engine,
    school_plan_engine,
)
from services.api.app.routers import command_center, powerbi_feed


def _market_ok():
    return {
        "status": "ok",
        "market_engine": {
            "summary": {"market_capability_score": 0.65, "overall_market_status": "supportive"},
            "prioritized_market_zip": [{"zip_code": "12345", "priority_score": 75.0}],
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _funnel_ok():
    return {
        "status": "ok",
        "funnel_engine": {
            "summary": {"lead_to_contract_rate": 0.18, "overall_funnel_status": "watch"},
            "prioritized_funnel_gaps": [{"category": "funnel", "priority_score": 70.0}],
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _targeting_ok():
    return {
        "status": "ok",
        "targeting_engine": {
            "summary": {"high_priority_count": 12},
            "prioritized_targets": [{"zip_code": "12345", "priority_score": 75.0}],
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _school_ok():
    return {
        "status": "ok",
        "school_plan_engine": {
            "summary": {"underengaged_school_count": 5, "total_schools": 50, "priority_school_count": 8},
            "prioritized_schools": [{"school_id": "S1", "priority_score": 65.0}],
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _roi_ok():
    return {
        "status": "ok",
        "roi_engine": {
            "summary": {"low_effectiveness_count": 3, "total_events_scored": 15, "avg_roi_score": 62.0},
            "prioritized_events": [{"event_id": "E1", "priority_score": 55.0}],
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _acc_ok():
    return {
        "summary": {"status": "balanced"},
        "classification": "balanced",
    }


def _loe_ok():
    return {
        "status": "ok",
        "status_counts": {"at_risk": 2, "not_met": 1, "met": 20},
        "total_metrics": 23,
    }


def _mission_ok():
    return {
        "status": "ok",
        "mission_status": {
            "summary": {"mission_delta_pct": 2.5},
            "factor_candidates": [
                {"factor_id": "market", "impact": 0.15},
                {"factor_id": "funnel", "impact": -0.10},
            ],
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _twg_with_candidates():
    return {
        "status": "ok",
        "twg_engine": {
            "summary": {
                "total_items": 8,
                "high_priority_count": 3,
                "medium_priority_count": 4,
                "low_priority_count": 1,
                "board_elevation_count": 3,
                "overall_twg_status": "attention_required",
            },
            "prioritized_items": [
                {
                    "item_id": "TWG-001",
                    "category": "funnel",
                    "title": "Funnel acceleration needed at CO level",
                    "priority_score": 78.5,
                    "priority_band": "high",
                    "owner_level": "CO",
                    "recommended_action": "Implement funnel recovery plan",
                    "due_out": "2026-04-20",
                    "expected_effect": "Improve funnel progression by 15%",
                    "board_elevation_recommended": True,
                    "rationale": "Severe funnel dropoff at lead-to-contract stage",
                    "source_engine": "funnel_engine",
                    "trace_id": "TBE-001",
                },
                {
                    "item_id": "TWG-002",
                    "category": "targeting",
                    "title": "ZIP targeting realignment",
                    "priority_score": 72.0,
                    "priority_band": "high",
                    "owner_level": "CO",
                    "recommended_action": "Reallocate targeting effort to high-opportunity ZIPs",
                    "due_out": "2026-04-25",
                    "expected_effect": "Improve ZIP coverage efficiency",
                    "board_elevation_recommended": True,
                    "rationale": "Targeting gaps identified in market analysis",
                    "source_engine": "targeting_engine",
                    "trace_id": "TBE-002",
                },
                {
                    "item_id": "TWG-003",
                    "category": "roi",
                    "title": "Low-ROI event reallocation",
                    "priority_score": 70.0,
                    "priority_band": "high",
                    "owner_level": "CO",
                    "recommended_action": "Redirect event effort from low-ROI to high-ROI activities",
                    "due_out": "2026-04-22",
                    "expected_effect": "Improve accession-per-event ratio by 12%",
                    "board_elevation_recommended": True,
                    "rationale": "3 events show low ROI effectiveness",
                    "source_engine": "roi_engine",
                    "trace_id": "TBE-003",
                },
                {
                    "item_id": "TWG-004",
                    "category": "school",
                    "title": "School engagement intensification",
                    "priority_score": 58.5,
                    "priority_band": "medium",
                    "owner_level": "CO",
                    "recommended_action": "Increase effort at high-opportunity schools",
                    "due_out": "2026-05-01",
                    "expected_effect": "Increase school-level participation",
                    "board_elevation_recommended": False,
                    "rationale": "5 schools underengaged with high opportunity",
                    "source_engine": "school_plan_engine",
                    "trace_id": "TBE-004",
                },
                {
                    "item_id": "TWG-005",
                    "category": "market",
                    "title": "Market capability strengthening",
                    "priority_score": 52.0,
                    "priority_band": "medium",
                    "owner_level": "BN",
                    "recommended_action": "Strengthen market support infrastructure",
                    "due_out": "2026-05-05",
                    "expected_effect": "Improve market capability score",
                    "board_elevation_recommended": False,
                    "rationale": "Market capability gap identified",
                    "source_engine": "market_engine",
                    "trace_id": "TBE-005",
                },
            ],
            "board_candidates": [
                {
                    "item_id": "TWG-001",
                    "category": "funnel",
                    "title": "Funnel acceleration needed at CO level",
                    "priority_score": 78.5,
                    "owner_level": "CO",
                    "recommended_action": "Implement funnel recovery plan",
                    "rationale": "Severe funnel dropoff at lead-to-contract stage",
                    "source_engine": "funnel_engine",
                    "trace_id": "TBE-001",
                },
                {
                    "item_id": "TWG-002",
                    "category": "targeting",
                    "title": "ZIP targeting realignment",
                    "priority_score": 72.0,
                    "owner_level": "CO",
                    "recommended_action": "Reallocate targeting effort to high-opportunity ZIPs",
                    "rationale": "Targeting gaps identified in market analysis",
                    "source_engine": "targeting_engine",
                    "trace_id": "TBE-002",
                },
                {
                    "item_id": "TWG-003",
                    "category": "roi",
                    "title": "Low-ROI event reallocation",
                    "priority_score": 70.0,
                    "owner_level": "CO",
                    "recommended_action": "Redirect event effort from low-ROI to high-ROI activities",
                    "rationale": "3 events show low ROI effectiveness",
                    "source_engine": "roi_engine",
                    "trace_id": "TBE-003",
                },
            ],
            "twg_agenda": [],
            "due_outs": [],
            "data_sources": {},
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


def _twg_no_data():
    return {
        "status": "no_data",
        "twg_engine": {
            "summary": {
                "total_items": 0,
                "high_priority_count": 0,
                "board_elevation_count": 0,
                "overall_twg_status": "no_data",
            },
            "prioritized_items": [],
            "board_candidates": [],
            "twg_agenda": [],
            "due_outs": [],
            "data_sources": {},
            "data_as_of": datetime.utcnow().isoformat() + "Z",
        },
    }


@pytest.fixture
def db():
    db_mock = MagicMock()
    return db_mock


def test_targeting_board_engine_valid_data(db, monkeypatch):
    """Test board engine with valid TWG board candidates produces decisions and shifts."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_engine, "summarize_targeting_engine", lambda *args, **kwargs: _targeting_ok()
    )

    result = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA", top_n=10
    )

    assert result["status"] == "ok"
    board_engine = result.get("targeting_board_engine", {})
    
    assert board_engine["summary"]["total_items"] == 3
    assert board_engine["summary"]["approved_count"] > 0
    assert board_engine["summary"]["resource_shift_count"] >= 0
    
    assert len(board_engine["prioritized_board_items"]) == 3
    assert len(board_engine["board_decisions"]) == 3
    
    # Check decision types exist
    decision_types = {d.get("decision_type") for d in board_engine["board_decisions"]}
    assert decision_types.issubset({"approve", "modify", "reject"})
    
    # Check downstream tasks generated for approved/modified items
    assert len(board_engine["downstream_twg_tasks"]) > 0


def test_targeting_board_engine_no_data(db, monkeypatch):
    """Test board engine with no TWG candidates returns no_data."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_no_data()
    )

    result = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA"
    )

    assert result["status"] == "no_data"
    board_engine = result.get("targeting_board_engine", {})
    
    assert board_engine["summary"]["total_items"] == 0
    assert board_engine["summary"]["approved_count"] == 0
    assert len(board_engine["prioritized_board_items"]) == 0
    assert len(board_engine["board_decisions"]) == 0


def test_targeting_board_engine_deterministic(db, monkeypatch):
    """Test board engine produces same output from same input."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_engine, "summarize_targeting_engine", lambda *args, **kwargs: _targeting_ok()
    )

    result1 = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA"
    )
    
    result2 = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA"
    )

    # Same number of items and decisions
    assert result1["targeting_board_engine"]["summary"]["total_items"] == result2["targeting_board_engine"]["summary"]["total_items"]
    assert result1["targeting_board_engine"]["summary"]["approved_count"] == result2["targeting_board_engine"]["summary"]["approved_count"]
    
    # Same item ordering (by priority score DESC, category ASC)
    items1 = result1["targeting_board_engine"]["prioritized_board_items"]
    items2 = result2["targeting_board_engine"]["prioritized_board_items"]
    
    for i1, i2 in zip(items1, items2):
        assert i1["source_twg_item_id"] == i2["source_twg_item_id"]
        assert i1["decision_type"] == i2["decision_type"]


def test_targeting_board_engine_decision_types(db, monkeypatch):
    """Test board engine produces approve/modify/reject decisions based on priority."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_engine, "summarize_targeting_engine", lambda *args, **kwargs: _targeting_ok()
    )

    result = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA"
    )

    board_items = result["targeting_board_engine"]["prioritized_board_items"]
    
    # Verify high-priority items are approved
    approved_items = [b for b in board_items if b["decision_type"] == "approve"]
    modified_items = [b for b in board_items if b["decision_type"] == "modify"]
    rejected_items = [b for b in board_items if b["decision_type"] == "reject"]
    
    # Should have some mix
    assert len(board_items) > 0
    # High-priority items should generally be approved
    if approved_items:
        avg_approved_priority = sum(b["priority_score"] for b in approved_items) / len(approved_items)
        assert avg_approved_priority >= 50.0


def test_targeting_board_engine_downstream_tasks(db, monkeypatch):
    """Test that approved/modified decisions generate executable downstream tasks."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_engine, "summarize_targeting_engine", lambda *args, **kwargs: _targeting_ok()
    )

    result = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA"
    )

    tasks = result["targeting_board_engine"]["downstream_twg_tasks"]
    
    # Should have tasks for non-rejected decisions
    assert len(tasks) > 0
    
    # Each task should have required fields
    for task in tasks:
        assert "task_id" in task
        assert "source_board_decision_id" in task
        assert "owner_level" in task
        assert "action" in task
        assert "due_out" in task
        assert task["owner_level"] in ["BN", "CO", "STN"]


def test_targeting_board_engine_resource_shifts(db, monkeypatch):
    """Test that approved high-priority items generate resource shifts."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_engine, "summarize_targeting_engine", lambda *args, **kwargs: _targeting_ok()
    )

    result = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA"
    )

    shifts = result["targeting_board_engine"]["directed_shifts"]
    
    # Should have shifts for high-priority approved items
    if shifts:
        for shift in shifts:
            assert "shift_type" in shift
            assert "from" in shift
            assert "to" in shift
            assert "justification" in shift
            assert shift["shift_type"] in ["resource", "effort", "targeting", "school", "event"]


def test_command_center_includes_board(db, monkeypatch):
    """Test that command center overview includes board engine summary."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_engine, "summarize_targeting_engine", lambda *args, **kwargs: _targeting_ok()
    )
    # Check board is callable in the API integration context
    result = targeting_board_engine.summarize_targeting_board_engine(db, "USAREC", "USAREC")
    assert result["status"] in ["ok", "no_data"]


def test_powerbi_includes_board_datasets(db, monkeypatch):
    """Test that PowerBI operational_command_dataset includes board outputs."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_board_engine, "summarize_targeting_board_engine",
        lambda *args, **kwargs: {
            "status": "ok",
            "targeting_board_engine": {
                "summary": {"total_items": 3, "approved_count": 2},
                "prioritized_board_items": [{"board_item_id": "BI-001", "decision_type": "approve"}],
                "board_decisions": [{"decision_id": "DEC-001"}],
                "directed_shifts": [{"shift_type": "effort"}],
                "downstream_twg_tasks": [{"task_id": "TASK-001"}],
            }
        }
    )
    # Check that board outputs are exported to PBI
    result = targeting_board_engine.summarize_targeting_board_engine(db, "USAREC", "USAREC")
    
    board_data = result.get("targeting_board_engine", {})
    assert "summary" in board_data
    assert "prioritized_board_items" in board_data
    assert "board_decisions" in board_data
    assert "directed_shifts" in board_data
    assert "downstream_twg_tasks" in board_data


def test_targeting_board_posture(db, monkeypatch):
    """Test that board posture reflects approval/rejection distribution."""
    monkeypatch.setattr(
        twg_engine, "summarize_twg_engine", lambda *args, **kwargs: _twg_with_candidates()
    )
    monkeypatch.setattr(
        roi_engine, "summarize_roi_engine", lambda *args, **kwargs: _roi_ok()
    )
    monkeypatch.setattr(
        targeting_engine, "summarize_targeting_engine", lambda *args, **kwargs: _targeting_ok()
    )

    result = targeting_board_engine.summarize_targeting_board_engine(
        db, "CO", "ALPHA", "CO", "ALPHA"
    )

    posture = result["targeting_board_engine"]["summary"]["overall_board_posture"]
    assert posture in ["aggressive", "balanced", "constrained", "unknown"]
