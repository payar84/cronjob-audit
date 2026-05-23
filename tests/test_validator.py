"""Tests for cronjob_audit.validator module."""

import pytest
from cronjob_audit.validator import validate_entry, validate_all, ValidationResult


class TestValidateEntry:
    def test_valid_schedule(self):
        result = validate_entry("svc", "backup", "0 3 * * *")
        assert result.is_valid is True
        assert result.errors == []
        assert result.parsed is not None

    def test_invalid_schedule_returns_errors(self):
        result = validate_entry("svc", "bad", "99 * * * *")
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.parsed is None

    def test_every_minute_triggers_warning(self):
        result = validate_entry("svc", "poll", "* * * * *")
        assert result.is_valid is True
        assert any("every minute" in w.lower() for w in result.warnings)

    def test_step_every_minute_triggers_warning(self):
        result = validate_entry("svc", "poll", "*/1 * * * *")
        assert result.is_valid is True
        assert any("every minute" in w.lower() for w in result.warnings)

    def test_result_to_dict_keys(self):
        result = validate_entry("svc", "job", "0 0 * * 0")
        d = result.to_dict()
        assert set(d.keys()) == {"service", "name", "schedule", "is_valid", "errors", "warnings", "parsed"}

    def test_service_and_name_preserved(self):
        result = validate_entry("my-service", "daily-report", "0 6 * * 1-5")
        assert result.service == "my-service"
        assert result.name == "daily-report"


class TestValidateAll:
    def test_mixed_entries(self):
        entries = [
            {"service": "a", "name": "ok", "schedule": "0 1 * * *"},
            {"service": "b", "name": "bad", "schedule": "60 * * * *"},
        ]
        results = validate_all(entries)
        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False

    def test_empty_list(self):
        assert validate_all([]) == []

    def test_missing_keys_use_defaults(self):
        results = validate_all([{}])
        assert results[0].service == "unknown"
        assert results[0].name == "unnamed"
