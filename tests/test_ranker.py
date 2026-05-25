"""Tests for cronjob_audit.ranker."""
from __future__ import annotations

from typing import List

import pytest

from cronjob_audit.validator import ValidationResult
from cronjob_audit.ranker import RankEntry, RankResult, rank


def _make_result(
    entry_id: str = "job-1",
    service: str = "svc",
    schedule: str = "0 * * * *",
    errors: List[str] | None = None,
    warnings: List[str] | None = None,
) -> ValidationResult:
    return ValidationResult(
        entry_id=entry_id,
        service=service,
        schedule=schedule,
        errors=errors or [],
        warnings=warnings or [],
    )


class TestRank:
    def test_returns_rank_result(self):
        result = rank([_make_result()])
        assert isinstance(result, RankResult)

    def test_empty_input_gives_empty_result(self):
        result = rank([])
        assert result.entries == []

    def test_single_entry_has_rank_one(self):
        result = rank([_make_result()])
        assert len(result.entries) == 1
        assert result.entries[0].rank == 1

    def test_rank_entry_fields_populated(self):
        vr = _make_result(entry_id="j1", service="alpha", schedule="0 0 * * *")
        result = rank([vr])
        entry = result.entries[0]
        assert entry.entry_id == "j1"
        assert entry.service == "alpha"
        assert entry.schedule == "0 0 * * *"
        assert isinstance(entry.score, float)
        assert entry.grade in {"A", "B", "C", "D", "F"}

    def test_healthiest_entry_ranked_first(self):
        good = _make_result(entry_id="good", errors=[], warnings=[])
        bad = _make_result(entry_id="bad", errors=["invalid field"], warnings=[])
        result = rank([bad, good])
        assert result.entries[0].entry_id == "good"
        assert result.entries[1].entry_id == "bad"

    def test_warning_lowers_rank_below_clean(self):
        clean = _make_result(entry_id="clean")
        warned = _make_result(entry_id="warned", warnings=["runs every minute"])
        result = rank([warned, clean])
        assert result.entries[0].entry_id == "clean"

    def test_ranks_are_sequential(self):
        results = [_make_result(entry_id=f"job-{i}") for i in range(5)]
        ranked = rank(results)
        ranks = [e.rank for e in ranked.entries]
        assert ranks == list(range(1, 6))

    def test_stable_sort_by_entry_id_on_tie(self):
        a = _make_result(entry_id="aaa")
        b = _make_result(entry_id="bbb")
        result = rank([b, a])
        assert result.entries[0].entry_id == "aaa"
        assert result.entries[1].entry_id == "bbb"

    def test_top_returns_n_entries(self):
        results = [_make_result(entry_id=f"j{i}") for i in range(10)]
        ranked = rank(results)
        assert len(ranked.top(3)) == 3
        assert ranked.top(3)[0].rank == 1

    def test_bottom_returns_n_entries(self):
        results = [_make_result(entry_id=f"j{i}") for i in range(10)]
        ranked = rank(results)
        assert len(ranked.bottom(3)) == 3
        assert ranked.bottom(3)[-1].rank == 10

    def test_to_dict_contains_entries_key(self):
        result = rank([_make_result()])
        d = result.to_dict()
        assert "entries" in d
        assert isinstance(d["entries"], list)

    def test_rank_entry_to_dict_keys(self):
        result = rank([_make_result()])
        d = result.entries[0].to_dict()
        for key in ("rank", "entry_id", "service", "schedule", "score", "grade", "errors", "warnings"):
            assert key in d
