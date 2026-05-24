"""Tests for cronjob_audit.aggregator."""
from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from cronjob_audit.aggregator import aggregate, AggregateStats
from cronjob_audit.validator import ValidationResult


def _make_result(
    schedule: str = "0 * * * *",
    service: str = "svc",
    errors: List[str] | None = None,
    warnings: List[str] | None = None,
) -> ValidationResult:
    entry = SimpleNamespace(schedule=schedule, service=service)
    return ValidationResult(
        entry=entry,
        errors=errors or [],
        warnings=warnings or [],
    )


class TestAggregate:
    def test_returns_aggregate_stats(self):
        results = [_make_result()]
        stats = aggregate(results)
        assert isinstance(stats, AggregateStats)

    def test_total_count(self):
        results = [_make_result() for _ in range(4)]
        assert aggregate(results).total == 4

    def test_valid_count(self):
        results = [_make_result(), _make_result()]
        stats = aggregate(results)
        assert stats.valid == 2
        assert stats.errors == 0
        assert stats.warnings == 0

    def test_error_count(self):
        results = [_make_result(errors=["bad"]), _make_result()]
        stats = aggregate(results)
        assert stats.errors == 1
        assert stats.valid == 1

    def test_warning_count(self):
        results = [_make_result(warnings=["warn"]), _make_result()]
        stats = aggregate(results)
        assert stats.warnings == 1
        assert stats.valid == 1

    def test_by_service_counts(self):
        results = [
            _make_result(service="alpha"),
            _make_result(service="alpha"),
            _make_result(service="beta"),
        ]
        stats = aggregate(results)
        assert stats.by_service["alpha"] == 2
        assert stats.by_service["beta"] == 1

    def test_missing_service_falls_back_to_unknown(self):
        entry = SimpleNamespace(schedule="* * * * *", service=None)
        result = ValidationResult(entry=entry, errors=[], warnings=[])
        stats = aggregate([result])
        assert stats.by_service.get("unknown", 0) == 1

    def test_most_common_schedules(self):
        results = [
            _make_result(schedule="0 * * * *"),
            _make_result(schedule="0 * * * *"),
            _make_result(schedule="*/5 * * * *"),
        ]
        stats = aggregate(results)
        assert stats.most_common_schedules[0] == ("0 * * * *", 2)

    def test_top_n_limits_schedules(self):
        results = [_make_result(schedule=f"{i} * * * *") for i in range(10)]
        stats = aggregate(results, top_n=3)
        assert len(stats.most_common_schedules) <= 3

    def test_empty_results(self):
        stats = aggregate([])
        assert stats.total == 0
        assert stats.valid == 0
        assert stats.by_service == {}
        assert stats.most_common_schedules == []

    def test_to_dict_keys(self):
        stats = aggregate([_make_result()])
        d = stats.to_dict()
        assert set(d.keys()) == {
            "total", "valid", "warnings", "errors",
            "by_service", "most_common_schedules",
        }

    def test_to_dict_most_common_format(self):
        results = [_make_result(schedule="* * * * *")]
        d = aggregate(results).to_dict()
        assert d["most_common_schedules"][0] == {"schedule": "* * * * *", "count": 1}
