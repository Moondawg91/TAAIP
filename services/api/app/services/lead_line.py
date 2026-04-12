from datetime import date


def calculate_lead_line(ytd_actual: int, annual_mission: int):
    """Calculate expected YTD pacing and status.

    Returns a dict with expected_ytd, actual_ytd, variance, status.
    """
    today = date.today()
    start_of_year = date(today.year, 1, 1)

    days_elapsed = (today - start_of_year).days + 1
    total_days = 365

    try:
        expected_ytd = (days_elapsed / total_days) * float(annual_mission or 0)
    except Exception:
        expected_ytd = 0.0

    variance = float(ytd_actual or 0) - expected_ytd

    if variance >= 0:
        status = "ON_TRACK"
    elif variance >= -1:
        status = "SLIGHTLY_BEHIND"
    else:
        status = "BEHIND"

    return {
        "expected_ytd": round(expected_ytd, 2),
        "actual_ytd": int(ytd_actual or 0),
        "variance": round(variance, 2),
        "status": status,
    }
