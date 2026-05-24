"""Tests for cronjob_audit.exporter."""

from __future__ import annotations

import csv
import io
import pytest

from cronjob_audit.exporter import ExportError, export_csv, export_markdown
from cronjob_audit.validator import ValidationResult


def _make_result(service: str, schedule: str, status: str,
                 errors=None, warnings=None) -> ValidationResult:
    return ValidationResult(
        entry={"service": service, "schedule": schedule, "command": "echo hi"},
        status=status,
        errors=errors or [],
        warnings=warnings or [],
    )


@pytest.fixture()
def mixed_results():
    return [
        _make_result("svc-a", "0 * * * *", "ok"),
        _make_result("svc-b", "* * * * *", "warning", warnings=["Runs every minute"]),
        _make_result("svc-c", "99 * * * *", "error", errors=["Invalid hour field"]),
    ]


class TestExportCsv:
    def test_returns_string(self, mixed_results):
        result = export_csv(mixed_results)
        assert isinstance(result, str)

    def test_has_header_row(self, mixed_results):
        result = export_csv(mixed_results)
        reader = csv.DictReader(io.StringIO(result))
        assert set(reader.fieldnames) == {"service", "schedule", "command", "status", "errors", "warnings"}

    def test_row_count_matches_results(self, mixed_results):
        result = export_csv(mixed_results)
        rows = list(csv.DictReader(io.StringIO(result)))
        assert len(rows) == len(mixed_results)

    def test_error_row_contains_message(self, mixed_results):
        result = export_csv(mixed_results)
        rows = list(csv.DictReader(io.StringIO(result)))
        error_row = next(r for r in rows if r["status"] == "error")
        assert "Invalid hour field" in error_row["errors"]

    def test_raises_on_invalid_input(self):
        with pytest.raises(ExportError):
            export_csv("not-a-list")

    def test_empty_list_returns_header_only(self):
        result = export_csv([])
        rows = list(csv.DictReader(io.StringIO(result)))
        assert rows == []


class TestExportMarkdown:
    def test_returns_string(self, mixed_results):
        result = export_markdown(mixed_results)
        assert isinstance(result, str)

    def test_contains_table_header(self, mixed_results):
        result = export_markdown(mixed_results)
        assert "| Service |" in result

    def test_summary_counts_present(self, mixed_results):
        result = export_markdown(mixed_results)
        assert "**Total:** 3" in result
        assert "**OK:** 1" in result
        assert "**Warnings:** 1" in result
        assert "**Errors:** 1" in result

    def test_schedule_wrapped_in_backticks(self, mixed_results):
        result = export_markdown(mixed_results)
        assert "`0 * * * *`" in result

    def test_raises_on_invalid_input(self):
        with pytest.raises(ExportError):
            export_markdown(42)

    def test_empty_list_shows_zero_counts(self):
        result = export_markdown([])
        assert "**Total:** 0" in result
