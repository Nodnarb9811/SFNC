#!/usr/bin/env python3
"""TEMPORARY diagnostic — resolve the exact server base, auth, and URL form."""

from __future__ import annotations

import datetime as dt
import json
import os
import requests

KEY = os.environ.get("TRYBOOKING_API_KEY", "")
SECRET = os.environ.get("TRYBOOKING_SECRET", "")
BASE = "https://api.trybooking.com"

spec = requests.get(f"{BASE}/swagger/v1/swagger.json", auth=(KEY, SECRET), timeout=20).json()
print("SERVERS:", json.dumps(spec.get("servers")))
print("SECURITY:", json.dumps(spec.get("security")))
print("SECURITY SCHEMES:", json.dumps(spec.get("components", {}).get("securitySchemes")))
# Show the sales/event operation's own servers (if path/op-level) and params
for path, methods in spec.get("paths", {}).items():
    if path.endswith("/sales/event"):
        print("PATH KEY:", path)
        print("PATH-LEVEL SERVERS:", json.dumps(methods.get("servers")))
        for m, op in methods.items():
            if isinstance(op, dict):
                print(f"OP {m} servers:", json.dumps(op.get("servers")))

today = dt.date(2026, 6, 25)
frm = (today - dt.timedelta(days=5)).isoformat()
to = today.isoformat()
qs = {"fromDate": frm, "toDate": to, "datePeriod": 1}

variants = [
    "/reporting/v1/sales/event",
    "/au/reporting/v1/sales/event",
    "/AU/reporting/v1/sales/event",
    "/v1/sales/event",
    "/api/reporting/v1/sales/event",
]
print("\n=== URL VARIANTS (status / content-type / snippet) ===")
for v in variants:
    try:
        r = requests.get(f"{BASE}{v}", auth=(KEY, SECRET), params=qs, timeout=25)
        ct = r.headers.get("content-type", "")
        snip = r.text[:160].replace("\n", " ")
        print(f"[{r.status_code}] {ct.split(';')[0]:24} {v}  ::  {snip}")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] {v} -> {exc}")
