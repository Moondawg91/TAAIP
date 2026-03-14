#!/usr/bin/env bash
set -euo pipefail

# Lightweight CI monitor for `ci.yml` workflow.
# - polls GitHub Actions every 5 minutes
# - on failed runs, saves logs and local pytest output, creates branch + PR with diagnostics

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT_DIR/.ci_monitor/logs"
PROCESSED_FILE="$ROOT_DIR/.ci_monitor/processed_runs.txt"
POLL_INTERVAL=${CI_MONITOR_INTERVAL:-300} # seconds

mkdir -p "$LOG_DIR"
touch "$PROCESSED_FILE"

echo "CI monitor starting (poll every $POLL_INTERVAL seconds)"

while true; do
  # list recent non-success runs
  mapfile -t failed_ids < <(gh run list --workflow=ci.yml --limit 10 --json id,conclusion --jq '.[] | select(.conclusion != "success") | .id') || true

  for runid in "${failed_ids[@]:-}"; do
    if grep -qx "$runid" "$PROCESSED_FILE"; then
      continue
    fi

    echo "Processing failed run: $runid"
    # save logs
    gh run view "$runid" --log > "$LOG_DIR/$runid.log" 2>&1 || true

    # attempt reproduce: run the CI's test files locally (best-effort)
    echo "Running local pytest reproduction..."
    (cd "$ROOT_DIR" && source .venv/bin/activate && python -m pytest -q services/api/app/tests/test_market_health_math.py services/api/app/tests/test_mission_allocation_market_health_integration.py services/api/app/tests/test_school_targeting_api.py services/api/app/tests/test_mission_risk.py services/api/app/tests/test_mission_risk_endpoints_and_integration.py services/api/app/tests/test_command_center_smoke.py) > "$LOG_DIR/$runid-pytest.log" 2>&1 || true

    # create diagnostic branch and PR
    BRANCH="fix/ci-$runid-diagnostics"
    git checkout -b "$BRANCH"
    mkdir -p ci_diagnostics
    cp "$LOG_DIR/$runid.log" "$ROOT_DIR/ci_diagnostics/$runid.log"
    cp "$LOG_DIR/$runid-pytest.log" "$ROOT_DIR/ci_diagnostics/$runid-pytest.log"
    git add ci_diagnostics/$runid.log ci_diagnostics/$runid-pytest.log
    git commit -m "ci: add diagnostics for failing CI run $runid" || true
    git push --set-upstream origin "$BRANCH" || true
    gh pr create --title "ci: diagnostics for failing run $runid" --body "Automated diagnostic PR: run $runid logs and local pytest output attached. Please review diagnostics and apply minimal fixes on this branch." || true

    echo "$runid" >> "$PROCESSED_FILE"
    # switch back to main
    git checkout -
  done

  sleep "$POLL_INTERVAL"
done
