"""Persist daily snapshots of ticket sales so we can compute the increase.

A snapshot is a plain JSON map ``{event_id: {"name": str, "tickets_sold": int}}``.
We keep one file per day plus a ``latest.json`` pointer. The "increase from the
previous day" is simply this run's totals minus the most recent stored snapshot.
"""

from __future__ import annotations

import json
import os
from typing import Any

STATE_DIR = os.environ.get("STATE_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "state"))


def _ensure_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)


def _serialise(sales: dict[str, Any]) -> dict[str, dict]:
    # Accept either EventSales objects or already-plain dicts.
    out: dict[str, dict] = {}
    for eid, s in sales.items():
        if hasattr(s, "name"):
            out[eid] = {"name": s.name, "tickets_sold": int(s.tickets_sold)}
        else:
            out[eid] = {"name": s["name"], "tickets_sold": int(s["tickets_sold"])}
    return out


def load_previous() -> dict[str, dict] | None:
    """Return the most recent stored snapshot, or None if this is the first run."""
    path = os.path.join(STATE_DIR, "latest.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_snapshot(date_str: str, sales: dict[str, Any]) -> str:
    """Write today's snapshot and update the ``latest.json`` pointer."""
    _ensure_dir()
    data = _serialise(sales)
    dated = os.path.join(STATE_DIR, f"snapshot-{date_str}.json")
    latest = os.path.join(STATE_DIR, "latest.json")
    for path in (dated, latest):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
    return dated
