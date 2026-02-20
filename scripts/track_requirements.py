#!/usr/bin/env python3
"""
Simple requirements-to-code tracker for TAAIP.
Run: python3 scripts/track_requirements.py
Generates: reports/taaip_requirements_gap_report.md and .json
"""
import json
import os
import re
import sys
from glob import glob

try:
    import yaml
except Exception:
    print("PyYAML is required: pip install pyyaml")
    sys.exit(2)


ROOT = os.path.dirname(os.path.dirname(__file__))
SPEC_PATH = os.path.join(ROOT, "scripts", "requirements_spec.yaml")
REPORT_MD = os.path.join(ROOT, "reports", "taaip_requirements_gap_report.md")
REPORT_JSON = os.path.join(ROOT, "reports", "taaip_requirements_gap_report.json")


def read_spec():
    with open(SPEC_PATH, "r") as f:
        return yaml.safe_load(f)


def slurp(glob_pattern):
    path = os.path.join(ROOT, glob_pattern)
    files = glob(path, recursive=True)
    return files


def file_contains(path, pattern, flags=0):
    try:
        txt = open(path, "r", encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    return re.search(pattern, txt, flags) is not None


def check_backend_route(path):
    # Search routers for the literal path string.
    # Accept both the literal path and a form without a leading '/api' prefix
    search_variants = [path]
    if path.startswith('/api/'):
        search_variants.append(path[len('/api'):])
    files = glob(os.path.join(ROOT, "services", "api", "app", "routers", "**", "*.py"), recursive=True)
    for f in files:
        try:
            txt = open(f, "r", encoding="utf-8", errors="ignore").read()
            for sv in search_variants:
                if sv in txt:
                    return True, f
        except Exception:
            continue
        # Special-case: if path looks like '/api/<prefix>/<tail>' try to match
        # router prefix + decorator style endpoints in the same file (e.g. APIRouter(prefix="/budget") and @router.get('/dashboard'))
        try:
            if path.startswith('/api/'):
                rel = path[len('/api'):]
                parts = rel.split('/')
                if len(parts) >= 3:
                    prefix = '/' + parts[1]
                    tail = '/' + '/'.join(parts[2:])
                    # look for APIRouter prefix declaration and decorator
                    if (f'APIRouter(prefix="{prefix}"' in txt or f"APIRouter(prefix='{prefix}'" in txt) and (f"@router.get('{tail}'" in txt or f'@router.get("{tail}"' in txt or f"@router.post('{tail}'" in txt or f'@router.post("{tail}"' in txt):
                        return True, f
        except Exception:
            pass
    return False, None


def check_frontend_route(path):
    # Search common frontend entry points and page/component folders for the path.
    candidates = []
    candidates.append(os.path.join(ROOT, 'apps', 'web', 'src', 'App.js'))
    candidates.append(os.path.join(ROOT, 'apps', 'web', 'src', 'nav', 'navConfig.ts'))
    # include pages and components
    candidates.extend(glob(os.path.join(ROOT, 'apps', 'web', 'src', 'pages', '**', '*.*'), recursive=True))
    candidates.extend(glob(os.path.join(ROOT, 'apps', 'web', 'src', 'components', '**', '*.*'), recursive=True))
    for f in candidates:
        try:
            if os.path.exists(f) and path in open(f, 'r', encoding='utf-8', errors='ignore').read():
                return True, f
        except Exception:
            continue
    return False, None


def run_check(check):
    kind = check.get("kind")
    if kind == "backend_route":
        ok, where = check_backend_route(check.get("path"))
        return ok, where
    if kind == "frontend_route":
        ok, where = check_frontend_route(check.get("path"))
        return ok, where
    if kind == "file_glob":
        files = slurp(check.get("glob"))
        return bool(files), files[:3]
    if kind == "regex":
        files = glob(os.path.join(ROOT, check.get("glob")), recursive=True)
        patt = check.get("pattern")
        for f in files:
            if file_contains(f, patt):
                return True, f
        return False, None
    if kind == "forbidden_word":
        files = glob(os.path.join(ROOT, check.get("glob")), recursive=True)
        word = check.get("word")
        bad = []
        for f in files:
            # match as a whole word to avoid substrings like 'demographic'
            pattern = r"\\b" + re.escape(word) + r"\\b"
            if file_contains(f, pattern):
                bad.append(f)
        return (len(bad) == 0), bad[:5]
    if kind == "nav_path":
        # look in the navigation config for the path
        nc = os.path.join(ROOT, "apps", "web", "src", "nav", "navConfig.ts")
        try:
            if os.path.exists(nc) and check.get("path") in open(nc, "r", encoding="utf-8", errors="ignore").read():
                return True, nc
        except Exception:
            pass
        return False, None
    if kind == "nav_routes_match":
        # not implemented in detail; do a basic file existence check
        nav = os.path.join(ROOT, check.get("nav"))
        routes = os.path.join(ROOT, check.get("routes"))
        return os.path.exists(nav) and os.path.exists(routes), [nav, routes]
    return False, None


def main():
    spec = read_spec()
    out = {"summary": {}, "items": []}
    total = 0
    failures = 0
    for req in spec.get("requirements", []):
        total += 1
        item = {"id": req.get("id"), "title": req.get("title"), "checks": []}
        checks = req.get("checks", [])
        ok_all = True
        for c in checks:
            ok, where = run_check(c)
            item["checks"].append({"check": c, "ok": bool(ok), "where": where})
            if not ok:
                ok_all = False
        item["status"] = "OK" if ok_all else "MISSING"
        if not ok_all:
            failures += 1
        out["items"].append(item)

    out["summary"] = {"total": total, "missing": failures, "ok": total - failures}

    os.makedirs(os.path.dirname(REPORT_MD), exist_ok=True)
    # Write JSON
    with open(REPORT_JSON, "w") as f:
        json.dump(out, f, indent=2)

    # Write Markdown
    with open(REPORT_MD, "w") as f:
        f.write("# TAAIP Requirements Gap Report\n\n")
        f.write(f"Total requirements: {total}\n\n")
        f.write(f"Missing: {failures}\n\n")
        for item in out["items"]:
            f.write(f"## {item['id']} - {item['title']}\n\n")
            f.write(f"Status: **{item['status']}**\n\n")
            for ch in item["checks"]:
                ok = ch["ok"]
                where = ch["where"]
                f.write(f"- Check: {ch['check'].get('kind')} {ch['check'].get('path', ch['check'].get('glob', ch['check'].get('pattern', '')))} — {'OK' if ok else 'MISSING'}\n")
                if where:
                    f.write(f"  - Where: {where}\n")
            f.write("\n")

    print(f"Wrote {REPORT_MD} and {REPORT_JSON}")


if __name__ == '__main__':
    main()
