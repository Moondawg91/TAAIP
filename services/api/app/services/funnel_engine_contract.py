from typing import Dict, Tuple

REQUIRED_CANONICAL_FIELDS = [
    "lead_id",
    "station_rsid",
    "company_id",
    "battalion_id",
    "zip",
    "lead_created_at",
    "appointment_date",
    "interview_date",
    "contract_date",
    "current_stage",
]

OPTIONAL_CANONICAL_FIELDS = [
    "school_id",
    "outcome_status",
    "processing_date",
    "action_history",
    "timestamp_history",
]

MIN_CONFIDENCE_REQUIRED = 0.40
MIN_CONFIDENCE_OPTIONAL = 0.25


def validate_inferred_mapping(mapping: Dict[str, Dict]) -> Tuple[bool, Dict]:
    missing_required = []
    ambiguous_required = []
    missing_optional = []

    for field in REQUIRED_CANONICAL_FIELDS:
        info = mapping.get(field) or {}
        idx = info.get("index")
        derived_from = info.get("derived_from")
        conf = float(info.get("confidence") or 0.0)
        if idx is None and not derived_from:
            missing_required.append(field)
        elif conf < MIN_CONFIDENCE_REQUIRED:
            ambiguous_required.append(f"{field}(confidence={round(conf, 3)})")

    for field in OPTIONAL_CANONICAL_FIELDS:
        info = mapping.get(field) or {}
        idx = info.get("index")
        derived_from = info.get("derived_from")
        conf = float(info.get("confidence") or 0.0)
        if (idx is None and not derived_from) or conf < MIN_CONFIDENCE_OPTIONAL:
            missing_optional.append(field)

    valid = len(missing_required) == 0 and len(ambiguous_required) == 0
    return valid, {
        "required_canonical_fields": REQUIRED_CANONICAL_FIELDS,
        "optional_canonical_fields": OPTIONAL_CANONICAL_FIELDS,
        "missing_required": missing_required,
        "ambiguous_required": ambiguous_required,
        "missing_optional": missing_optional,
        "valid": valid,
    }


def summarize_missing(validation: Dict) -> str:
    bits = []
    missing_required = validation.get("missing_required") or []
    ambiguous_required = validation.get("ambiguous_required") or []
    if missing_required:
        bits.append("missing required canonical fields: " + ", ".join(missing_required))
    if ambiguous_required:
        bits.append("ambiguous required canonical fields: " + ", ".join(ambiguous_required))
    if not bits:
        return ""
    return "; ".join(bits)
