"""Inspect Recruiting Funnel workbook structure and emit a structural report.

Usage:
  python inspect_funnel_workbook.py /path/to/Recruiting\ Funnel\ Enriched.xlsx

Writes: artifacts/funnel_recalibrated/structural_report.json
"""
import sys
import os
import json
import pandas as pd
import re

OUT_DIR = os.path.join('artifacts','funnel_recalibrated')
os.makedirs(OUT_DIR, exist_ok=True)

def synth_col_name(i):
    return f"col_{i:03d}"

def profile_column(series):
    # series expected as strings
    s = series.dropna().astype(str)
    total = max(1, len(series))
    nulls = (series.isna() | (series.astype(str).str.strip()=='')).sum()
    null_ratio = float(nulls) / float(total)
    examples = list(s.head(5).unique())

    # heuristics for likely type
    likely = 'text'
    # email
    if s.str.contains(r'@', regex=True).sum() >= max(1, int(0.02*total)):
        likely = 'email'
    # epoch-like numeric timestamps (very long ints)
    elif s.str.match(r'^\d{9,16}$').sum() >= max(1, int(0.02*total)):
        likely = 'timestamp'
    # comma-separated arrays
    elif s.str.contains(r',').sum() >= max(1, int(0.02*total)):
        likely = 'array_text'
    # dates parseable
    else:
        parsed = pd.to_datetime(s, errors='coerce')
        if parsed.notna().sum() >= max(1, int(0.02*total)):
            likely = 'date'
        else:
            # numeric
            if s.str.match(r'^-?\d+(\.\d+)?$').sum() >= max(1, int(0.05*total)):
                likely = 'numeric'

    return {'null_ratio': null_ratio, 'example_values': examples, 'likely_type': likely}

def normalize_colname(name):
    if pd.isna(name): return ''
    s = str(name)
    # strip BOM and whitespace
    s = s.lstrip('\ufeff').strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def inspect(path):
    xl = pd.ExcelFile(path)
    report = {'path': path, 'sheets': {}}
    for sheet in xl.sheet_names:
        # Treat sheet as headerless positional data per decision
        df = pd.read_excel(xl, sheet_name=sheet, header=None, dtype=object)
        col_count = df.shape[1]

        synthetic_columns = [synth_col_name(i) for i in range(col_count)]

        # profile first up to 100 rows
        sample = df.head(100)
        positional_profile = {}
        for i, col in enumerate(sample.columns):
            series = sample[col]
            positional_profile[synthetic_columns[i]] = profile_column(series)

        report['sheets'][sheet] = {
            'sheet_name': sheet,
            'header_mode': 'none',
            'header_row_index': None,
            'synthetic_columns': True,
            'column_count': int(col_count),
            'positional_profile_top100': positional_profile
        }
    out = os.path.join(OUT_DIR,'structural_report.json')
    with open(out,'w') as f:
        json.dump(report, f, indent=2)
    print('Wrote', out)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: inspect_funnel_workbook.py /path/to/file.xlsx')
        sys.exit(1)
    inspect(sys.argv[1])
