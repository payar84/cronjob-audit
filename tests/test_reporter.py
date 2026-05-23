"""Tests for cronjob_audit.reporter module."""

import io
import json
import pytest
from cronjob_audit.validator import validate_entry
from cronjob_audit.reporter import generate_json_report, generate_text_report


@pytest.fixture
def mixed_results():
    return [
        validate_entry("svc-a", "cleanup", "0 2 * * *"),
        validate_entry("svc-b", "broken", "99 * * * *"),
        validate_entry("svc-c", "frequent", "* * * * *"),
    ]


class TestJsonReport:
    def test_output_is_valid_json(self, mixed_results):
        buf = io.StringIO()
        generate_json_report(mixed_results, buf)
        data = json.loads(buf.getvalue())
        assert "summary" in data
        assert "entries" in data

    def test_summary_counts(self, mixed_results):
        buf = io.StringIO()
        generate_json_report(mixed_results, buf)
        summary = json.loads(buf.getvalue())["summary"]
        assert summary["total"] == 3
        assert summary["valid"] == 2
        assert summary["invalid"] == 1
        assert summary["with_warnings"] == 1

    def test_entries_count(self, mixed_results):
        buf = io.StringIO()
        generate_json_report(mixed_results, buf)
        entries = json.loads(buf.getvalue())["entries"]
        assert len(entries) == 3


class TestTextReport:
    def test_contains_header(self, mixed_results):
        buf = io.StringIO()
        generate_text_report(mixed_results, buf)
        assert "Cron Audit Report" in buf.getvalue()

    def test_fail_label_for_invalid(self, mixed_results):
        buf = io.StringIO()
        generate_text_report(mixed_results, buf)
        assert "[FAIL]" in buf.getvalue()

    def test_ok_label_for_valid(self, mixed_results):
        buf = io.StringIO()
        generate_text_report(mixed_results, buf)
        assert "[OK]" in buf.getvalue()

    def test_warning_shown(self, mixed_results):
        buf = io.StringIO()
        generate_text_report(mixed_results, buf)
        assert "WARN" in buf.getvalue()
