#!/usr/bin/env python3
"""TEMPORARY diagnostic — confirm the Event Sales Report endpoint + auth.

Calls GET /AU/reporting/v1/sales/event for the last few days with datePeriod=1
(daily) and prints the HTTP status, row count, and the first row's structure so
we can confirm Basic auth works and see the field values. Deleted afterwards.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import requests

KEY = os.environ.get("TRYBOOKING_API_KEY", "")
SECRET = os.environ.get("TRYBOOKING_SECRET", "")
REGION = "AU"
BASE = "https://api.trybooking.com"

today = dt.date(2026, 6, 25)
from_date = (today - dt.timedelta(days=5)).isoformat()
to_date = today.isoformat()

url = f"{BASE}/{REGION}/reporting/v1/sales/event"
params = {"fromDate": from_date, "toDate": to_date, "datePeriod": 1}
r = requests.get(url, auth=(KEY, SECRET), params=params, timeout=30)
print(f"URL: {r.url}")
print(f"STATUS: {r.status_code}")
print(f"CONTENT-TYPE: {r.headers.get('content-type')}")
try:
    data = r.json()
    print(f"TYPE: {type(data).__name__}")
    if isinstance(data, list):
        print(f"ROW COUNT: {len(data)}")
        if data:
            print("FIRST ROW:", json.dumps(data[0], indent=2)[:500])
            print("ALL transactionDate+eventName+totalSold:")
            for row in data[:40]:
                print(f"  {row.get('transactionDate')}  sold={row.get('totalSold')}  {row.get('eventName')}")
    else:
        print("BODY:", json.dumps(data)[:500])
except Exception as exc:  # noqa: BLE001
    print("NON-JSON BODY:", r.text[:500], "ERR:", exc)
