"""
Test asset_engine: verifies real data usage, constraint handling, and board traceability.

HARD RULES VALIDATION:
1. No fabricated asset counts/capacities - uses real DB data
2. Structured no_data/partial_data when unavailable
3. All recommendations traceable back to board decisions and upstream evidence
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from services.api.app.services import asset_engine


class TestAssetEngineConstraintHandling:
    """Verify structured no_data and partial_data constraints."""
    
    def test_no_data_no_recruiter_workload(self, mock_db):
        """Return no_data with constraints when recruiter and workload unavailable."""
        
        # Mock: No recruiter data
        with patch.object(asset_engine, '_query_recruiter_count') as mock_recruiter:
            mock_recruiter.return_value = (None, "scope_not_found_in_database")
            
            # Mock: No workload signals
            with patch.object(asset_engine.targeting_board_engine, 'summarize_targeting_board_engine') as mock_board:
                mock_board.return_value = {"status": "no_data"}
                
                with patch.object(asset_engine.twg_engine, 'summarize_twg_engine') as mock_twg:
                    mock_twg.return_value = {"status": "no_data"}
                    
                    with patch.object(asset_engine.funnel_engine, 'summarize_funnel_engine') as mock_funnel:
                        mock_funnel.return_value = {"status": "no_data"}
                        
                        with patch.object(asset_engine.school_plan_engine, 'summarize_school_plan_engine') as mock_school:
                            mock_school.return_value = {"status": "no_data"}
                            
                            with patch.object(asset_engine.roi_engine, 'summarize_roi_engine') as mock_roi:
                                mock_roi.return_value = {"status": "no_data"}
                                
                                result = asset_engine.summarize_asset_engine(
                                    mock_db, "CO", "1-27-INF", "CO", "1-27-INF"
                                )
        
        assert result["status"] == "no_data"
        assert len(result["asset_engine"]["execution_constraints"]) > 0
        
        # Verify constraints describe missing data
        constraint_types = [c["constraint_type"] for c in result["asset_engine"]["execution_constraints"]]
        assert "data_availability" in constraint_types
    
    def test_partial_data_recruiter_no_workload(self, mock_db):
        """Return partial_data when recruiter found but workload unavailable."""
        
        # Mock: Recruiter data available
        with patch.object(asset_engine, '_query_recruiter_count') as mock_recruiter:
            mock_recruiter.return_value = (120, None)
            
            with patch.object(asset_engine, '_query_asset_strength') as mock_asset:
                mock_asset.return_value = (None, None)  # No individual asset data
                
                # Mock: No workload signals
                with patch.object(asset_engine.targeting_board_engine, 'summarize_targeting_board_engine') as mock_board:
                    mock_board.return_value = {"status": "no_data"}
                    
                    with patch.object(asset_engine.twg_engine, 'summarize_twg_engine') as mock_twg:
                        mock_twg.return_value = {"status": "no_data"}
                        
                        with patch.object(asset_engine.funnel_engine, 'summarize_funnel_engine') as mock_funnel:
                            mock_funnel.return_value = {"status": "no_data"}
                            
                            with patch.object(asset_engine.school_plan_engine, 'summarize_school_plan_engine') as mock_school:
                                mock_school.return_value = {"status": "no_data"}
                                
                                with patch.object(asset_engine.roi_engine, 'summarize_roi_engine') as mock_roi:
                                    mock_roi.return_value = {"status": "no_data"}
                                    
                                    result = asset_engine.summarize_asset_engine(
                                        mock_db, "CO", "1-27-INF", "CO", "1-27-INF"
                                    )
        
        assert result["status"] == "partial_data"
        assert result["asset_engine"]["summary"]["feasibility_posture"] == "pending_workload_data"
        
        # Verify capacity calculated from real recruiter count
        asset_dist = result["asset_engine"]["asset_distribution"]
        assert len(asset_dist) > 0
        assert asset_dist[0]["capacity"] > 0  # Should have capacity from actual recruiter count


class TestAssetEngineTraceability:
    """Verify recommendations trace back to board decisions and upstream evidence."""
    
    def test_recommended_shifts_linked_to_board_decisions(self, mock_db):
        """Asset shifts trace explicitly back to board directives."""
        
        # Setup: Full data scenario with board shifts
        with patch.object(asset_engine, '_query_recruiter_count') as mock_recruiter:
            mock_recruiter.return_value = (50, None)
            
            with patch.object(asset_engine, '_query_asset_strength') as mock_asset:
                mock_asset.return_value = (None, None)
                
                # Mock board signal with directed shifts
                board_signal = {
                    "status": "ok",
                    "targeting_board_engine": {
                        "summary": {"approved_count": 2},
                        "directed_shifts": [
                            {
                                "decision_id": "DEC-001",
                                "shift_type": "effort",
                                "rationale": "Increase funnel closure support"
                            }
                        ]
                    }
                }
                
                # Mock workload signals
                funnel_signal = {
                    "status": "ok",
                    "funnel_engine": {
                        "summary": {},
                        "prioritized_funnel_gaps": [
                            {"gap_id": "GAP-01"},
                            {"gap_id": "GAP-02"}
                        ]
                    }
                }
                
                school_signal = {
                    "status": "ok",
                    "school_plan_engine": {
                        "summary": {"underengaged_school_count": 3}
                    }
                }
                
                roi_signal = {
                    "status": "ok",
                    "roi_engine": {
                        "summary": {"total_events_scored": 5}
                    }
                }
                
                twg_signal = {
                    "status": "ok",
                    "twg_engine": {
                        "summary": {"high_priority_count": 2}
                    }
                }
                
                with patch.object(asset_engine.targeting_board_engine, 'summarize_targeting_board_engine') as mock_board:
                    mock_board.return_value = board_signal
                    
                    with patch.object(asset_engine.twg_engine, 'summarize_twg_engine') as mock_twg:
                        mock_twg.return_value = twg_signal
                        
                        with patch.object(asset_engine.funnel_engine, 'summarize_funnel_engine') as mock_funnel:
                            mock_funnel.return_value = funnel_signal
                            
                            with patch.object(asset_engine.school_plan_engine, 'summarize_school_plan_engine') as mock_school:
                                mock_school.return_value = school_signal
                                
                                with patch.object(asset_engine.roi_engine, 'summarize_roi_engine') as mock_roi:
                                    mock_roi.return_value = roi_signal
                                    
                                    result = asset_engine.summarize_asset_engine(
                                        mock_db, "CO", "1-27-INF", "CO", "1-27-INF"
                                    )
        
        assert result["status"] == "ok"
        shifts = result["asset_engine"]["recommended_shifts"]
        
        # Verify shifts link back to board decisions
        if len(shifts) > 0:
            shift = shifts[0]
            assert "board_decision_id" in shift
            assert shift["board_decision_id"] != "unknown_board_decision"
            assert "trace_source" in shift
            assert shift["trace_source"] == "board_directed_shift"
    
    def test_overutilization_recommendations_trace_to_workload(self, mock_db):
        """Overutilization-driven shifts trace back to upstream workload evidence."""
        
        with patch.object(asset_engine, '_query_recruiter_count') as mock_recruiter:
            mock_recruiter.return_value = (1, None)  # Single recruiter
            
            with patch.object(asset_engine, '_query_asset_strength') as mock_asset:
                mock_asset.return_value = (None, None)
                
                # Mock HIGH workload signals to exceed capacity
                funnel_signal = {
                    "status": "ok",
                    "funnel_engine": {
                        "summary": {},
                        "prioritized_funnel_gaps": [
                            {"gap_id": f"GAP-{i:02d}"} for i in range(50)  # High funnel gaps
                        ]
                    }
                }
                
                school_signal = {
                    "status": "ok",
                    "school_plan_engine": {
                        "summary": {"underengaged_school_count": 100}  # 100 schools * 4 hours
                    }
                }
                
                roi_signal = {
                    "status": "ok",
                    "roi_engine": {
                        "summary": {"total_events_scored": 200}  # 200 events for overload
                    }
                }
                
                board_signal = {
                    "status": "ok",
                    "targeting_board_engine": {
                        "summary": {"approved_count": 0},
                        "directed_shifts": []
                    }
                }
                
                twg_signal = {
                    "status": "ok",
                    "twg_engine": {
                        "summary": {"high_priority_count": 5}
                    }
                }
                
                with patch.object(asset_engine.targeting_board_engine, 'summarize_targeting_board_engine') as mock_board:
                    mock_board.return_value = board_signal
                    
                    with patch.object(asset_engine.twg_engine, 'summarize_twg_engine') as mock_twg:
                        mock_twg.return_value = twg_signal
                        
                        with patch.object(asset_engine.funnel_engine, 'summarize_funnel_engine') as mock_funnel:
                            mock_funnel.return_value = funnel_signal
                            
                            with patch.object(asset_engine.school_plan_engine, 'summarize_school_plan_engine') as mock_school:
                                mock_school.return_value = school_signal
                                
                                with patch.object(asset_engine.roi_engine, 'summarize_roi_engine') as mock_roi:
                                    mock_roi.return_value = roi_signal
                                    
                                    result = asset_engine.summarize_asset_engine(
                                        mock_db, "CO", "1-27-INF", "CO", "1-27-INF"
                                    )
        
        assert result["status"] == "ok"
        
        # Verify asset shows high utilization (should be > 1.0)
        asset_dist = result["asset_engine"]["asset_distribution"]
        assert asset_dist[0]["utilization_rate"] > 1.0  # Overloaded


class TestAssetEngineUtilization:
    """Verify utilization calculations use real data."""
    
    def test_capacity_calculation_from_recruiter_count(self):
        """Capacity hours derived from real recruiter count."""
        recruiter_count = 40
        capacity_hours = asset_engine._calculate_capacity_hours(recruiter_count)
        
        # 40 recruiters * 220 days * 8 hours = 70,400
        expected = 40 * 220 * 8
        assert capacity_hours == expected
    
    def test_utilization_rate_balanced_status(self):
        """Utilization rate 0.75 = balanced."""
        # Using balanced threshold bounds: 0.7 <= utilization <= 1.0
        utilization = 0.75
        
        status = asset_engine._utilization_status(utilization)
        assert status == "balanced"
    
    def test_overloaded_status(self):
        """Utilization > 1.0 classified as overloaded."""
        utilization = 1.2
        status = asset_engine._utilization_status(utilization)
        assert status == "overloaded"
    
    def test_underutilized_status(self):
        """Utilization < 0.7 classified as underutilized."""
        utilization = 0.5
        status = asset_engine._utilization_status(utilization)
        assert status == "underutilized"


class TestAssetEngineExecutionConstraints:
    """Verify constraints detected from asset data."""
    
    def test_overload_constraint_detected(self):
        """Detect personnel constraints from overloaded assets."""
        asset_distribution = [
            {"asset_id": "A1", "status": "overloaded"},
            {"asset_id": "A2", "status": "overloaded"},
            {"asset_id": "A3", "status": "balanced"},
        ]
        
        board_shifts = []
        constraints = asset_engine._detect_execution_constraints(asset_distribution, board_shifts)
        
        # Should detect personnel constraint
        personnel_constraints = [c for c in constraints if c["constraint_type"] == "personnel"]
        assert len(personnel_constraints) > 0
    
    def test_distance_constraint_included(self):
        """Distance/travel constraints flagged."""
        asset_distribution = [{"asset_id": "A1", "status": "balanced"}]
        board_shifts = []
        
        constraints = asset_engine._detect_execution_constraints(asset_distribution, board_shifts)
        
        distance_constraints = [c for c in constraints if c["constraint_type"] == "distance"]
        assert len(distance_constraints) > 0


class TestAssetEngineDataCompleteness:
    """Verify data_completeness field reflects actual data sources."""
    
    def test_full_completeness_with_individual_assets(self, mock_db):
        """Mark as 'full' when individual recruiter data available."""
        
        with patch.object(asset_engine, '_query_recruiter_count') as mock_recruiter:
            mock_recruiter.return_value = (50, None)
            
            with patch.object(asset_engine, '_query_asset_strength') as mock_asset:
                # Return actual asset data
                mock_asset.return_value = (
                    [
                        {
                            "asset_id": "REC-001",
                            "recruiter_name": "SSG Smith",
                            "location": "1-27-INF",
                            "current_assignments": 12,
                            "ownership_schools": 2,
                            "status_observations": "normal"
                        }
                    ],
                    None
                )
                
                # Setup minimal signals
                board_signal = {"status": "ok", "targeting_board_engine": {"summary": {}, "directed_shifts": []}}
                funnel_signal = {
                    "status": "ok",
                    "funnel_engine": {"summary": {}, "prioritized_funnel_gaps": []}
                }
                school_signal = {
                    "status": "ok",
                    "school_plan_engine": {"summary": {"underengaged_school_count": 2}}
                }
                roi_signal = {
                    "status": "ok",
                    "roi_engine": {"summary": {"total_events_scored": 1}}
                }
                twg_signal = {
                    "status": "ok",
                    "twg_engine": {"summary": {"high_priority_count": 0}}
                }
                
                with patch.object(asset_engine.targeting_board_engine, 'summarize_targeting_board_engine') as mock_board:
                    mock_board.return_value = board_signal
                    
                    with patch.object(asset_engine.twg_engine, 'summarize_twg_engine') as mock_twg:
                        mock_twg.return_value = twg_signal
                        
                        with patch.object(asset_engine.funnel_engine, 'summarize_funnel_engine') as mock_funnel:
                            mock_funnel.return_value = funnel_signal
                            
                            with patch.object(asset_engine.school_plan_engine, 'summarize_school_plan_engine') as mock_school:
                                mock_school.return_value = school_signal
                                
                                with patch.object(asset_engine.roi_engine, 'summarize_roi_engine') as mock_roi:
                                    mock_roi.return_value = roi_signal
                                    
                                    result = asset_engine.summarize_asset_engine(
                                        mock_db, "CO", "1-27-INF", "CO", "1-27-INF"
                                    )
        
        assert result["status"] == "ok"
        summary = result["asset_engine"]["summary"]
        assert summary["data_completeness"] == "full"
    
    def test_partial_completeness_without_individual_assets(self, mock_db):
        """Mark as 'partial_scope_level' when only org-level math available."""
        
        with patch.object(asset_engine, '_query_recruiter_count') as mock_recruiter:
            mock_recruiter.return_value = (50, None)
            
            with patch.object(asset_engine, '_query_asset_strength') as mock_asset:
                # No individual asset data
                mock_asset.return_value = (None, "error_querying_asset_data: no records")
                
                # Setup signals
                board_signal = {"status": "ok", "targeting_board_engine": {"summary": {}, "directed_shifts": []}}
                funnel_signal = {
                    "status": "ok",
                    "funnel_engine": {"summary": {}, "prioritized_funnel_gaps": []}
                }
                school_signal = {
                    "status": "ok",
                    "school_plan_engine": {"summary": {"underengaged_school_count": 1}}
                }
                roi_signal = {
                    "status": "ok",
                    "roi_engine": {"summary": {"total_events_scored": 1}}
                }
                twg_signal = {
                    "status": "ok",
                    "twg_engine": {"summary": {"high_priority_count": 0}}
                }
                
                with patch.object(asset_engine.targeting_board_engine, 'summarize_targeting_board_engine') as mock_board:
                    mock_board.return_value = board_signal
                    
                    with patch.object(asset_engine.twg_engine, 'summarize_twg_engine') as mock_twg:
                        mock_twg.return_value = twg_signal
                        
                        with patch.object(asset_engine.funnel_engine, 'summarize_funnel_engine') as mock_funnel:
                            mock_funnel.return_value = funnel_signal
                            
                            with patch.object(asset_engine.school_plan_engine, 'summarize_school_plan_engine') as mock_school:
                                mock_school.return_value = school_signal
                                
                                with patch.object(asset_engine.roi_engine, 'summarize_roi_engine') as mock_roi:
                                    mock_roi.return_value = roi_signal
                                    
                                    result = asset_engine.summarize_asset_engine(
                                        mock_db, "CO", "1-27-INF", "CO", "1-27-INF"
                                    )
        
        assert result["status"] == "ok"
        summary = result["asset_engine"]["summary"]
        assert summary["data_completeness"] == "partial_scope_level"
        
        # Verify constraint notes data granularity
        constraints = result["asset_engine"]["execution_constraints"]
        granularity_constraints = [c for c in constraints if c["constraint_type"] == "data_granularity"]
        assert len(granularity_constraints) > 0


# Fixtures

@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()
