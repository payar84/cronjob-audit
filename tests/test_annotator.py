"""Tests for cronjob_audit.annotator."""
from __future__ import annotations

import pytest

from cronjob_audit.annotator import annotate, annotate_all, AnnotatedEntry
from cronjob_audit.validator import ValidationResult


def _make_result(
    schedule: str = "0 9 * * 1-5",
    service: str = "payments",
    is_valid: bool = True,
    errors: list | None = None,
    warnings: list | None = None,
) -> ValidationResult:
    return ValidationResult(
        entry={"schedule": schedule, "service": service, "command": "run.sh"},
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
    )


class TestAnnotate:
    def test_returns_annotated_entry(self):
        result = _make_result()
        annotated = annotate(result)
        assert isinstance(annotated, AnnotatedEntry)

    def test_description_is_string(self):
        result = _make_result(schedule="0 * * * *")
        annotated = annotate(result)
        assert isinstance(annotated.description, str)
        assert len(annotated.description) > 0

    def test_healthy_tag_for_valid_no_warnings(self):
        result = _make_result()
        annotated = annotate(result)
        assert "healthy" in annotated.tags

    def test_warning_tag_when_warnings_present(self):
        result = _make_result(warnings=["Runs every minute"])
        annotated = annotate(result)
        assert "warning" in annotated.tags
        assert "healthy" not in annotated.tags

    def test_invalid_tag_when_errors_present(self):
        result = _make_result(is_valid=False, errors=["Bad field"])
        annotated = annotate(result)
        assert "invalid" in annotated.tags

    def test_every_minute_tag(self):
        result = _make_result(schedule="* * * * *")
        annotated = annotate(result)
        assert "every-minute" in annotated.tags

    def test_daily_tag(self):
        result = _make_result(schedule="0 0 * * *")
        annotated = annotate(result)
        assert "daily" in annotated.tags

    def test_hourly_tag(self):
        result = _make_result(schedule="0 * * * *")
        annotated = annotate(result)
        assert "hourly" in annotated.tags

    def test_service_tag_included(self):
        result = _make_result(service="billing")
        annotated = annotate(result)
        assert "service:billing" in annotated.tags

    def test_note_is_none_for_healthy(self):
        result = _make_result()
        annotated = annotate(result)
        assert annotated.note is None

    def test_note_contains_errors(self):
        result = _make_result(is_valid=False, errors=["Invalid minute"])
        annotated = annotate(result)
        assert annotated.note is not None
        assert "Invalid minute" in annotated.note

    def test_note_contains_warnings(self):
        result = _make_result(warnings=["High frequency"])
        annotated = annotate(result)
        assert annotated.note is not None
        assert "High frequency" in annotated.note

    def test_to_dict_has_expected_keys(self):
        result = _make_result()
        annotated = annotate(result)
        d = annotated.to_dict()
        assert set(d.keys()) == {"entry", "description", "tags", "note"}

    def test_annotate_all_returns_list(self):
        results = [_make_result(), _make_result(schedule="* * * * *")]
        annotated = annotate_all(results)
        assert len(annotated) == 2
        assert all(isinstance(a, AnnotatedEntry) for a in annotated)
