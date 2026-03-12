"""Lightweight narrative generator for mission feasibility summaries.
This is a deterministic, non-ML helper that composes an explainable narrative
based on inputs, computed metrics, drivers, and gaps.
"""
from typing import Any, Dict, List


def _join_reasons(drivers: List[Dict[str, Any]]) -> str:
    if not drivers:
        return 'No primary drivers identified.'
    parts = []
    for d in drivers:
        t = d.get('type') or d.get('label') or 'unknown'
        v = d.get('value')
        parts.append(f"{t}: {v if v is not None else 'n/a'}")
    return '; '.join(parts)


def generate(summary: Dict[str, Any], drivers: List[Dict[str, Any]], gaps: List[Any]) -> Dict[str, Any]:
    unit = summary.get('unit_rsid') or 'USAREC'
    fy = summary.get('fy')
    inputs = summary.get('inputs', {})
    computed = summary.get('computed', {})

    what_changed = []
    why = []
    so_what = []
    now_what = []

    # What changed: differences between mission and market
    if inputs.get('annual_mission_contracts') is None:
        what_changed.append('Mission target missing')
    else:
        what_changed.append(f"Mission target: {inputs.get('annual_mission_contracts')}")

    if inputs.get('market_capacity_baseline') is None:
        why.append('Market capacity data missing')
    else:
        why.append(f"Market baseline: {inputs.get('market_capacity_baseline')}")

    if gaps:
        now_what.append({'action': 'ingest', 'detail': 'Supply missing datasets: ' + ', '.join(gaps)})

    # Drivers summary
    drivers_txt = _join_reasons(drivers)
    so_what.append({'drivers': drivers_txt})

    # Recommendations (heuristic)
    now_what.append({'action': 'recommend', 'detail': 'Consider adjusting mission, reallocating recruiters, or focusing markets with higher capacity.'})

    narrative = {
        'headline': f'Mission Feasibility for {unit} FY{fy}',
        'what_changed': what_changed,
        'why': why,
        'so_what': so_what,
        'now_what': now_what,
        'drivers_summary': drivers_txt,
        'confidence': 'low' if gaps else 'medium'
    }

    return {'narrative': narrative}
