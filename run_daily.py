#!/usr/bin/env python3
"""Daily TryBooking ticket-sales report → email to shop@ssfnc.com.au.

Run once a day from cron. On each run it:
  1. Pulls every event's tickets-sold total from the TryBooking API.
  2. Compares against yesterday's stored snapshot to get the daily increase.
  3. Emails a per-event table (sold + increase) to the configured recipient.
  4. Saves today's snapshot for tomorrow's comparison.

Usage:
  python run_daily.py            # fetch live data, email, save snapshot
  python run_daily.py --dry-run  # print the report, don't email or save
  python run_daily.py --mock     # use built-in sample data (no network/SMTP)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from trybooking import config, report as report_mod, state


def _mock_sales() -> dict:
    from trybooking.client import EventSales

    return {
        "101": EventSales("101", "Annual Gala Dinner", 184),
        "102": EventSales("102", "Junior Coaching Clinic", 56),
        "103": EventSales("103", "Quiz & Trivia Night", 92),
        "104": EventSales("104", "Season Launch", 240),
    }


def _fetch_live_sales() -> dict:
    from trybooking.client import TryBookingClient

    api = config.load_api_config()
    client = TryBookingClient(api.api_key, api.secret, api.base_url)
    return client.get_event_sales()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily TryBooking ticket-sales report")
    parser.add_argument("--dry-run", action="store_true", help="print instead of emailing/saving")
    parser.add_argument("--mock", action="store_true", help="use sample data, no network")
    args = parser.parse_args(argv)

    today = date.today().isoformat()

    try:
        current = _mock_sales() if args.mock else _fetch_live_sales()
    except Exception as exc:  # noqa: BLE001 - surface a clean message to cron logs
        print(f"ERROR fetching TryBooking data: {exc}", file=sys.stderr)
        return 1

    previous = state.load_previous()
    rep = report_mod.build_report(today, current, previous)

    text_body = report_mod.render_text(rep)
    html_body = report_mod.render_html(rep)
    subject = f"SSFNC ticket sales — {today} (total {rep.total_sold}, " + (
        f"+{rep.total_increase} since yesterday)" if rep.has_previous else "first run)"
    )

    if args.dry_run or args.mock:
        print(subject)
        print()
        print(text_body)
        # --mock / --dry-run never touch SMTP or the real snapshot state.
        return 0

    try:
        email_cfg = config.load_email_config()
        from trybooking.emailer import send_email

        send_email(email_cfg, subject, text_body, html_body)
        print(f"Sent report to {email_cfg.to_addr}")
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR sending email: {exc}", file=sys.stderr)
        return 1

    saved = state.save_snapshot(today, current)
    print(f"Saved snapshot: {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
