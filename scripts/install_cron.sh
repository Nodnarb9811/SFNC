#!/usr/bin/env bash
# Install a daily cron job that runs the TryBooking report at 07:00 local time.
# Usage:  bash scripts/install_cron.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
HOUR="${REPORT_HOUR:-7}"   # 24h local time; override with REPORT_HOUR=8 etc.

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

CRON_LINE="0 ${HOUR} * * * cd ${PROJECT_DIR} && ${PYTHON_BIN} run_daily.py >> ${PROJECT_DIR}/report.log 2>&1"

# Replace any existing line for this script, then append the fresh one.
( crontab -l 2>/dev/null | grep -v "run_daily.py" || true; echo "${CRON_LINE}" ) | crontab -

echo "Installed cron job:"
echo "  ${CRON_LINE}"
echo
echo "It runs daily at ${HOUR}:00 and appends output to ${PROJECT_DIR}/report.log"
