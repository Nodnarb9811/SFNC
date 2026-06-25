"""Build the daily report from TryBooking Event Sales Report rows.

For each event we compute:
  * total_sold  — tickets sold to date (sum of totalSold across the window)
  * increase    — tickets sold on the reporting day (yesterday) = the
                  day-over-day increase in the running total.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field


@dataclass
class EventRow:
    name: str
    total_sold: int
    increase: int


@dataclass
class Report:
    reporting_day: str
    rows: list = field(default_factory=list)

    @property
    def total_sold(self) -> int:
        return sum(r.total_sold for r in self.rows)

    @property
    def total_increase(self) -> int:
        return sum(r.increase for r in self.rows)


def build_report(rows: list[dict], reporting_day: str) -> Report:
    """Aggregate raw EventSalesDto rows into a Report.

    ``reporting_day`` is the yyyy-MM-dd whose sales count as the day's increase.
    """
    cumulative: dict[str, int] = {}
    on_day: dict[str, int] = {}
    order: list[str] = []

    for r in rows:
        name = (r.get("eventName") or "(unnamed event)").strip()
        date = (r.get("transactionDate") or "")[:10]
        try:
            sold = int(r.get("totalSold") or 0)
        except (TypeError, ValueError):
            sold = 0
        if name not in cumulative:
            cumulative[name] = 0
            on_day[name] = 0
            order.append(name)
        cumulative[name] += sold
        if date == reporting_day:
            on_day[name] += sold

    out = [EventRow(n, cumulative[n], on_day[n]) for n in order if cumulative[n] > 0]
    # Biggest increase first, then biggest total.
    out.sort(key=lambda e: (e.increase, e.total_sold), reverse=True)
    return Report(reporting_day=reporting_day, rows=out)


# --- rendering -------------------------------------------------------------

def _delta(n: int) -> str:
    return f"+{n}" if n > 0 else str(n)


def render_text(report: Report) -> str:
    lines = [
        f"Sorrento FNC — TryBooking ticket sales",
        f"New sales on {report.reporting_day}",
        "=" * 48,
        "",
    ]
    if not report.rows:
        lines.append("No event sales found.")
        return "\n".join(lines)

    name_w = max([len(r.name) for r in report.rows] + [len("Event")])
    header = f"{'Event'.ljust(name_w)}  {'Sold (12mo)':>12}  {'+/- day':>8}"
    lines.append(header)
    lines.append("-" * len(header))
    for r in report.rows:
        lines.append(f"{r.name.ljust(name_w)}  {r.total_sold:>12}  {_delta(r.increase):>8}")
    lines.append("-" * len(header))
    lines.append(f"{'TOTAL'.ljust(name_w)}  {report.total_sold:>12}  {_delta(report.total_increase):>8}")
    return "\n".join(lines)


def render_html(report: Report) -> str:
    def delta_cell(n: int) -> str:
        color = "#1a7f37" if n > 0 else ("#888" if n == 0 else "#b00")
        return f'<td style="text-align:right;padding:4px 10px;color:{color};font-weight:600">{_delta(n)}</td>'

    if not report.rows:
        body_rows = '<tr><td colspan="3" style="padding:8px 10px;color:#888">No event sales found.</td></tr>'
        foot = ""
    else:
        body_rows = "".join(
            "<tr>"
            f'<td style="padding:4px 10px">{html.escape(r.name)}</td>'
            f'<td style="text-align:right;padding:4px 10px">{r.total_sold}</td>'
            f"{delta_cell(r.increase)}"
            "</tr>"
            for r in report.rows
        )
        foot = (
            '<tr style="border-top:2px solid #0b3d63;font-weight:700">'
            '<td style="padding:6px 10px">TOTAL</td>'
            f'<td style="text-align:right;padding:6px 10px">{report.total_sold}</td>'
            f'<td style="text-align:right;padding:6px 10px">{_delta(report.total_increase)}</td>'
            "</tr>"
        )

    return f"""\
<html><body style="font-family:Arial,Helvetica,sans-serif;color:#222">
  <h2 style="margin-bottom:0">Sorrento FNC — TryBooking ticket sales</h2>
  <p style="margin-top:4px;color:#555">New sales on {report.reporting_day}</p>
  <table style="border-collapse:collapse;min-width:460px">
    <thead>
      <tr style="background:#0b3d63;color:#fff">
        <th style="text-align:left;padding:6px 10px">Event</th>
        <th style="text-align:right;padding:6px 10px">Tickets sold (last 12 months)</th>
        <th style="text-align:right;padding:6px 10px">+/- since previous day</th>
      </tr>
    </thead>
    <tbody>{body_rows}</tbody>
    <tfoot>{foot}</tfoot>
  </table>
</body></html>"""
