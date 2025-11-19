"""
USAREC Organizational Hierarchy - RSID Structure
Enables filtering from USAREC down to station level
"""

# USAREC RSID Hierarchy Mapping
USAREC_HIERARCHY = {
    "USAREC": {
        "name": "U.S. Army Recruiting Command",
        "level": "command",
        "brigades": {
            "1BDE": {
                "name": "1st Recruiting Brigade",
                "battalions": {
                    "1BN": {"name": "1st Battalion", "stations": ["1-1", "1-2", "1-3"]},
                    "2BN": {"name": "2nd Battalion", "stations": ["2-1", "2-2", "2-3"]},
                    "3BN": {"name": "3rd Battalion", "stations": ["3-1", "3-2", "3-3"]},
                }
            },
            "2BDE": {
                "name": "2nd Recruiting Brigade",
                "battalions": {
                    "4BN": {"name": "4th Battalion", "stations": ["4-1", "4-2", "4-3"]},
                    "5BN": {"name": "5th Battalion", "stations": ["5-1", "5-2", "5-3"]},
                    "6BN": {"name": "6th Battalion", "stations": ["6-1", "6-2", "6-3"]},
                }
            },
            "3BDE": {
                "name": "3rd Recruiting Brigade",
                "battalions": {
                    "7BN": {"name": "7th Battalion", "stations": ["7-1", "7-2", "7-3"]},
                    "8BN": {"name": "8th Battalion", "stations": ["8-1", "8-2", "8-3"]},
                    "9BN": {"name": "9th Battalion", "stations": ["9-1", "9-2", "9-3"]},
                }
            },
            "4BDE": {
                "name": "4th Recruiting Brigade",
                "battalions": {
                    "10BN": {"name": "10th Battalion", "stations": ["10-1", "10-2", "10-3"]},
                    "11BN": {"name": "11th Battalion", "stations": ["11-1", "11-2", "11-3"]},
                    "12BN": {"name": "12th Battalion", "stations": ["12-1", "12-2", "12-3"]},
                }
            },
            "5BDE": {
                "name": "5th Recruiting Brigade",
                "battalions": {
                    "13BN": {"name": "13th Battalion", "stations": ["13-1", "13-2", "13-3"]},
                    "14BN": {"name": "14th Battalion", "stations": ["14-1", "14-2", "14-3"]},
                    "15BN": {"name": "15th Battalion", "stations": ["15-1", "15-2", "15-3"]},
                }
            },
            "6BDE": {
                "name": "6th Recruiting Brigade",
                "battalions": {
                    "16BN": {"name": "16th Battalion", "stations": ["16-1", "16-2", "16-3"]},
                    "17BN": {"name": "17th Battalion", "stations": ["17-1", "17-2", "17-3"]},
                    "18BN": {"name": "18th Battalion", "stations": ["18-1", "18-2", "18-3"]},
                }
            },
        }
    }
}

def get_all_brigades():
    """Get list of all brigades"""
    return list(USAREC_HIERARCHY["USAREC"]["brigades"].keys())

def get_battalions_for_brigade(brigade_id):
    """Get battalions under a specific brigade"""
    try:
        return list(USAREC_HIERARCHY["USAREC"]["brigades"][brigade_id]["battalions"].keys())
    except KeyError:
        return []

def get_stations_for_battalion(brigade_id, battalion_id):
    """Get stations under a specific battalion"""
    try:
        return USAREC_HIERARCHY["USAREC"]["brigades"][brigade_id]["battalions"][battalion_id]["stations"]
    except KeyError:
        return []

def get_full_hierarchy_path(rsid):
    """
    Parse RSID and return full organizational path
    RSID format: [Brigade]-[Battalion]-[Station]
    Example: 1BDE-1BN-1-1 or 2BDE-5BN-5-2
    """
    parts = rsid.split("-")
    if len(parts) < 2:
        return None
    
    brigade = parts[0]
    battalion = parts[1]
    station = "-".join(parts[2:]) if len(parts) > 2 else None
    
    try:
        hierarchy = USAREC_HIERARCHY["USAREC"]["brigades"][brigade]
        battalion_info = hierarchy["battalions"][battalion]
        
        return {
            "command": "USAREC",
            "brigade": brigade,
            "brigade_name": hierarchy["name"],
            "battalion": battalion,
            "battalion_name": battalion_info["name"],
            "station": station,
            "full_path": f"USAREC > {hierarchy['name']} > {battalion_info['name']}" + (f" > Station {station}" if station else "")
        }
    except KeyError:
        return None

def validate_rsid(rsid):
    """Validate RSID format and existence in hierarchy"""
    path = get_full_hierarchy_path(rsid)
    return path is not None

def get_subordinate_rsids(rsid):
    """
    Get all subordinate RSIDs for a given level
    - Brigade RSID returns all battalions and stations
    - Battalion RSID returns all stations
    - Station RSID returns itself
    """
    if not rsid:
        return []
    
    parts = rsid.split("-")
    subordinates = []
    
    if len(parts) == 1:  # Brigade level (e.g., "1BDE")
        brigade = parts[0]
        battalions = get_battalions_for_brigade(brigade)
        for bn in battalions:
            subordinates.append(f"{brigade}-{bn}")
            stations = get_stations_for_battalion(brigade, bn)
            for stn in stations:
                subordinates.append(f"{brigade}-{bn}-{stn}")
    
    elif len(parts) == 2:  # Battalion level (e.g., "1BDE-1BN")
        brigade = parts[0]
        battalion = parts[1]
        stations = get_stations_for_battalion(brigade, battalion)
        for stn in stations:
            subordinates.append(f"{brigade}-{battalion}-{stn}")
    
    else:  # Station level - return itself
        subordinates.append(rsid)
    
    return subordinates
