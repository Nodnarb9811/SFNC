"""Build the daily report: tickets sold per event + increase vs previous day."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any


@dataclass
class ReportRow:
    event_id: str
    name: str
    tickets_sold: int
    previous: int
    increase: int


@dataclass
class Report:
    date_str: str
    rows: list[ReportRow]
    has_previous: bool

    @property
    def total_sold(self) -> int:
        return sum(r.tickets_sold for r in self.rows)

    @property
    def total_increase(self) -> int:
        return sum(r.increase for r in self.rows)


def _to_plain(sales: dict[str, Any]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for eid, s in sales.items():
        if hasattr(s, "name"):
            out[eid] = {"name": s.name, "tickets_sold": int(s.tickets_sold)}
        else:
            out[eid] = {"name": s["name"], "tickets_sold": int(s["tickets_sold"])}
    return out


def build_report(date_str: str, current: dict[str, Any], previous: dict[str, dict] | None) -> Report:
    cur = _to_plain(current)
    prev = previous or {}
    has_previous = previous is not None

    rows: list[ReportRow] = []
    for eid, info in cur.items():
        prev_sold = int(prev.get(eid, {}).get("tickets_sold", 0))
        sold = int(info["tickets_sold"])
        rows.append(
            ReportRow(
                event_id=eid,
                name=info["name"],
                tickets_sold=sold,
                previous=prev_sold,
                increase=sold - prev_sold,
            )
        )

    # Biggest movers first, then by total sold.
    rows.sort(key=lambda r: (r.increase, r.tickets_sold), reverse=True)
    return Report(date_str=date_str, rows=rows, has_previous=has_previous)


# --- rendering -------------------------------------------------------------

def _fmt_delta(n: int, first_run: bool) -> str:
    if first_run:
        return "—"
    return f"+{n}" if n > 0 else str(n)


def render_text(report: Report) -> str:
    lines = [
        f"SSFNC — TryBooking ticket sales — {report.date_str}",
        "=" * 52,
        "",
    ]
    if not report.has_previous:
        lines.append("(First run — no previous day to compare against yet.)")
        lines.append("")

    name_w = max([len(r.name) for r in report.rows] + [len("Event")])
    header = f"{'Event'.ljust(name_w)}  {'Sold':>6}  {'+/- day':>8}"
    lines.append(header)
    lines.append("-" * len(header))
    for r in report.rows:
        lines.append(
            f"{r.name.ljust(name_w)}  {r.tickets_sold:>6}  "
            f"{_fmt_delta(r.increase, not report.has_previous):>8}"
        )
    lines.append("-" * len(header))
    lines.append(
        f"{'TOTAL'.ljust(name_w)}  {report.total_sold:>6}  "
        f"{_fmt_delta(report.total_increase, not report.has_previous):>8}"
    )
    if not report.rows:
        lines.append("(No events returned by the TryBooking API.)")
    return "\n".join(lines)


def render_html(report: Report) -> str:
    first = not report.has_previous

    def delta_cell(n: int) -> str:
        if first:
            return '<td style="text-align:right;color:#888">—</td>'
        color = "#1a7f37" if n > 0 else ("#888" if n == 0 else "#b00")
        text = f"+{n}" if n > 0 else str(n)
        return f'<td style="text-align:right;color:{color};font-weight:600">{text}</td>'

    rows_html = []
    for r in report.rows:
        rows_html.append(
            "<tr>"
            f'<td style="padding:4px 10px">{html.escape(r.name)}</td>'
            f'<td style="text-align:right;padding:4px 10px">{r.tickets_sold}</td>'
            f"{delta_cell(r.increase)}"
            "</tr>"
        )

    note = (
        '<p style="color:#888;font-size:13px">First run — no previous day to '
        "compare against yet.</p>"
        if first
        else ""
    )
    empty = (
        '<p style="color:#888">No events returned by the TryBooking API.</p>'
        if not report.rows
        else ""
    )

    return f"""\
<html><body style="font-family:Arial,Helvetica,sans-serif;color:#222">
  <h2 style="margin-bottom:0">SSFNC — TryBooking ticket sales</h2>
  <p style="margin-top:4px;color:#555">{report.date_str}</p>
  {note}
  <table style="border-collapse:collapse;min-width:420px">
    <thead>
      <tr style="background:#0b3d63;color:#fff">
        <th style="text-align:left;padding:6px 10px">Event</th>
        <th style="text-align:right;padding:6px 10px">Tickets sold</th>
        <th style="text-align:right;padding:6px 10px">+/- since yesterday</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
    <tfoot>
      <tr style="border-top:2px solid #0b3d63;font-weight:700">
        <td style="padding:6px 10px">TOTAL</td>
        <td style="text-align:right;padding:6px 10px">{report.total_sold}</td>
        <td style="text-align:right;padding:6px 10px">{
          '—' if first else ('+' + str(report.total_increase) if report.total_increase > 0 else str(report.total_increase))
        }</td>
      </tr>
    </tfoot>
  </table>
  {empty}
</body></html>"""
