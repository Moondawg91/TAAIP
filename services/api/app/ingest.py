import os
import json
import pandas as pd
from .database import SessionLocal
from . import models_ingest, models
from sqlalchemy.orm import Session
import re


def read_file_to_df(path: str):
    # try excel, then csv, then json
    try:
        if path.lower().endswith('.xlsx') or path.lower().endswith('.xls'):
            return pd.read_excel(path, engine='openpyxl')
        if path.lower().endswith('.csv'):
            return pd.read_csv(path)
        if path.lower().endswith('.json'):
            return pd.read_json(path)
    except Exception:
        raise
    raise ValueError('Unsupported file type')


def apply_recipe_to_df(df: pd.DataFrame, steps: list) -> (pd.DataFrame, dict):
    report = {"steps": [], "rows_before": len(df), "rows_after": None}
    cur = df.copy()
    for step in steps:
        stype = step.get('type')
        if stype == 'cast':
            col = step['column']
            to_type = step['to']
            try:
                if to_type == 'int':
                    cur[col] = pd.to_numeric(cur[col], errors='coerce').astype('Int64')
                elif to_type == 'float':
                    cur[col] = pd.to_numeric(cur[col], errors='coerce')
                elif to_type == 'str':
                    cur[col] = cur[col].astype(str)
                report['steps'].append({'step': step, 'status': 'ok'})
            except Exception as e:
                report['steps'].append({'step': step, 'status': 'error', 'error': str(e)})
        elif stype == 'filter':
            expr = step['expr']
            try:
                cur = cur.query(expr)
                report['steps'].append({'step': step, 'status': 'ok'})
            except Exception as e:
                report['steps'].append({'step': step, 'status': 'error', 'error': str(e)})
        elif stype == 'dedupe':
            cols = step.get('columns')
            cur = cur.drop_duplicates(subset=cols)
            report['steps'].append({'step': step, 'status': 'ok'})
        elif stype == 'map':
            col = step['column']
            mapping = step.get('mapping', {})
            cur[col] = cur[col].map(mapping).fillna(cur[col])
            report['steps'].append({'step': step, 'status': 'ok'})
        else:
            report['steps'].append({'step': step, 'status': 'skipped', 'reason': 'unknown step type'})

    report['rows_after'] = len(cur)
    return cur, report


def save_ingested_file(db: Session, filename: str, source: str, uploaded_by: str):
    f = models_ingest.IngestedFile(filename=filename, source=source, uploaded_by=uploaded_by)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def run_ingest(path: str, recipe: dict = None, uploaded_by: str = None):
    db = SessionLocal()
    try:
        ing = save_ingested_file(db, os.path.basename(path), path, uploaded_by)
        steps = recipe.get('steps') if recipe else []
        df = read_file_to_df(path)
        out_df, report = apply_recipe_to_df(df, steps)
        run = models_ingest.IngestRun(file_id=ing.id, recipe_id=recipe.get('id') if recipe else None, status='completed', report=report)
        db.add(run)
        db.commit()
        db.refresh(run)
        return {'file': ing.id, 'run': run.id, 'report': report, 'preview': out_df.head(20).to_dict(orient='records')}
    finally:
        db.close()
