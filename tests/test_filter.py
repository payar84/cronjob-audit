"""Tests for cronjob_audit.filter."""
from __future__ import annotations

import pytest

from cronjob_audit.annotator import annotate, AnnotatedEntry
from cronjob_audit.filter import (
    by_tag,
    by_service,
    by_validity,
    has_warnings,
    by_predicate,
    search,
)
from cronjob_audit.validator import ValidationResult


def _make_annotated(
    schedule: str = "0 9 * * *",
    service: str = "svc",
    is_valid: bool = True,
    errors: list | None = None,
    warnings: list | None = None,
) -> AnnotatedEntry:
    vr = ValidationResult(
        entry={"schedule": schedule, "service": service, "command": "cmd"},
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
    )
    return annotate(vr)


@pytest.fixture()
def mixed() -> list[AnnotatedEntry]:
    return [
        _make_annotated(schedule="0 0 * * *", service="alpha"),
        _make_annotated(schedule="0 * * * *", service="beta"),
        _make_annotated(schedule="* * * * *", service="alpha", warnings=["High freq"]),
        _make_annotated(schedule="bad", service="gamma", is_valid=False, errors=["err"]),
    ]


class TestByTag:
    def test_filters_by_daily(self, mixed):
        result = by_tag(mixed, "daily")
        assert len(result) == 1
        assert result[0].result.entry["service"] == "alpha"

    def test_filters_by_invalid(self, mixed):
        result = by_tag(mixed, "invalid")
        assert len(result) == 1

    def test_no_match_returns_empty(self, mixed):
        assert by_tag(mixed, "nonexistent") == []


class TestByService:
    def test_returns_matching_service(self, mixed):
        result = by_service(mixed, "alpha")
        assert len(result) == 2

    def test_unknown_service_returns_empty(self, mixed):
        assert by_service(mixed, "unknown") == []


class TestByValidity:
    def test_valid_only(self, mixed):
        result = by_validity(mixed, valid=True)
        assert all(e.result.is_valid for e in result)

    def test_invalid_only(self, mixed):
        result = by_validity(mixed, valid=False)
        assert all(not e.result.is_valid for e in result)
        assert len(result) == 1


class TestHasWarnings:
    def test_returns_only_warned(self, mixed):
        result = has_warnings(mixed)
        assert len(result) == 1
        assert "warning" in result[0].tags


class TestByPredicate:
    def test_custom_predicate(self, mixed):
        result = by_predicate(mixed, lambda e: "hourly" in e.tags)
        assert len(result) == 1
        assert result[0].result.entry["service"] == "beta"


class TestSearch:
    def test_tag_and_service(self, mixed):
        result = search(mixed, tag="service:alpha", service="alpha")
        assert len(result) == 2

    def test_valid_true(self, mixed):
        result = search(mixed, valid=True)
        assert all(e.result.is_valid for e in result)

    def test_warnings_only(self, mixed):
        result = search(mixed, warnings_only=True)
        assert len(result) == 1

    def test_combined_service_and_valid(self, mixed):
        result = search(mixed, service="alpha", valid=True)
        assert len(result) == 2

    def test_no_criteria_returns_all(self, mixed):
        assert len(search(mixed)) == len(mixed)
