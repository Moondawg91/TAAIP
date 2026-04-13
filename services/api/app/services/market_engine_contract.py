from typing import Dict, Iterable, List, Tuple

REQUIRED_COLUMNS = [
    "zip",
    "rsid_enlisted_station",
    "tot_male_18_19_b01001_007e",
    "tot_male_20_b01001_008e",
    "tot_male_21_b01001_009e",
    "tot_male_22_24_b01001_010e",
    "tot_female_18_19_b01001_031e",
    "tot_female_20_b01001_032e",
    "tot_female_21_b01001_033e",
    "tot_female_22_24_b01001_034e",
]

OPTIONAL_COLUMNS = [
    "rsid_enlisted_company",
    "rsid_enlisted_battalion",
    "rsid_enlisted_brigade",
    "enlisted_begin_effective_date",
    "enlisted_end_effective_date",
    "tot_nonvet_education_twenty_five_over_b21003_007e",
    "tot_nonvet_edu_high_school_b21003_009e",
    "tot_nonvet_edu_some_college_or_assoc_degree_b21003_010e",
    "tot_nonvet_edu_bachelors_or_higher_b21003_011e",
    "tot_median_income_vet_b21004_002e",
    "tot_median_income_nonvet_b21004_005e",
    "tot_median_income_nonvet_male_b21004_006e",
    "tot_median_income_nonvet_female_b21004_007e",
]


def validate_schema_columns(columns: Iterable[str]) -> Tuple[bool, Dict]:
    cols = {str(c) for c in columns}
    missing_required = [c for c in REQUIRED_COLUMNS if c not in cols]
    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in cols]
    return (
        len(missing_required) == 0,
        {
            "required_columns": REQUIRED_COLUMNS,
            "optional_columns": OPTIONAL_COLUMNS,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "valid": len(missing_required) == 0,
        },
    )


def normalize_zip(v) -> str:
    s = "" if v is None else str(v).strip()
    if not s:
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    s = "".join(ch for ch in s if ch.isdigit())
    return s.zfill(5)[:5] if s else ""


def safe_float(v, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        if isinstance(v, str) and not v.strip():
            return default
        return float(v)
    except Exception:
        return default


def normalize_rsid(v, fallback: str = "") -> str:
    s = "" if v is None else str(v).strip().upper()
    if not s:
        return fallback
    return s


def summarize_missing(schema_validation: Dict) -> str:
    missing = schema_validation.get("missing_required") or []
    if not missing:
        return ""
    return "missing required columns: " + ", ".join(missing)
