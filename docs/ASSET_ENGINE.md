## Asset Engine - Recruiter Strength & Utilization

### Overview
The Asset Engine calculates recruiter/asset utilization from upstream workload signals and generates realistic reallocation recommendations traceable to board decisions. It enforces three hard rules:

1. **Real Data Only**: Uses actual recruiter strength and workload data from database; no fabricated capacities
2. **Structured Constraints**: Returns `no_data` or `partial_data` with explicit constraints when data unavailable
3. **Full Traceability**: All asset recommendations trace back to specific board decisions and upstream engine evidence

### Inputs (Consume-Only; No Independent Analytics)

| Source | Signal | Purpose |
|--------|--------|---------|
| **targeting_board_engine** | `board_decisions`, `directed_shifts` | Board-directed reallocations to evaluate |
| **twg_engine** | Workload indicators, high-priority count | Current tasking load |
| **funnel_engine** | Prioritized funnel gaps | Recruitment funnel effort demands |
| **school_plan_engine** | Underengaged school count | School engagement effort demands |
| **roi_engine** | Event count and effectiveness | Event planning workload |
| **CRUD: recruiter_strength** | Actual recruiter count by scope | Real capacity baseline (required) |
| **CRUD: recruiter_assignments** | Individual recruiter workload/ownership | Individual asset utilization (optional, for granularity) |

### Data Availability Scenarios

#### No Data (`status: no_data`)
- **When**: No recruiter data found AND insufficient workload signals
- **Returns**: Empty asset distribution, constraints listing data_availability issues
- **Action**: Operator must ingest recruiter roster or enable workload signals

#### Partial Data (`status: partial_data`)
- **When**: Recruiter count available but no workload signals
- **Returns**: Single synthetic asset at scope level with capacity but 0% utilization
- **Note**: Marks `feasibility_posture: pending_workload_data`; further analysis blocked

#### Full Data (`status: ok`)
- **When**: Both recruiter capacity and workload signals present
- **Returns**: Complete utilization analysis with recommendations
- **Completeness**: `full` (individual assets) or `partial_scope_level` (org-level math)

### Outputs

```json
{
  "status": "ok",
  "asset_engine": {
    "summary": {
      "total_assets": 35,
      "overutilized_assets": 8,
      "underutilized_assets": 2,
      "balanced_assets": 25,
      "execution_risk_level": "medium",
      "feasibility_posture": "feasible",
      "data_completeness": "full"
    },
    "asset_distribution": [
      {
        "asset_id": "REC-001",
        "recruiter_name": "SSG Smith",
        "location": "1-27-INF",
        "current_assignments": 15,
        "ownership_schools": 3,
        "current_load": 120.5,
        "capacity": 1760.0,
        "utilization_rate": 0.0685,
        "status": "balanced",
        "primary_workload_driver": "funnel_closure",
        "data_source": "recruiter_assignment_records"
      }
    ],
    "recommended_shifts": [
      {
        "shift_id": "SHIFT-ABC123",
        "board_decision_id": "DEC-001",
        "shift_type": "effort",
        "justification": "Support board directive: increase funnel closure support",
        "feasibility": "high",
        "capacity_impact_hours": 8.0,
        "available_capacity_hours": 450.0,
        "expected_effect": "Reallocate asset from lower-priority area to supported board decision",
        "trace_id": "SHIFT-ABC123",
        "trace_source": "board_directed_shift"
      }
    ],
    "execution_constraints": [
      {
        "constraint_id": "CONST-XYZ789",
        "constraint_type": "personnel",
        "description": "8 assets overloaded; capacity limits execution",
        "affected_area": "overall_operations",
        "severity": "medium",
        "trace_id": "CONST-XYZ789"
      }
    ],
    "data_sources": {
      "recruiter_strength": "crud_domain.read_recruiter_count() [REAL DATA]",
      "asset_assignments": "crud_domain.read_recruiter_assignments() [REAL DATA]",
      "board": "targeting_board_engine.summarize_targeting_board_engine()",
      "twg": "twg_engine.summarize_twg_engine()",
      "funnel": "funnel_engine.summarize_funnel_engine()",
      "school_plan": "school_plan_engine.summarize_school_plan_engine()",
      "roi": "roi_engine.summarize_roi_engine()"
    },
    "data_as_of": "2026-04-13T19:45:32.123Z"
  }
}
```

### Key Calculations

**Capacity (hours/period)**
```
capacity_hours = recruiter_count * 220_working_days * 8_hours_per_day
```

**Utilization Rate**
```
utilization_rate = current_workload_hours / capacity_hours

Classification:
- > 1.0: overloaded (unsustainable)
- 0.7-1.0: balanced (optimal)  
- < 0.7: underutilized (excess capacity)
```

**Workload Estimation** (hours)
```
funnel_workload = gaps_count × 6  # hours per gap closure
school_workload = underengaged_schools × 4  # hours per engagement
event_workload = total_events × 8  # hours per event
twg_workload = high_priority_items × 6  # hours per due-out
```

### Integration Points

1. **Command Center** (`/api/v2/decision-output/command-center`)
   - Includes asset utilization in phase2_overview
   - Feeds asset constraints into feasibility assessment

2. **Mission Decrease Justification** (`/api/v2/decision-output/mission-decrease-justification`)
   - Asset signals inform mission adjustment logic
   - Constraints block or slow mission optimization

3. **PowerBI Feed** (`/api/v2/feeds/command-dataset`)
   - Asset distribution exported for dashboard
   - Recommended shifts feed executive reporting

### Hard Rules Enforcement

#### Rule 1: Real Data Only
- ✅ Queries `crud_domain.read_recruiter_count()` for actual capacity
- ✅ Queries `crud_domain.read_recruiter_assignments()` for individual asset data
- ❌ Never uses hardcoded reference capacity estimates (used only as fallback for org math)
- ⚠️ If query fails, returns structured no_data constraint, never invents baseline

#### Rule 2: Structured Constraints When Data Missing
- ✅ Returns `partial_data` when recruiter found but workload unavailable
- ✅ Returns `no_data` when both data types missing
- ✅ Includes `execution_constraints` array explaining why analysis blocked
- ❌ Never silently returns empty results without constraint explanation

#### Rule 3: Recommendations Traceable to Board/Evidence
- ✅ Every recommended shift includes `board_decision_id` (if board-driven)
- ✅ Every shift includes `trace_source` (e.g., `board_directed_shift`, `asset_overutilization_detected`)
- ✅ Every shift references upstream evidence (`upstream_evidence: "funnel_high"`)
- ❌ Never generates recommendations without linking to board decision or workload evidence

### Testing

Run full test suite:
```bash
pytest services/api/tests/test_asset_engine.py -v
```

Core test classes:
- `TestAssetEngineConstraintHandling`: Validates no_data/partial_data scenarios
- `TestAssetEngineTraceability`: Confirms recommendations link to board decisions
- `TestAssetEngineUtilization`: Verifies capacity/workload calculations
- `TestAssetEngineDataCompleteness`: Tests data_completeness field accuracy

### Future Extensions

1. **Geographic Constraints**: Add travel time between priority locations
2. **Skill-Based Allocation**: Match recruiter skills to mission demands
3. **Bench Forecasting**: Predict underutilization periods for training
4. **Load Balancing**: Recommend shifts to equalize asset utilization
5. **Cost Optimization**: Weight shifts by recruiter tour cost/grade
