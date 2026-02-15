"""CLI to import Zip Codes in USAREC.xlsx into DB"""
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2] / 'app'))

from database import SessionLocal
import crud


def main(filepath: str):
    db = SessionLocal()
    report = crud.import_zip_coverage_from_excel(db, filepath, source_file=filepath)
    print("ZIP coverage import report:")
    print(report)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: import_zips.py <path to Zip Codes in USAREC.xlsx>")
        sys.exit(1)
    main(sys.argv[1])
