"""Tests for the day-over-day diff and rendering — the logic that must be right."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trybooking import report as report_mod  # noqa: E402
from trybooking import state  # noqa: E402


def test_increase_vs_previous_day():
    previous = {
        "1": {"name": "Gala", "tickets_sold": 100},
        "2": {"name": "Clinic", "tickets_sold": 50},
    }
    current = {
        "1": {"name": "Gala", "tickets_sold": 130},   # +30
        "2": {"name": "Clinic", "tickets_sold": 50},  # +0
        "3": {"name": "New Event", "tickets_sold": 12},  # new -> +12
    }
    rep = report_mod.build_report("2026-06-25", current, previous)

    by_id = {r.event_id: r for r in rep.rows}
    assert by_id["1"].increase == 30
    assert by_id["2"].increase == 0
    assert by_id["3"].increase == 12
    assert rep.total_sold == 192
    assert rep.total_increase == 42
    assert rep.has_previous is True
    # Biggest mover sorts first.
    assert rep.rows[0].event_id == "1"


def test_first_run_has_no_previous():
    current = {"1": {"name": "Gala", "tickets_sold": 10}}
    rep = report_mod.build_report("2026-06-25", current, None)
    assert rep.has_previous is False
    assert rep.rows[0].increase == 10  # vs implicit zero
    assert "First run" in report_mod.render_text(rep)
    assert "—" in report_mod.render_html(rep)


def test_render_text_and_html_contain_totals():
    current = {"1": {"name": "Gala", "tickets_sold": 130}}
    previous = {"1": {"name": "Gala", "tickets_sold": 100}}
    rep = report_mod.build_report("2026-06-25", current, previous)
    text = report_mod.render_text(rep)
    html = report_mod.render_html(rep)
    assert "Gala" in text and "Gala" in html
    assert "+30" in text and "+30" in html
    assert "TOTAL" in text and "TOTAL" in html


def test_snapshot_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "STATE_DIR", str(tmp_path))
    assert state.load_previous() is None
    state.save_snapshot("2026-06-24", {"1": {"name": "Gala", "tickets_sold": 7}})
    loaded = state.load_previous()
    assert loaded == {"1": {"name": "Gala", "tickets_sold": 7}}


def test_html_escapes_event_names():
    current = {"1": {"name": "Quiz <Night> & Co", "tickets_sold": 5}}
    rep = report_mod.build_report("2026-06-25", current, None)
    html = report_mod.render_html(rep)
    assert "&lt;Night&gt;" in html
    assert "&amp;" in html
