"""TryBooking Reporting API client.

Verified against the live OpenAPI spec at
https://api.trybooking.com/swagger/v1/swagger.json ("ReportingApi Documentation").

Authentication: HTTP Basic — the "Key" is the username, the "Secret Key" the
password (built by requests via ``auth=(key, secret)``).

The account's region is implicit in the host, so the path does NOT include a
region segment: GET https://api.trybooking.com/reporting/v1/sales/event
returns 200 JSON; including /AU/ in the path returns a 404. A region prefix is
left configurable for non-AU accounts but defaults to empty.

Event Sales Report response is a JSON array of:
    {eventName, transactionDate, totalBookings, totalSold, totalSales, trend}
With datePeriod=1 (Day) there is one row per event per day in the range.
"""

from __future__ import annotations

import datetime as _dt

import requests

SALES_EVENT_PATH = "/reporting/v1/sales/event"

# datePeriod values from the spec: 1=Day, 2=Week, 3=Month, 4=Year
DATE_PERIOD_DAY = 1

# The API rejects a single request spanning more than ~3 months
# ("Invalid date range."); 90 days works, 180 does not. Chunk below that.
MAX_CHUNK_DAYS = 80


class TryBookingClient:
    def __init__(self, api_key, secret, base_url="https://api.trybooking.com",
                 region_prefix="", timeout=30):
        self.base_url = base_url.rstrip("/")
        self.region_prefix = region_prefix.strip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = (api_key, secret)
        self.session.headers.update({"Accept": "application/json"})

    def event_sales(self, from_date: str, to_date: str, date_period: int = DATE_PERIOD_DAY) -> list[dict]:
        """Return the Event Sales Report rows for [from_date, to_date].

        Dates are ``yyyy-MM-dd``. Returns a list of EventSalesDto dicts; an empty
        list if the API returns no rows.
        """
        prefix = f"/{self.region_prefix}" if self.region_prefix else ""
        url = f"{self.base_url}{prefix}{SALES_EVENT_PATH}"
        params = {"fromDate": from_date, "toDate": to_date, "datePeriod": date_period}
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []

    def event_sales_range(self, from_date: str, to_date: str,
                          chunk_days: int = MAX_CHUNK_DAYS) -> list[dict]:
        """Like ``event_sales`` but split into API-sized chunks and concatenated.

        The Event Sales Report rejects spans wider than ~3 months, so a long
        history (e.g. 12 months) must be fetched in pieces.
        """
        start = _dt.date.fromisoformat(from_date)
        end = _dt.date.fromisoformat(to_date)
        rows: list[dict] = []
        cur = start
        while cur <= end:
            chunk_end = min(cur + _dt.timedelta(days=chunk_days), end)
            rows.extend(self.event_sales(cur.isoformat(), chunk_end.isoformat()))
            cur = chunk_end + _dt.timedelta(days=1)
        return rows
