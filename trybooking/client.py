"""TryBooking API client.

Authentication
--------------
TryBooking issues a "Key" and a "Secret Key" (see the Generate API key dialog).
The API uses HTTP Basic authentication:

    username = Key (TRYBOOKING_API_KEY)
    password = Secret Key (TRYBOOKING_SECRET)

i.e. an ``Authorization: Basic base64(key:secret)`` header, which ``requests``
builds for us via ``auth=(key, secret)``.

>>> VERIFY-AGAINST-DOCS <<<
The exact endpoint *paths* and *field names* are the only TryBooking-specific
details. They are all collected in the two clearly-marked blocks below so you
can confirm them against https://developer.trybooking.com/ and adjust in one
place. Everything downstream (aggregation, day-over-day diff, email) is generic
and does not care about the wire format.

The client's public contract is a single method:

    get_event_sales() -> dict[str, EventSales]

where the key is a stable event id and EventSales carries the event name plus
the total number of tickets sold to date.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

# ===========================================================================
# >>> VERIFY-AGAINST-DOCS: endpoint paths ==================================
# Relative to TRYBOOKING_API_BASE (default https://api.trybooking.com).
EVENTS_PATH = "/api/v1/events"        # GET -> list of events for the account
BOOKINGS_PATH = "/api/v1/bookings"    # GET -> bookings (used to sum tickets)
PAGE_SIZE = 200
# ===========================================================================

# ===========================================================================
# >>> VERIFY-AGAINST-DOCS: field names ====================================
# Candidate keys are tried in order; the first present one wins. This makes the
# parser tolerant of minor naming differences between API versions/regions.
EVENT_ID_KEYS = ("eventId", "id", "EventId", "event_id")
EVENT_NAME_KEYS = ("eventName", "name", "EventName", "title")
# A per-event "tickets sold" total, if the events endpoint already provides one.
EVENT_SOLD_KEYS = ("ticketsSold", "soldTickets", "quantitySold", "totalTickets")
# Booking-level fields (fallback path: sum ticket quantities per event).
BOOKING_EVENT_ID_KEYS = ("eventId", "EventId", "event_id")
BOOKING_QTY_KEYS = ("quantity", "ticketQuantity", "numberOfTickets", "tickets")
# ===========================================================================


@dataclass
class EventSales:
    event_id: str
    name: str
    tickets_sold: int


def _first(d: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


class TryBookingClient:
    def __init__(self, api_key: str, secret: str, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = (api_key, secret)
        self.session.headers.update({"Accept": "application/json"})

    # -- low-level ---------------------------------------------------------
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _as_list(payload: Any) -> list[dict[str, Any]]:
        """Normalise a response into a list of records.

        Handles both bare arrays and the common ``{"data": [...]}`` /
        ``{"results": [...]}`` envelope shapes.
        """
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "results", "items", "events", "bookings"):
                if isinstance(payload.get(key), list):
                    return payload[key]
        return []

    def _get_paginated(self, path: str, params: dict[str, Any] | None = None) -> list[dict]:
        records: list[dict] = []
        page = 1
        params = dict(params or {})
        while True:
            params.update({"page": page, "pageSize": PAGE_SIZE})
            batch = self._as_list(self._get(path, params))
            if not batch:
                break
            records.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
            page += 1
        return records

    # -- high-level --------------------------------------------------------
    def get_event_sales(self) -> dict[str, EventSales]:
        """Return ``{event_id: EventSales}`` with total tickets sold to date.

        Strategy: read the events list. If each event already reports a
        tickets-sold total, use it directly. Otherwise fall back to summing
        ticket quantities across all bookings grouped by event.
        """
        events = self._get_paginated(EVENTS_PATH)
        sales: dict[str, EventSales] = {}
        need_booking_fallback = False

        for ev in events:
            eid = _first(ev, EVENT_ID_KEYS)
            if eid is None:
                continue
            eid = str(eid)
            name = str(_first(ev, EVENT_NAME_KEYS, default=f"Event {eid}"))
            sold = _first(ev, EVENT_SOLD_KEYS)
            if sold is None:
                need_booking_fallback = True
                sales[eid] = EventSales(eid, name, 0)
            else:
                sales[eid] = EventSales(eid, name, int(sold))

        if need_booking_fallback:
            self._fill_from_bookings(sales)

        return sales

    def _fill_from_bookings(self, sales: dict[str, EventSales]) -> None:
        bookings = self._get_paginated(BOOKINGS_PATH)
        totals: dict[str, int] = {}
        for bk in bookings:
            eid = _first(bk, BOOKING_EVENT_ID_KEYS)
            if eid is None:
                continue
            eid = str(eid)
            qty = _first(bk, BOOKING_QTY_KEYS, default=1)
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 1
            totals[eid] = totals.get(eid, 0) + qty

        for eid, total in totals.items():
            if eid in sales:
                sales[eid].tickets_sold = total
            else:
                sales[eid] = EventSales(eid, f"Event {eid}", total)
