#!/usr/bin/env python3
"""TEMPORARY diagnostic — dump the TryBooking Reporting API spec.

Downloads the published OpenAPI spec and prints every endpoint path, its HTTP
method, summary, and query parameters, plus the response schema field names.
Deleted once the client is wired to the correct endpoints.
"""

from __future__ import annotations

import json
import os
import requests

KEY = os.environ.get("TRYBOOKING_API_KEY", "")
SECRET = os.environ.get("TRYBOOKING_SECRET", "")
SPEC = "https://api.trybooking.com/swagger/v1/swagger.json"

spec = requests.get(SPEC, auth=(KEY, SECRET), timeout=20).json()

print("TITLE:", spec.get("info", {}).get("title"))
print("SERVERS:", spec.get("servers"))
print("\n=== PATHS ===")
for path, methods in spec.get("paths", {}).items():
    for method, op in methods.items():
        summary = op.get("summary", "")
        print(f"\n{method.upper()} {path}    {summary}")
        for p in op.get("parameters", []):
            req = "required" if p.get("required") else "optional"
            print(f"    param: {p.get('name')} ({p.get('in')}, {req}) - {p.get('description','')}")
        # Response content schema reference (200)
        resp = op.get("responses", {}).get("200", {})
        content = resp.get("content", {})
        for ctype, cval in content.items():
            ref = json.dumps(cval.get("schema", {}))[:200]
            print(f"    200 {ctype}: {ref}")

print("\n=== SCHEMAS (field names) ===")
for name, schema in spec.get("components", {}).get("schemas", {}).items():
    props = schema.get("properties", {})
    if props:
        fields = ", ".join(props.keys())
        print(f"\n{name}: {fields}")
