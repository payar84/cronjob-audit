"""Tests for cronjob_audit.watchdog."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from cronjob_audit.watchdog import evaluate, WatchdogReport, WatchdogEntry


def _make_result(entry_id: str, schedule: str, service: str = "svc", errors=None):
    """Minimal ValidationResult-like object."""
    class _FakeResult:
        def __init__(self):
            self.entry = {"id": entry_id, "schedule": schedule, "service": service}
            self.errors = errors or []
            self.warnings = []
    return _FakeResult()


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestEvaluate:
    def test_returns_watchdog_report(self):
        report = evaluate([], {}, now=NOW)
        assert isinstance(report, WatchdogReport)

    def test_empty_input_gives_empty_report(self):
        report = evaluate([], {}, now=NOW)
        assert report.total == 0
        assert report.overdue_count == 0

    def test_never_ran_is_overdue(self):
        r = _make_result("job1", "0 * * * *")
        report = evaluate([r], {"job1": None}, now=NOW)
        assert report.never_ran_count == 1
        assert report.overdue_count == 1

    def test_recently_ran_not_overdue(self):
        r = _make_result("job1", "0 * * * *")
        last = NOW - timedelta(minutes=30)
        report = evaluate([r], {"job1": last}, now=NOW)
        assert report.overdue_count == 0

    def test_long_overdue_is_flagged(self):
        r = _make_result("job1", "0 * * * *")
        # last ran 3 hours ago; hourly job should have run twice since
        last = NOW - timedelta(hours=3)
        report = evaluate([r], {"job1": last}, now=NOW, grace_minutes=5.0)
        assert report.overdue_count == 1

    def test_entry_with_errors_is_skipped(self):
        r = _make_result("job1", "bad schedule", errors=["invalid"])
        report = evaluate([r], {"job1": None}, now=NOW)
        assert report.total == 0

    def test_checked_at_preserved(self):
        report = evaluate([], {}, now=NOW)
        assert report.checked_at == NOW

    def test_to_dict_contains_keys(self):
        r = _make_result("job1", "0 * * * *")
        last = NOW - timedelta(minutes=30)
        report = evaluate([r], {"job1": last}, now=NOW)
        d = report.to_dict()
        assert "checked_at" in d
        assert "total" in d
        assert "overdue_count" in d
        assert "never_ran_count" in d
        assert "entries" in d

    def test_entry_to_dict_shape(self):
        r = _make_result("job1", "0 * * * *")
        last = NOW - timedelta(minutes=30)
        report = evaluate([r], {"job1": last}, now=NOW)
        entry_dict = report.entries[0].to_dict()
        for key in ("entry_id", "service", "schedule", "last_run", "overdue", "minutes_overdue", "next_expected"):
            assert key in entry_dict

    def test_multiple_services(self):
        r1 = _make_result("j1", "0 * * * *", service="alpha")
        r2 = _make_result("j2", "0 0 * * *", service="beta")
        last_runs = {
            "j1": NOW - timedelta(minutes=20),
            "j2": NOW - timedelta(hours=25),
        }
        report = evaluate([r1, r2], last_runs, now=NOW, grace_minutes=5.0)
        assert report.total == 2
        overdue_ids = {e.entry_id for e in report.entries if e.overdue}
        assert "j2" in overdue_ids

    def test_missing_last_run_treated_as_never(self):
        r = _make_result("job99", "*/5 * * * *")
        # entry_id not in last_runs dict at all
        report = evaluate([r], {}, now=NOW)
        assert report.never_ran_count == 1
