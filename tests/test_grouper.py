"""Tests for cronjob_audit.grouper."""

from __future__ import annotations

import pytest

from cronjob_audit.grouper import group_by_service, group_by_status, summarise_groups
from cronjob_audit.validator import ValidationResult


def _make_result(
    schedule: str = "0 * * * *",
    service: str = "svc-a",
    is_valid: bool = True,
    errors: list | None = None,
    warnings: list | None = None,
) -> ValidationResult:
    return ValidationResult(
        entry={"schedule": schedule, "service": service},
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
    )


# ---------------------------------------------------------------------------
# group_by_service
# ---------------------------------------------------------------------------

class TestGroupByService:
    def test_single_service(self):
        results = [_make_result(service="payments"), _make_result(service="payments")]
        groups = group_by_service(results)
        assert set(groups.keys()) == {"payments"}
        assert groups["payments"].total == 2

    def test_multiple_services(self):
        results = [
            _make_result(service="alpha"),
            _make_result(service="beta"),
            _make_result(service="alpha"),
        ]
        groups = group_by_service(results)
        assert groups["alpha"].total == 2
        assert groups["beta"].total == 1

    def test_missing_service_falls_back_to_unknown(self):
        result = ValidationResult(entry={"schedule": "* * * * *"}, is_valid=True, errors=[], warnings=[])
        groups = group_by_service([result])
        assert "unknown" in groups

    def test_group_counts_valid_and_errors(self):
        results = [
            _make_result(service="svc", is_valid=True),
            _make_result(service="svc", is_valid=False, errors=["bad field"]),
        ]
        g = group_by_service(results)["svc"]
        assert g.valid_count == 1
        assert g.error_count == 1


# ---------------------------------------------------------------------------
# group_by_status
# ---------------------------------------------------------------------------

class TestGroupByStatus:
    def test_valid_bucket(self):
        results = [_make_result(is_valid=True)]
        groups = group_by_status(results)
        assert "valid" in groups
        assert groups["valid"].total == 1

    def test_error_bucket(self):
        results = [_make_result(is_valid=False, errors=["oops"])]
        groups = group_by_status(results)
        assert "error" in groups
        assert "valid" not in groups

    def test_warning_bucket(self):
        results = [_make_result(is_valid=True, warnings=["runs every minute"])]
        groups = group_by_status(results)
        assert "warning" in groups

    def test_to_dict_includes_entries(self):
        results = [_make_result(is_valid=True)]
        groups = group_by_status(results)
        d = groups["valid"].to_dict()
        assert "entries" in d
        assert len(d["entries"]) == 1


# ---------------------------------------------------------------------------
# summarise_groups
# ---------------------------------------------------------------------------

def test_summarise_groups_omits_entry_detail():
    results = [_make_result(service="x"), _make_result(service="y")]
    groups = group_by_service(results)
    summary = summarise_groups(groups)
    assert len(summary) == 2
    for item in summary:
        assert "entries" not in item
        assert "key" in item
        assert "total" in item
