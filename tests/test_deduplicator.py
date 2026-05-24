"""Tests for cronjob_audit.deduplicator."""

from __future__ import annotations

import pytest

from cronjob_audit.deduplicator import DeduplicateResult, deduplicate
from cronjob_audit.validator import ValidationResult


def _make_result(
    schedule: str = "0 * * * *",
    service: str = "svc",
    errors: list | None = None,
    warnings: list | None = None,
) -> ValidationResult:
    entry = {"service": service, "schedule": schedule, "command": "echo hi"}
    return ValidationResult(
        entry=entry,
        errors=errors or [],
        warnings=warnings or [],
    )


# ---------------------------------------------------------------------------
# Basic return type
# ---------------------------------------------------------------------------

class TestDeduplicate:
    def test_returns_deduplicate_result(self):
        result = deduplicate([_make_result()])
        assert isinstance(result, DeduplicateResult)

    def test_empty_input_gives_empty_result(self):
        r = deduplicate([])
        assert r.unique_count == 0
        assert r.duplicate_count == 0

    def test_single_entry_is_unique(self):
        r = deduplicate([_make_result()])
        assert r.unique_count == 1
        assert r.duplicate_count == 0


# ---------------------------------------------------------------------------
# Same-service deduplication (default)
# ---------------------------------------------------------------------------

    def test_detects_duplicate_within_service(self):
        a = _make_result(schedule="0 9 * * *", service="billing")
        b = _make_result(schedule="0 9 * * *", service="billing")
        r = deduplicate([a, b])
        assert r.duplicate_count == 1
        assert r.unique_count == 1

    def test_same_schedule_different_service_not_duplicate(self):
        a = _make_result(schedule="0 9 * * *", service="billing")
        b = _make_result(schedule="0 9 * * *", service="reporting")
        r = deduplicate([a, b])
        assert r.duplicate_count == 0
        assert r.unique_count == 2

    def test_first_occurrence_kept_as_unique(self):
        a = _make_result(schedule="*/5 * * * *", service="svc")
        b = _make_result(schedule="*/5 * * * *", service="svc")
        r = deduplicate([a, b])
        assert r.unique[0] is a

    def test_duplicate_pair_references_original_and_duplicate(self):
        a = _make_result(schedule="*/5 * * * *", service="svc")
        b = _make_result(schedule="*/5 * * * *", service="svc")
        r = deduplicate([a, b])
        original, dup = r.duplicates[0]
        assert original is a
        assert dup is b


# ---------------------------------------------------------------------------
# Cross-service deduplication
# ---------------------------------------------------------------------------

    def test_cross_service_detects_duplicate_across_services(self):
        a = _make_result(schedule="0 0 * * *", service="alpha")
        b = _make_result(schedule="0 0 * * *", service="beta")
        r = deduplicate([a, b], cross_service=True)
        assert r.duplicate_count == 1

    def test_cross_service_false_does_not_flag_different_services(self):
        a = _make_result(schedule="0 0 * * *", service="alpha")
        b = _make_result(schedule="0 0 * * *", service="beta")
        r = deduplicate([a, b], cross_service=False)
        assert r.duplicate_count == 0


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

    def test_to_dict_contains_expected_keys(self):
        r = deduplicate([_make_result()])
        d = r.to_dict()
        assert set(d.keys()) == {"unique_count", "duplicate_count", "unique", "duplicates"}

    def test_to_dict_counts_match(self):
        a = _make_result(schedule="@daily", service="svc")
        b = _make_result(schedule="@daily", service="svc")
        r = deduplicate([a, b])
        d = r.to_dict()
        assert d["unique_count"] == 1
        assert d["duplicate_count"] == 1
