from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
import os, json

router = APIRouter(prefix="/api/v2/tor", tags=["TOR"])

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATALOG_PATH = os.environ.get("TOR_METRICS_PATH") or os.path.join(ROOT, "backend", "config", "tor_metrics.yaml")


def _load_catalog() -> Dict[str, Any]:
    if not os.path.exists(CATALOG_PATH):
        return {"metrics": []}
    try:
        # import yaml lazily to avoid hard dependency at import time
        try:
            import yaml
        except Exception:
            yaml = None

        if yaml:
            with open(CATALOG_PATH, "r") as fh:
                data = yaml.safe_load(fh)
                return data or {"metrics": []}
        # fallback: try to load as json
        # Minimal YAML-ish parser fallback for simple metric lists
        def _simple_yaml_parse(path: str) -> Dict[str, Any]:
            items = []
            cur = None
            import ast
            with open(path, "r") as fh:
                for raw in fh:
                    line = raw.rstrip("\n")
                    stripped = line.lstrip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    # start of list item
                    if stripped.startswith("- ") and ":" in stripped:
                        # push previous
                        if cur:
                            items.append(cur)
                        cur = {}
                        keyval = stripped[2:]
                        if ":" in keyval:
                            k, v = keyval.split(":", 1)
                            cur[k.strip()] = _coerce_value(v.strip())
                    elif ":" in stripped and cur is not None:
                        k, v = stripped.split(":", 1)
                        cur[k.strip()] = _coerce_value(v.strip())
                    elif stripped.endswith(":"):
                        # key with nested list (not supported in fallback)
                        continue
                if cur:
                    items.append(cur)
            return {"metrics": items}

        def _coerce_value(s: str):
            # handle YAML-like lists in single line: ["a","b"] or [a, b]
            import ast
            if s.startswith("[") and s.endswith("]"):
                try:
                    return ast.literal_eval(s)
                except Exception:
                    # strip brackets and split
                    inner = s[1:-1]
                    return [x.strip().strip('"\'') for x in inner.split(",") if x.strip()]
            # numeric
            try:
                if s.isdigit():
                    return int(s)
                return float(s)
            except Exception:
                pass
            # unquote
            return s.strip().strip('"\'')

        try:
            return _simple_yaml_parse(CATALOG_PATH)
        except Exception:
            # last resort: try json
            with open(CATALOG_PATH, "r") as fh:
                return json.load(fh)
    except Exception:
        return {"metrics": []}


@router.get("/metrics")
def list_metrics() -> Dict[str, Any]:
    cat = _load_catalog()
    return {"items": cat.get("metrics", []), "count": len(cat.get("metrics", []))}


@router.get("/metrics/{metric_id}")
def metric_detail(metric_id: str) -> Dict[str, Any]:
    cat = _load_catalog()
    for m in cat.get("metrics", []):
        if m.get("metric_id") == metric_id:
            return m
    raise HTTPException(status_code=404, detail="Metric not found")
