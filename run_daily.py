#!/usr/bin/env python3
"""Daily TryBooking ticket-sales report -> email to shop@ssfnc.com.au.

Runs once a day. It pulls the TryBooking Event Sales Report, computes each
event's tickets sold to date and how many sold on the previous day (the
day-over-day increase), and emails a per-event table.

Usage:
  python run_daily.py            # fetch live data and email the report
  python run_daily.py --dry-run  # fetch live data, print the report, no email
  python run_daily.py --mock     # use sample data, no network, no email
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from trybooking import config, report as report_mod

# Default to Sorrento FNC's timezone (Victoria, AU). Override with REPORT_TIMEZONE.
TIMEZONE = os.environ.get("REPORT_TIMEZONE", "Australia/Melbourne")
# How far back to sum for the "tickets sold" total (fetched in API-sized
# chunks). Defaults to the last 12 months.
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "365"))


def _reporting_dates():
    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    reporting_day = (today - timedelta(days=1)).isoformat()  # yesterday, last complete day
    from_date = (today - timedelta(days=LOOKBACK_DAYS)).isoformat()
    to_date = today.isoformat()
    return reporting_day, from_date, to_date


def _mock_rows(reporting_day: str) -> list[dict]:
    prev = (datetime.fromisoformat(reporting_day) - timedelta(days=1)).date().isoformat()
    return [
        {"eventName": "Red & White Night", "transactionDate": f"{reporting_day}T00:00:00", "totalSold": 18},
        {"eventName": "Red & White Night", "transactionDate": f"{prev}T00:00:00", "totalSold": 160},
        {"eventName": "Season Launch", "transactionDate": f"{reporting_day}T00:00:00", "totalSold": 12},
        {"eventName": "Season Launch", "transactionDate": f"{prev}T00:00:00", "totalSold": 228},
        {"eventName": "Junior Presentation", "transactionDate": f"{prev}T00:00:00", "totalSold": 56},
    ]


def _fetch_rows(from_date: str, to_date: str) -> list[dict]:
    from trybooking.client import TryBookingClient

    api = config.load_api_config()
    client = TryBookingClient(api.api_key, api.secret, api.base_url)
    return client.event_sales_range(from_date, to_date)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily TryBooking ticket-sales report")
    parser.add_argument("--dry-run", action="store_true", help="fetch live data, print, don't email")
    parser.add_argument("--mock", action="store_true", help="use sample data, no network/email")
    args = parser.parse_args(argv)

    reporting_day, from_date, to_date = _reporting_dates()

    try:
        rows = _mock_rows(reporting_day) if args.mock else _fetch_rows(from_date, to_date)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR fetching TryBooking data: {exc}", file=sys.stderr)
        return 1

    report = report_mod.build_report(rows, reporting_day)
    text_body = report_mod.render_text(report)
    html_body = report_mod.render_html(report)
    subject = (
        f"Sorrento FNC ticket sales — {reporting_day} "
        f"(+{report.total_increase} sold that day)"
    )

    if args.dry_run or args.mock:
        print(subject)
        print()
        print(text_body)
        return 0

    try:
        email_cfg = config.load_email_config()
        from trybooking.emailer import send_email

        send_email(email_cfg, subject, text_body, html_body)
        print(f"Sent report to {email_cfg.to_addr}")
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR sending email: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
