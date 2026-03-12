from typing import List, Tuple, Optional
from .column_normalizer import normalize_col_name

FILTER_PHRASES = [
    'applied filters', 'filters:', 'report run', 'generated', 'as of', 'date range', 'exported'
]

def is_filter_line(cells: List[str]) -> bool:
    text = ' '.join([str(c or '').lower() for c in cells])
    for p in FILTER_PHRASES:
        if p in text:
            return True
    return False

def candidate_headers(sheet_preview: List[List[str]], required_normalized: List[str]) -> Optional[dict]:
    # sheet_preview: list of rows (each row is list of cell strings)
    best = None
    for idx, row in enumerate(sheet_preview):
        if not row or sum(1 for c in row if c not in (None, '')) < 3: continue
        if is_filter_line(row): continue
        # normalize cells
        norm = [normalize_col_name(str(c)) for c in row]
        # count matches
        matches = sum(1 for r in required_normalized if r in norm)
        # signature bonus: uniqueness
        unique_count = len(set(norm))
        score = matches + (unique_count / max(len(norm),1))
        if best is None or score > best['score']:
            best = {'score': score, 'index': idx, 'raw': row, 'normalized': norm, 'matches': matches}
    return best
