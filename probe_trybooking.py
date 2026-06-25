#!/usr/bin/env python3
"""TEMPORARY diagnostic — discover the correct TryBooking API endpoint.

Runs in GitHub Actions (which can reach api.trybooking.com). It first tries to
download the API's own OpenAPI/Swagger spec, then probes a set of candidate
endpoints with the real Key/Secret and prints the HTTP status + a short snippet
of each response. No secrets are printed. Snippets are truncated so booking
data is not dumped into logs. This file and its workflow are deleted once the
correct path is known.
"""

from __future__ import annotations

import os
import requests

KEY = os.environ.get("TRYBOOKING_API_KEY", "")
SECRET = os.environ.get("TRYBOOKING_SECRET", "")
AUTH = (KEY, SECRET)
BASE = "https://api.trybooking.com"

print(f"Key present: {bool(KEY)}  Secret present: {bool(SECRET)}\n")

# 1) Try to grab a machine-readable spec that lists every real endpoint.
SPEC_URLS = [
    f"{BASE}/swagger/v1/swagger.json",
    f"{BASE}/swagger/index.html",
    f"{BASE}/openapi.json",
    f"{BASE}/api/swagger/v1/swagger.json",
    f"{BASE}/",
    f"{BASE}/api",
    f"{BASE}/api/v1",
]
print("=== SPEC / ROOT PROBES ===")
for url in SPEC_URLS:
    try:
        r = requests.get(url, auth=AUTH, timeout=20)
        body = r.text[:600].replace("\n", " ")
        print(f"[{r.status_code}] {url}\n    {body}\n")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] {url} -> {exc}\n")

# 2) Probe candidate data endpoints. Non-404 => the path likely exists.
CANDIDATES = [
    "/api/v1/events",
    "/api/v1/event",
    "/api/v1/bookings",
    "/api/v1/booking",
    "/api/v1/sessions",
    "/api/v1/account/events",
    "/api/v1/accounts/events",
    "/v1/events",
    "/v1/bookings",
    "/AU/api/v1/events",
    "/AU/api/v1/bookings",
    "/api/v1/Event",
    "/api/v1/Booking",
    "/api/Event",
    "/api/Booking",
]
print("=== ENDPOINT PROBES (status + snippet) ===")
for path in CANDIDATES:
    url = f"{BASE}{path}"
    try:
        r = requests.get(url, auth=AUTH, timeout=20)
        snippet = r.text[:200].replace("\n", " ")
        print(f"[{r.status_code}] {path}  ::  {snippet}")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] {path} -> {exc}")
