import re

# Candidate person id column names (case-insensitive)
PERSON_ID_CANDIDATES = [
    'person_id','id','applicant_id','applicantid','source_id','sourceid','candidate_id','candidateid','lead_id','leadid','uid'
]

# Helpful regexes for positional inference (exported for use by recalibrator)
EMAIL_REGEX = r"\S+@\S+\.\S+"
ZIP_REGEX = r'^[0-9]{5}(-[0-9]{4})?$'
EPOCH_LIST_REGEX = r'^\d{9,16}(,\s*\d{9,16})*$'

# Canonical field mapping rules: list of (regex_pattern, canonical_field_name)
# Patterns are matched against normalized column names (lowercased, underscores)
CANONICAL_COLUMN_RULES = [
    (r'timestamp|date|dt|time', 'event_timestamp_raw'),
    (r'stage|lifecycle|status', 'lifecycle_stage_raw'),
    (r'activity|action|event_code', 'activity_code_raw'),
    (r'activity_label|action_label|event_label', 'activity_label_raw'),
    (r'outcome', 'outcome_raw'),
    (r'recruiter', 'recruiter_id_candidate'),
    (r'company|station|rsid', 'source_description_candidate'),
    (r'note|comments|remark', 'note_raw'),
    (r'zip|postal', 'postal_code_raw')
]

# Stage mapping: maps common raw labels/codes to standardized funnel stages.
# All keys are matched case-insensitively after stripping.
STAGE_MAP = {
    # Lead phase
    "LEAD": "Lead",
    "Lead": "Lead",
    "PROSPECT": "Lead",
    "Prospect": "Lead",

    # Mid funnel
    "APPLICANT": "Applicant",
    "Applicant": "Applicant",

    # Contract / DEP
    "DELAYED ENTRY PROGRAM": "DEP",
    "DELAYED TRAINING PROGRAM": "DEP",
    "FS PGM": "DEP",

    # Training / shipped
    "IADT": "Ship",
    "SHIPPED": "Ship",
    "Shipped": "Ship",

    # Edge cases
    "PENDING UNIT MEMBER": "Other"
}

# Milestone mapping (high-level funnel milestones)
MILESTONE_MAP = {
    "Lead": "lead_created",
    "Applicant": "application_started",
    "DEP": "contracted",
    "Ship": "shipped"
}

def map_to_canonical(colname: str):
    """Return canonical field name for a given normalized column name, or None."""
    n = colname.lower()
    for pattern, canonical in CANONICAL_COLUMN_RULES:
        if re.search(pattern, n):
            return canonical
    return None

def map_stage(raw_stage: str):
    if raw_stage is None:
        return None
    key = str(raw_stage).strip()
    # try exact, upper, and lower lookups to be forgiving
    if key in STAGE_MAP:
        return STAGE_MAP.get(key)
    if key.upper() in STAGE_MAP:
        return STAGE_MAP.get(key.upper())
    if key.lower() in STAGE_MAP:
        return STAGE_MAP.get(key.lower())
    return None
