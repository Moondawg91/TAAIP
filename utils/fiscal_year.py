"""
USAREC Fiscal Year and Recruiting Calendar Utilities
Handles FY, RY, recruiting months, and ship month calculations
"""
from datetime import datetime, date
from typing import Tuple


def get_fiscal_year(date_obj: datetime = None) -> int:
    """
    Get fiscal year for a given date.
    Federal fiscal year runs October 1 - September 30
    
    Examples:
        Oct 1, 2024 - Sep 30, 2025 = FY2025
        Oct 1, 2025 - Sep 30, 2026 = FY2026
    """
    if date_obj is None:
        date_obj = datetime.now()
    
    if date_obj.month >= 10:  # October or later
        return date_obj.year + 1
    else:
        return date_obj.year


def get_recruiting_year(date_obj: datetime = None) -> str:
    """
    Get recruiting year (RY) for a given date.
    Same as fiscal year but formatted as string: "RY2025"
    """
    fy = get_fiscal_year(date_obj)
    return f"RY{fy}"


def get_quarter(date_obj: datetime = None) -> str:
    """
    Get fiscal quarter (Q1-Q4) for a given date.
    Q1: Oct-Dec
    Q2: Jan-Mar
    Q3: Apr-Jun
    Q4: Jul-Sep
    """
    if date_obj is None:
        date_obj = datetime.now()
    
    month = date_obj.month
    
    if 10 <= month <= 12:  # Oct, Nov, Dec
        return "Q1"
    elif 1 <= month <= 3:  # Jan, Feb, Mar
        return "Q2"
    elif 4 <= month <= 6:  # Apr, May, Jun
        return "Q3"
    else:  # Jul, Aug, Sep
        return "Q4"


def get_ship_month(date_obj: datetime = None) -> str:
    """
    Get ship month in format "YYYY-MM" for tracking when recruits ship to basic training
    """
    if date_obj is None:
        date_obj = datetime.now()
    
    return date_obj.strftime("%Y-%m")


def parse_ship_month(ship_month: str) -> Tuple[int, int]:
    """
    Parse ship month string "YYYY-MM" into (year, month) tuple
    """
    try:
        parts = ship_month.split("-")
        return (int(parts[0]), int(parts[1]))
    except (IndexError, ValueError):
        return (datetime.now().year, datetime.now().month)


def get_recruiting_month_name(date_obj: datetime = None) -> str:
    """
    Get recruiting month name with fiscal year context
    Example: "October 2024 (FY25 Q1)"
    """
    if date_obj is None:
        date_obj = datetime.now()
    
    month_name = date_obj.strftime("%B %Y")
    fy = get_fiscal_year(date_obj)
    quarter = get_quarter(date_obj)
    
    return f"{month_name} (FY{fy % 100} {quarter})"


def calculate_flash_to_bang_days(start_date: datetime, end_date: datetime = None) -> int:
    """
    Calculate "flash-to-bang" time - days from start to end event
    Used for:
    - Lead to Contract time
    - Contract to Ship time
    - Lead to Ship time
    """
    if end_date is None:
        end_date = datetime.now()
    
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    delta = end_date - start_date
    return max(0, delta.days)


def get_fy_date_range(fiscal_year: int) -> Tuple[datetime, datetime]:
    """
    Get start and end dates for a fiscal year
    
    Args:
        fiscal_year: FY number (e.g., 2025 for FY2025)
    
    Returns:
        (start_date, end_date) tuple
        FY2025: (Oct 1, 2024, Sep 30, 2025)
    """
    start_date = datetime(fiscal_year - 1, 10, 1)  # October 1 of previous calendar year
    end_date = datetime(fiscal_year, 9, 30, 23, 59, 59)  # September 30 of FY year
    
    return (start_date, end_date)


def is_in_fiscal_year(date_obj: datetime, fiscal_year: int) -> bool:
    """Check if a date falls within a specific fiscal year"""
    start, end = get_fy_date_range(fiscal_year)
    return start <= date_obj <= end


def get_recruiting_year_goals(fiscal_year: int) -> dict:
    """
    Get USAREC recruiting goals for a fiscal year
    These are example/placeholder values - should be updated with actual USAREC goals
    """
    return {
        "fiscal_year": fiscal_year,
        "total_contracts_goal": 60000,  # Example goal
        "regular_army_goal": 55000,
        "army_reserve_goal": 5000,
        "quarterly_goals": {
            "Q1": 15000,  # Oct-Dec
            "Q2": 15000,  # Jan-Mar
            "Q3": 15000,  # Apr-Jun
            "Q4": 15000,  # Jul-Sep
        },
        "monthly_run_rate": 5000,  # Contracts per month to meet goal
    }


def calculate_dep_length(dep_date: datetime, ship_date: datetime = None) -> int:
    """
    Calculate length of time in DEP (Delayed Entry Program)
    Typical DEP length: 1-365 days
    """
    if ship_date is None:
        ship_date = datetime.now()
    
    return calculate_flash_to_bang_days(dep_date, ship_date)


def get_current_fy_progress() -> dict:
    """Get current fiscal year progress information"""
    now = datetime.now()
    fy = get_fiscal_year(now)
    start, end = get_fy_date_range(fy)
    
    total_days = (end - start).days
    elapsed_days = (now - start).days
    remaining_days = (end - now).days
    
    progress_pct = (elapsed_days / total_days * 100) if total_days > 0 else 0
    
    return {
        "fiscal_year": fy,
        "recruiting_year": get_recruiting_year(now),
        "quarter": get_quarter(now),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "current_date": now.isoformat(),
        "elapsed_days": elapsed_days,
        "remaining_days": remaining_days,
        "total_days": total_days,
        "progress_percent": round(progress_pct, 1),
    }


# USAREC Calendar Reference
USAREC_CALENDAR = {
    "fiscal_year": {
        "start_month": "October",
        "end_month": "September",
        "quarters": {
            "Q1": ["October", "November", "December"],
            "Q2": ["January", "February", "March"],
            "Q3": ["April", "May", "June"],
            "Q4": ["July", "August", "September"],
        }
    },
    "recruiting_year": "Same as fiscal year (RY2025 = FY2025)",
    "ship_months": "Tracked monthly for basic training departures",
    "reporting_period": "Monthly with quarterly reviews",
}


if __name__ == "__main__":
    # Test the utilities
    print("USAREC Fiscal Year Utilities Test")
    print("=" * 50)
    
    now = datetime.now()
    print(f"Current Date: {now.strftime('%B %d, %Y')}")
    print(f"Fiscal Year: FY{get_fiscal_year()}")
    print(f"Recruiting Year: {get_recruiting_year()}")
    print(f"Quarter: {get_quarter()}")
    print(f"Ship Month: {get_ship_month()}")
    print(f"Recruiting Month: {get_recruiting_month_name()}")
    
    print("\nFY Progress:")
    progress = get_current_fy_progress()
    print(f"  {progress['recruiting_year']} {progress['quarter']}")
    print(f"  {progress['elapsed_days']} days elapsed")
    print(f"  {progress['remaining_days']} days remaining")
    print(f"  {progress['progress_percent']}% complete")
    
    print("\nFlash-to-Bang Example:")
    lead_date = datetime(2024, 10, 1)
    contract_date = datetime(2024, 12, 15)
    days = calculate_flash_to_bang_days(lead_date, contract_date)
    print(f"  Lead Date: {lead_date.strftime('%B %d, %Y')}")
    print(f"  Contract Date: {contract_date.strftime('%B %d, %Y')}")
    print(f"  Flash-to-Bang: {days} days")
