"""Tests for the report aggregation and rendering."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trybooking import report as report_mod  # noqa: E402


def _rows():
    # Two events, two days each. Reporting day = 2026-06-24.
    return [
        {"eventName": "Gala", "transactionDate": "2026-06-24T00:00:00", "totalSold": 30},
        {"eventName": "Gala", "transactionDate": "2026-06-23T00:00:00", "totalSold": 100},
        {"eventName": "Clinic", "transactionDate": "2026-06-23T00:00:00", "totalSold": 50},
        {"eventName": "Clinic", "transactionDate": "2026-06-24T00:00:00", "totalSold": 0},
        {"eventName": "Dormant", "transactionDate": "2026-06-01T00:00:00", "totalSold": 0},
    ]


def test_totals_and_increase():
    rep = report_mod.build_report(_rows(), "2026-06-24")
    by = {r.name: r for r in rep.rows}
    assert by["Gala"].total_sold == 130
    assert by["Gala"].increase == 30
    assert by["Clinic"].total_sold == 50
    assert by["Clinic"].increase == 0
    assert "Dormant" not in by  # zero cumulative is dropped
    assert rep.total_sold == 180
    assert rep.total_increase == 30
    assert rep.rows[0].name == "Gala"  # biggest increase first


def test_render_text_has_totals_and_delta():
    rep = report_mod.build_report(_rows(), "2026-06-24")
    text = report_mod.render_text(rep)
    assert "Gala" in text
    assert "+30" in text
    assert "TOTAL" in text
    assert "2026-06-24" in text


def test_render_html_escapes_names():
    rows = [{"eventName": "Quiz <Night> & Co", "transactionDate": "2026-06-24T00:00:00", "totalSold": 5}]
    rep = report_mod.build_report(rows, "2026-06-24")
    html = report_mod.render_html(rep)
    assert "&lt;Night&gt;" in html
    assert "&amp;" in html


def test_empty_rows():
    rep = report_mod.build_report([], "2026-06-24")
    assert rep.rows == []
    assert "No event sales found." in report_mod.render_text(rep)
    assert "No event sales found." in report_mod.render_html(rep)
