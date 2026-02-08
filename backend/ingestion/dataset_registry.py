"""
Dataset registry for ingestion classifier. Start with USAREC datasets.
"""
import re
from typing import List, Optional

def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

DATASETS = [
  {
    "key": "usarec_market_share_contracts",
    "source_system": "USAREC",
    "required_any": [
      {"zip", "zip code", "zipcode"},
      {"share", "market share"},
      {"contr", "contract", "contracts", "market contracts", "mkt contracts"},
    ],
    "optional": {"fy", "stn", "rsid", "bn", "bde", "co", "comp", "mkt"},
    "grain_hint": "zip+org+fy",
    "dashboards": ["DoD/Market Share", "USAREC Market Analysis"]
  },
  {
    "key": "usarec_zip_by_category",
    "source_system": "USAREC",
    "required_any": [
      {"zip", "zip code", "zipcode"},
      {"category", "cat"}
    ],
    "optional": {"stn","rsid","fy","value","count"},
    "grain_hint": "zip+category(+org)",
    "dashboards": ["G2 Segmentation", "Targeting Board"]
  }
  ,{
    "key": "usarec_vol_contracts_by_service",
    "source_system": "USAREC",
    "required_any": [
      {"ry", "fy", "year"},
      {"rq", "quarter", "qtr"},
      {"sum of contracts", "contracts", "contract", "contr"},
      {"service"}
    ],
    "optional": {"stn","rsid","bn","bde","co"},
    "grain_hint": "service+fy+rq",
    "dashboards": ["DoD/Market Share", "USAREC Volume by Service"]
  }
]

def classify(columns: List[str], source_system: str = 'USAREC') -> Optional[str]:
    colset = {norm(c) for c in columns}
    for ds in DATASETS:
        if ds["source_system"] != source_system:
            continue
        ok = True
        for group in ds["required_any"]:
            if not any(x in colset for x in group):
                ok = False
                break
        if ok:
            return ds["key"]
    return None
