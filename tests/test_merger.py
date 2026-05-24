"""Tests for cronjob_audit.merger."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronjob_audit.merger import MergeConflict, MergeResult, merge
from cronjob_audit.validator import ValidationResult


def _make_result(
    entry_id: str,
    schedule: str = "0 * * * *",
    service: str = "svc",
    is_valid: bool = True,
) -> ValidationResult:
    expr = MagicMock()
    expr.raw = schedule
    return ValidationResult(
        entry_id=entry_id,
        service=service,
        expression=expr,
        is_valid=is_valid,
        errors=[],
        warnings=[],
    )


class TestMerge:
    def test_returns_merge_result(self):
        result = merge([])
        assert isinstance(result, MergeResult)

    def test_empty_collections_give_empty_result(self):
        result = merge([], [])
        assert result.entries == []
        assert result.conflicts == []

    def test_single_collection_preserved(self):
        entries = [_make_result("job-1"), _make_result("job-2")]
        result = merge(entries)
        assert len(result.entries) == 2

    def test_deduplicates_identical_entries(self):
        a = _make_result("job-1", schedule="0 * * * *")
        b = _make_result("job-1", schedule="0 * * * *")
        result = merge([a], [b])
        assert len(result.entries) == 1
        assert not result.has_conflicts

    def test_detects_schedule_conflict(self):
        a = _make_result("job-1", schedule="0 * * * *", service="alpha")
        b = _make_result("job-1", schedule="0 0 * * *", service="beta")
        result = merge([a], [b])
        assert result.has_conflicts
        assert len(result.conflicts) == 1
        conflict = result.conflicts[0]
        assert isinstance(conflict, MergeConflict)
        assert conflict.entry_id == "job-1"
        assert "0 * * * *" in conflict.schedules
        assert "0 0 * * *" in conflict.schedules

    def test_conflict_services_recorded(self):
        a = _make_result("job-1", service="alpha")
        b = _make_result("job-1", schedule="0 0 * * *", service="beta")
        result = merge([a], [b])
        conflict = result.conflicts[0]
        assert "alpha" in conflict.services
        assert "beta" in conflict.services

    def test_prefer_service_wins_conflict(self):
        a = _make_result("job-1", schedule="0 * * * *", service="alpha")
        b = _make_result("job-1", schedule="0 0 * * *", service="beta")
        result = merge([a], [b], prefer_service="beta")
        kept = next(e for e in result.entries if e.entry_id == "job-1")
        assert kept.expression.raw == "0 0 * * *"

    def test_first_seen_kept_without_prefer(self):
        a = _make_result("job-1", schedule="0 * * * *", service="alpha")
        b = _make_result("job-1", schedule="0 0 * * *", service="beta")
        result = merge([a], [b])
        kept = next(e for e in result.entries if e.entry_id == "job-1")
        assert kept.expression.raw == "0 * * * *"

    def test_to_dict_shape(self):
        a = _make_result("job-1")
        result = merge([a])
        d = result.to_dict()
        assert "entries" in d
        assert "conflicts" in d
        assert "has_conflicts" in d

    def test_conflict_to_dict(self):
        c = MergeConflict(entry_id="x", schedules=["a", "b"], services=["s1", "s2"])
        d = c.to_dict()
        assert d["entry_id"] == "x"
        assert d["schedules"] == ["a", "b"]
        assert d["services"] == ["s1", "s2"]

    def test_multiple_collections_merged(self):
        col1 = [_make_result("job-1"), _make_result("job-2")]
        col2 = [_make_result("job-3")]
        col3 = [_make_result("job-4")]
        result = merge(col1, col2, col3)
        assert len(result.entries) == 4
        assert not result.has_conflicts
