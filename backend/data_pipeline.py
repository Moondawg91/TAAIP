import csv
import json
import os
import uuid
from typing import Dict, List, Tuple, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
MAPPINGS_FILE = os.path.join(DATA_DIR, 'data_mappings.json')

os.makedirs(PROCESSED_DIR, exist_ok=True)


def detect_columns(sample_rows: List[Dict[str, str]]) -> Dict[str, str]:
    """Simple heuristic to map incoming CSV columns to canonical fields.

    Returns a mapping {incoming_col: canonical_field}
    """
    # Canonical candidates: try to detect common names
    candidates = {
        'first_name': ['first', 'first_name', 'fname', 'given_name'],
        'last_name': ['last', 'last_name', 'lname', 'surname'],
        'email': ['email', 'email_address', 'e-mail'],
        'phone': ['phone', 'phone_number', 'tel', 'telephone'],
        'zip': ['zip', 'zipcode', 'postal', 'postal_code', 'zip_code'],
        'dob': ['dob', 'date_of_birth'],
        'applicant_id': ['id', 'app_id', 'applicant_id', 'applicantid'],
    }

    mapping: Dict[str, str] = {}
    headers = sample_rows[0].keys() if sample_rows else []
    for h in headers:
        hl = h.strip().lower()
        assigned = False
        for canon, variants in candidates.items():
            for v in variants:
                if v in hl:
                    mapping[h] = canon
                    assigned = True
                    break
            if assigned:
                break
        if not assigned:
            mapping[h] = h  # passthrough unknown columns

    return mapping


def process_csv(file_path: str) -> Tuple[str, Dict[str, Any]]:
    """Read CSV, detect columns, normalize rows, save processed JSON and mapping.

    Returns (dataset_name, metadata)
    """
    dataset_name = f"dataset_{uuid.uuid4().hex[:8]}"
    out_path = os.path.join(PROCESSED_DIR, f"{dataset_name}.json")

    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader]

    mapping = detect_columns(rows[:5]) if rows else {}

    # Normalize rows according to mapping
    normalized = []
    for r in rows:
        nr = {}
        for k, v in r.items():
            mapped = mapping.get(k, k)
            nr[mapped] = v.strip() if isinstance(v, str) else v
        normalized.append(nr)

    # Save processed JSON
    with open(out_path, 'w', encoding='utf-8') as out:
        json.dump({'mapping': mapping, 'rows': normalized}, out, ensure_ascii=False)

    # Update mappings file
    mappings = {}
    if os.path.exists(MAPPINGS_FILE):
        try:
            with open(MAPPINGS_FILE, 'r', encoding='utf-8') as mfp:
                mappings = json.load(mfp)
        except Exception:
            mappings = {}

    mappings[dataset_name] = {
        'filename': os.path.basename(file_path),
        'stored_path': out_path,
        'mapping': mapping,
        'rows': len(normalized),
    }

    with open(MAPPINGS_FILE, 'w', encoding='utf-8') as mfp:
        json.dump(mappings, mfp, ensure_ascii=False, indent=2)

    metadata = mappings[dataset_name]
    return dataset_name, metadata


def list_datasets() -> Dict[str, Any]:
    if os.path.exists(MAPPINGS_FILE):
        with open(MAPPINGS_FILE, 'r', encoding='utf-8') as mfp:
            return json.load(mfp)
    return {}


def get_dataset(dataset_name: str) -> Dict[str, Any]:
    path = os.path.join(PROCESSED_DIR, f"{dataset_name}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    raise FileNotFoundError(dataset_name)
