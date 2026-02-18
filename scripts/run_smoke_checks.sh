#!/usr/bin/env bash
set -euo pipefail

# Automated smoke-check script for TAAIP
# Places output in /opt/TAAIP/logs/diag-<timestamp>.log

LOGDIR="/opt/TAAIP/logs"
mkdir -p "$LOGDIR"
TS=$(date +%Y%m%d_%H%M%S)
OUT="$LOGDIR/diag-$TS.log"

echo "TAAIP diagnostic run: $TS" | tee "$OUT"
echo "Host: $(hostname)" | tee -a "$OUT"
echo "User: $(whoami)" | tee -a "$OUT"
echo "--- Containers ---" | tee -a "$OUT"
# Prefer the local compose (v2) or fall back to docker-compose (v1)
DOCKER_COMPOSE_CMD=""
if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
  fi
fi

# If a compose file exists in /opt/TAAIP use it, else run plain ps
COMPOSE_FILE="/opt/TAAIP/docker-compose.yml"
if [ -n "$DOCKER_COMPOSE_CMD" ]; then
  if [ -f "$COMPOSE_FILE" ]; then
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" ps --all 2>&1 | tee -a "$OUT" || echo "$DOCKER_COMPOSE_CMD ps failed" | tee -a "$OUT"
  else
    $DOCKER_COMPOSE_CMD ps --all 2>&1 | tee -a "$OUT" || echo "$DOCKER_COMPOSE_CMD ps failed (no compose file in cwd)" | tee -a "$OUT"
  fi
else
  echo "docker/docker-compose not available on PATH" | tee -a "$OUT"
fi

echo "--- Backend health ---" | tee -a "$OUT"
curl -fsS http://127.0.0.1:8000/health 2>&1 | tee -a "$OUT" || echo "health check failed" | tee -a "$OUT"

echo "--- Git branch & recent commits ---" | tee -a "$OUT"
cd /opt/TAAIP || true
git rev-parse --abbrev-ref HEAD 2>&1 | tee -a "$OUT" || true
git log -3 --oneline 2>&1 | tee -a "$OUT" || true

DB=/opt/TAAIP/recruiting.db
echo "--- DB tables (first 200 chars) ---" | tee -a "$OUT"
if [ -f "$DB" ]; then
  sqlite3 "$DB" ".tables" 2>&1 | tee -a "$OUT"
  echo "--- Key table counts ---" | tee -a "$OUT"
  sqlite3 "$DB" "SELECT 'leads',COUNT(*) FROM leads;" 2>&1 | tee -a "$OUT" || true
  sqlite3 "$DB" "SELECT 'twg_review_boards',COUNT(*) FROM twg_review_boards;" 2>&1 | tee -a "$OUT" || true
  sqlite3 "$DB" "SELECT 'market_potential',COUNT(*) FROM market_potential;" 2>&1 | tee -a "$OUT" || true
  sqlite3 "$DB" "SELECT 'calendar_events',COUNT(*) FROM calendar_events;" 2>&1 | tee -a "$OUT" || true
else
  echo "DB not found at $DB" | tee -a "$OUT"
fi

echo "--- OpenAPI paths (trimmed) ---" | tee -a "$OUT"
if command -v jq >/dev/null 2>&1; then
  curl -fsS http://127.0.0.1:8000/openapi.json 2>/dev/null | jq '.paths | keys' 2>/dev/null | sed -n '1,200p' 2>&1 | tee -a "$OUT" || echo "openapi not reachable" | tee -a "$OUT"
else
  # jq not available — fetch raw openapi and print first lines
  curl -fsS http://127.0.0.1:8000/openapi.json 2>/dev/null | sed -n '1,200p' 2>&1 | tee -a "$OUT" || echo "openapi not reachable" | tee -a "$OUT"
fi

echo "--- Recent backend logs (tail 200) ---" | tee -a "$OUT"
if [ -n "$DOCKER_COMPOSE_CMD" ]; then
  if [ -f "$COMPOSE_FILE" ]; then
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" logs --no-color --tail 200 backend 2>&1 | tee -a "$OUT" || true
    echo "--- Recent frontend logs (tail 200) ---" | tee -a "$OUT"
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" logs --no-color --tail 200 frontend 2>&1 | tee -a "$OUT" || true
  else
    $DOCKER_COMPOSE_CMD logs --no-color --tail 200 backend 2>&1 | tee -a "$OUT" || true
    echo "--- Recent frontend logs (tail 200) ---" | tee -a "$OUT"
    $DOCKER_COMPOSE_CMD logs --no-color --tail 200 frontend 2>&1 | tee -a "$OUT" || true
  fi
else
  echo "Skipping compose logs — docker compose/docker-compose not available" | tee -a "$OUT"
fi

echo "--- System resources ---" | tee -a "$OUT"
free -h 2>&1 | tee -a "$OUT"
df -h / 2>&1 | tee -a "$OUT"
top -b -n 1 | head -n 20 2>&1 | tee -a "$OUT"

echo "--- Docker disk usage ---" | tee -a "$OUT"
docker system df 2>&1 | tee -a "$OUT" || true

echo "--- Diagnostic summary ---" | tee -a "$OUT"
echo "Log file: $OUT" | tee -a "$OUT"
echo "Diagnostic run complete: $(date)" | tee -a "$OUT"

echo
echo "Summary written to: $OUT"
echo "To upload or paste the log, run: sudo cat $OUT | sed -n '1,400p'"

exit 0
