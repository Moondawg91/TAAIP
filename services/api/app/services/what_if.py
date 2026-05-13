from typing import Dict

from services.api.app.services import forecasting


def run_what_if(db, scope_type: str, scope_value: str, scenario: Dict) -> Dict:
    assumptions = {
        "mission_delta": float(scenario.get("mission_delta", 0.0) or 0.0),
        "effort_shift": float(scenario.get("effort_shift", 0.0) or 0.0),
        "burden_delta": float(scenario.get("burden_delta", 0.0) or 0.0),
        "access_delta": float(scenario.get("access_delta", 0.0) or 0.0),
        "targeting_shift": float(scenario.get("targeting_shift", 0.0) or 0.0),
    }

    proj = forecasting.project_scope(db, scope_type, scope_value, assumptions=assumptions)
    proj["scenario_name"] = str(scenario.get("scenario_name") or "unnamed_scenario")
    return proj
