from typing import Dict, List, Tuple

CONTRACTS: Dict[str, Dict[str, List[str]]] = {
    "market": {
        "required": ["station_rsid", "zip_code", "market_category", "qma_population"],
        "optional": ["contracts_actual", "write_rate_actual", "data_as_of"],
    },
    "burden": {
        "required": ["scope_type", "scope_value", "mission_requirement", "recruiter_strength", "reporting_date"],
        "optional": ["source_system", "reported_at"],
    },
    "school_access": {
        "required": ["school_id", "school_name", "station_rsid"],
        "optional": ["zip_code", "enrollment", "zone_valid"],
    },
    "execution_quality": {
        "required": ["lead_key", "station_rsid", "to_stage", "transitioned_at"],
        "optional": ["from_stage", "transition_reason", "technician_user"],
    },
}


def validate_contract(dataset_type: str, columns: List[str]) -> Tuple[bool, Dict]:
    dset = (dataset_type or "").strip().lower()
    if dset not in CONTRACTS:
        return False, {"error": "unknown_dataset_type", "supported": sorted(CONTRACTS.keys())}

    c = CONTRACTS[dset]
    cols = {str(x) for x in (columns or [])}
    missing = [x for x in c["required"] if x not in cols]

    return (
        len(missing) == 0,
        {
            "dataset_type": dset,
            "required": c["required"],
            "optional": c["optional"],
            "missing_required": missing,
            "valid": len(missing) == 0,
        },
    )
