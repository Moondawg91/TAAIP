"""CLI to import RSIDs USAREC.xlsx into DB"""
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app import crud


def main(filepath: str):
    db = SessionLocal()
    report = crud.import_rsids_from_excel(db, filepath)
    print("RSID import report:")
    print(report)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: import_rsids.py <path to RSIDs USAREC.xlsx>")
        sys.exit(1)
    main(sys.argv[1])
