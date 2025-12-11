#!/usr/bin/env bash
set -euo pipefail

# Simple API functional tests for TAAIP
# Usage: TOKEN=<admin_jwt_or_api_key> ./scripts/api_functional_tests.sh

BASE_URL="http://127.0.0.1:8000"
TOKEN="${TOKEN:-}"

echo "API functional test run: $(date)"
echo "Base URL: $BASE_URL"

echo "\n1) Health check"
curl -fsS "$BASE_URL/health" || { echo "health failed"; exit 2; }

echo "\n2) OpenAPI (first 200 lines)"
if command -v jq >/dev/null 2>&1; then
  curl -fsS "$BASE_URL/openapi.json" | jq '.paths | keys' | sed -n '1,200p' || echo "openapi fetch failed"
else
  curl -fsS "$BASE_URL/openapi.json" 2>/dev/null | sed -n '1,200p' || echo "openapi fetch failed"
fi

echo "\n3) Basic GET checks"
echo "- Leads (sample)"
curl -fsS "$BASE_URL/api/v2/data/leads?limit=3" || curl -fsS "$BASE_URL/api/v2/data/leads" || echo "leads endpoint not reachable"

echo "\n- TWG boards"
curl -fsS "$BASE_URL/api/v2/twg/boards" || echo "twg boards not reachable"

echo "\n4) Create user (requires admin token)"
if [ -z "$TOKEN" ]; then
  echo "SKIPPED: no TOKEN supplied. To run, set TOKEN env var to an admin JWT or API key. Example: TOKEN=ey... ./scripts/api_functional_tests.sh"
else
  echo "Posting sample user (won't be run if server rejects)"
  curl -s -o /tmp/api_create_user_resp.txt -w "HTTP_STATUS:%{http_code}\n" -X POST "$BASE_URL/api/v2/users" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"email":"test.user@example.mil","first_name":"Test","last_name":"User","rank":"CIV","tier":4,"start_date":"2025-12-01","end_date":"2026-12-01"}' || true
  sed -n '1,200p' /tmp/api_create_user_resp.txt || true
fi

echo "\n5) Funnel endpoints sanity"
curl -fsS "$BASE_URL/api/v2/funnel/stages" || echo "funnel stages not reachable"
curl -fsS "$BASE_URL/api/v2/funnel/metrics" || echo "funnel metrics not reachable"

echo "\nDone. If a create-user POST failed due to missing token or permissions, you can either provide an admin token or create a bootstrap admin user in the SQLite DB manually.\n"

echo "Manual DB bootstrap guidance (DO NOT run until you inspect schema):"
echo "  sqlite3 /opt/TAAIP/recruiting.db \"PRAGMA table_info(users);\""
echo "If columns exist for (id,email,first_name,last_name,tier,created_at) you can insert a row similar to:" \
     && echo "  sqlite3 /opt/TAAIP/recruiting.db \"INSERT INTO users (email,first_name,last_name,tier,created_at) VALUES ('admin@example.mil','Admin','User',4,datetime('now'));\""

exit 0
