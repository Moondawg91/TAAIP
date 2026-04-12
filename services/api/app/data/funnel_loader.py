import pandas as pd
from pathlib import Path

BASE_PATH = Path("artifacts/funnel_recalibrated")

def load_funnel_data():
    events_path = BASE_PATH / "funnel_events_long.csv"
    summary_path = BASE_PATH / "funnel_summary.csv"

    if not events_path.exists() or not summary_path.exists():
        raise FileNotFoundError("Funnel artifacts not found")

    events = pd.read_csv(events_path)
    summary = pd.read_csv(summary_path)

    # 🔥 FORCE datetime parsing
    for col in ["lead_at", "applicant_at", "dep_at", "ship_at"]:
        if col in summary.columns:
            summary[col] = pd.to_datetime(summary[col], errors="coerce")

    return events, summary
