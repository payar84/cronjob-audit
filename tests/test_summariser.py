"""Tests for cronjob_audit.summariser."""
from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from cronjob_audit.summariser import summarise, Summary
from cronjob_audit.validator import ValidationResult


def _make_result(
    schedule: str = "0 * * * *",
    service: str = "svc",
    errors: List[str] | None = None,
    warnings: List[str] | None = None,
    tags: List[str] | None = None,
) -> ValidationResult:
    entry = SimpleNamespace(schedule=schedule, service=service)
    result = ValidationResult(
        entry=entry,
        errors=errors or [],
        warnings=warnings or [],
    )
    result.tags = tags or []
    return result


class TestSummarise:
    def test_returns_summary(self):
        assert isinstance(summarise([_make_result()]), Summary)

    def test_empty_input_gives_full_health(self):
        s = summarise([])
        assert s.health_ratio == 1.0

    def test_all_valid_health_ratio(self):
        results = [_make_result() for _ in range(3)]
        s = summarise(results)
        assert s.health_ratio == 1.0

    def test_partial_valid_health_ratio(self):
        results = [
            _make_result(),
            _make_result(errors=["bad"]),
        ]
        s = summarise(results)
        assert s.health_ratio == pytest.approx(0.5)

    def test_tag_counts_aggregated(self):
        results = [
            _make_result(tags=["daily", "healthy"]),
            _make_result(tags=["daily"]),
        ]
        s = summarise(results)
        assert s.tag_counts["daily"] == 2
        assert s.tag_counts["healthy"] == 1

    def test_no_tags_gives_empty_tag_counts(self):
        s = summarise([_make_result()])
        assert s.tag_counts == {}

    def test_stats_total_matches(self):
        results = [_make_result() for _ in range(5)]
        s = summarise(results)
        assert s.stats.total == 5

    def test_to_dict_structure(self):
        s = summarise([_make_result()])
        d = s.to_dict()
        assert "stats" in d
        assert "tag_counts" in d
        assert "health_ratio" in d

    def test_health_ratio_rounded(self):
        results = [_make_result()] * 3 + [_make_result(errors=["e"])] * 1
        s = summarise(results)
        assert s.to_dict()["health_ratio"] == round(3 / 4, 4)
