"""Tests for cronjob_audit.profiler."""
import pytest
from cronjob_audit.profiler import profile, ProfileReport, ProfileEntry, _runs_per_day, _pressure


def _make_result(schedule: str, entry_id: str = "job-1", service: str = "svc"):
    """Minimal ValidationResult-like object."""
    class _FakeResult:
        def __init__(self):
            self.entry = {"id": entry_id, "service": service, "schedule": schedule}
            self.errors = []
            self.warnings = []
    return _FakeResult()


class TestRunsPerDay:
    def test_every_minute(self):
        assert _runs_per_day("*", "*") == 1440.0

    def test_every_hour(self):
        assert _runs_per_day("0", "*") == 24.0

    def test_daily(self):
        assert _runs_per_day("0", "0") == 1.0

    def test_every_five_minutes(self):
        assert _runs_per_day("*/5", "*") == pytest.approx(288.0)

    def test_every_six_hours(self):
        assert _runs_per_day("0", "*/6") == pytest.approx(4.0)


class TestPressure:
    def test_low(self):
        assert _pressure(1.0) == "low"

    def test_medium(self):
        assert _pressure(48.0) == "medium"

    def test_high(self):
        assert _pressure(288.0) == "high"

    def test_critical(self):
        assert _pressure(1440.0) == "critical"


class TestProfile:
    def test_returns_profile_report(self):
        result = profile([_make_result("* * * * *")])
        assert isinstance(result, ProfileReport)

    def test_empty_input_gives_empty_report(self):
        report = profile([])
        assert report.total == 0
        assert report.critical_count == 0

    def test_every_minute_is_critical(self):
        report = profile([_make_result("* * * * *")])
        assert report.entries[0].pressure == "critical"
        assert report.critical_count == 1

    def test_daily_is_low(self):
        report = profile([_make_result("0 0 * * *")])
        assert report.entries[0].pressure == "low"

    def test_entry_id_preserved(self):
        report = profile([_make_result("0 * * * *", entry_id="abc")])
        assert report.entries[0].entry_id == "abc"

    def test_service_preserved(self):
        report = profile([_make_result("0 * * * *", service="billing")])
        assert report.entries[0].service == "billing"

    def test_schedule_preserved(self):
        report = profile([_make_result("*/15 * * * *")])
        assert report.entries[0].schedule == "*/15 * * * *"

    def test_runs_per_hour_derived_from_runs_per_day(self):
        report = profile([_make_result("0 * * * *")])
        entry = report.entries[0]
        assert entry.runs_per_hour == pytest.approx(entry.runs_per_day / 24, rel=1e-3)

    def test_invalid_schedule_skipped(self):
        report = profile([_make_result("not-a-cron")])
        assert report.total == 0

    def test_to_dict_structure(self):
        report = profile([_make_result("0 0 * * *")])
        d = report.to_dict()
        assert "total" in d
        assert "critical_count" in d
        assert "high_count" in d
        assert "entries" in d
        assert isinstance(d["entries"], list)

    def test_entry_to_dict_keys(self):
        report = profile([_make_result("0 0 * * *")])
        keys = report.entries[0].to_dict().keys()
        assert {"entry_id", "service", "schedule", "runs_per_day", "runs_per_hour", "pressure"} == set(keys)

    def test_multiple_entries(self):
        results = [
            _make_result("* * * * *", entry_id="a"),
            _make_result("0 0 * * *", entry_id="b"),
        ]
        report = profile(results)
        assert report.total == 2
        assert report.high_count + report.critical_count >= 1
