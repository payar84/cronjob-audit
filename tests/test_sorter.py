"""Tests for cronjob_audit.sorter."""

from __future__ import annotations

import pytest

from cronjob_audit.validator import ValidationResult
from cronjob_audit.annotator import AnnotatedEntry, annotate
from cronjob_audit.sorter import sort_results


def _make_result(
    service: str = "svc",
    schedule: str = "0 * * * *",
    entry_id: str = "job-1",
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> ValidationResult:
    return ValidationResult(
        entry={"service": service, "schedule": schedule, "id": entry_id},
        errors=errors or [],
        warnings=warnings or [],
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mixed_results() -> list[ValidationResult]:
    return [
        _make_result(service="zebra", schedule="0 12 * * *", entry_id="z1"),
        _make_result(service="alpha", schedule="* * * * *", entry_id="a1", warnings=["runs every minute"]),
        _make_result(service="alpha", schedule="0 0 * * *", entry_id="a2", errors=["invalid field"]),
        _make_result(service="mango", schedule="30 6 * * *", entry_id="m1"),
    ]


# ---------------------------------------------------------------------------
# sort by service
# ---------------------------------------------------------------------------

class TestSortByService:
    def test_ascending(self, mixed_results):
        out = sort_results(mixed_results, by="service")
        services = [r.entry["service"] for r in out]
        assert services == sorted(services)

    def test_descending(self, mixed_results):
        out = sort_results(mixed_results, by="service", reverse=True)
        services = [r.entry["service"] for r in out]
        assert services == sorted(services, reverse=True)


# ---------------------------------------------------------------------------
# sort by schedule
# ---------------------------------------------------------------------------

class TestSortBySchedule:
    def test_ascending(self, mixed_results):
        out = sort_results(mixed_results, by="schedule")
        schedules = [r.entry["schedule"] for r in out]
        assert schedules == sorted(schedules)


# ---------------------------------------------------------------------------
# sort by status
# ---------------------------------------------------------------------------

class TestSortByStatus:
    def test_errors_last(self, mixed_results):
        out = sort_results(mixed_results, by="status")
        # last entry should be the one with errors
        assert out[-1].errors != []

    def test_valid_first(self, mixed_results):
        out = sort_results(mixed_results, by="status")
        assert out[0].errors == [] and out[0].warnings == []


# ---------------------------------------------------------------------------
# sort by entry_id
# ---------------------------------------------------------------------------

class TestSortByEntryId:
    def test_ascending(self, mixed_results):
        out = sort_results(mixed_results, by="entry_id")
        ids = [r.entry["id"] for r in out]
        assert ids == sorted(ids)


# ---------------------------------------------------------------------------
# AnnotatedEntry passthrough
# ---------------------------------------------------------------------------

class TestAnnotatedEntrySupport:
    def test_accepts_annotated_entries(self, mixed_results):
        annotated = [annotate(r) for r in mixed_results]
        out = sort_results(annotated, by="service")
        services = [item.result.entry["service"] for item in out]
        assert services == sorted(services)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestInvalidKey:
    def test_raises_value_error(self, mixed_results):
        with pytest.raises(ValueError, match="Unknown sort key"):
            sort_results(mixed_results, by="nonexistent")  # type: ignore[arg-type]
