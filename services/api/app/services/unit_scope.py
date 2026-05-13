"""Unit scope resolver: returns the full RSID list for a given echelon anchor.

For a station-level RSID this is just [rsid].
For any higher echelon (BN, CO, BDE, CMD, …) it is [rsid] plus every
subordinate station/unit RSID resolved via the org_unit hierarchy.

Usage:
    from .unit_scope import get_unit_scope
    scope = get_unit_scope("0101AA")          # -> ["0101AA", "0101AB", ...]
    query = query.filter(Model.station_rsid.in_(scope))
"""

from typing import List

from .org_unit_resolver import resolve_subordinate_units
from .runtime_cache import bucket


def get_unit_scope(rsid: str) -> List[str]:
    """Return a deduplicated list of RSIDs representing *rsid* and all of its
    subordinate units.

    Args:
        rsid: The anchor RSID for any echelon (STN, CO, BN, BDE, CMD, …).

    Returns:
        A list beginning with *rsid* followed by every descendant RSID, with
        no duplicates.  Returns an empty list when *rsid* is falsy.
    """
    if not rsid:
        return []

    cache = bucket("unit_scope")
    cache_key = f"unit_scope:{rsid}"
    cached = cache.get(cache_key)
    if cached is not None:
        return list(cached)

    subordinates = resolve_subordinate_units(rsid)

    # resolve_subordinate_units returns [rsid] for STN echelon and the
    # subordinate descendants for higher echelons.  Build a deduplicated set
    # that always includes the anchor itself.
    seen: set = {rsid}
    scope: List[str] = [rsid]
    for r in subordinates:
        if r not in seen:
            seen.add(r)
            scope.append(r)

    cache.set(cache_key, list(scope))

    return scope
