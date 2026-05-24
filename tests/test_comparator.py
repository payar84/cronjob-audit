"""Tests for cronjob_audit.comparator."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from cronjob_audit.comparator import compare, CompareResult, CompareEntry


def _make_result(entry_id: str, service: str, schedule: str, errors=None, warnings=None):
    entry = SimpleNamespace(entry_id=entry_id, service=service, schedule=schedule)
    return SimpleNamespace(entry=entry, errors=errors or [], warnings=warnings or [])


@pytest.fixture()
def before():
    return [
        _make_result("job-1", "svc-a", "0 * * * *"),
        _make_result("job-2", "svc-a", "*/5 * * * *"),
        _make_result("job-3", "svc-b", "0 0 * * *"),
    ]


@pytest.fixture()
def after():
    return [
        _make_result("job-1", "svc-a", "0 * * * *"),          # unchanged
        _make_result("job-2", "svc-a", "*/10 * * * *"),        # schedule changed
        _make_result("job-4", "svc-b", "0 12 * * 1-5"),        # new entry
    ]


class TestCompare:
    def test_returns_compare_result(self, before, after):
        result = compare(before, after)
        assert isinstance(result, CompareResult)

    def test_entries_cover_all_ids(self, before, after):
        result = compare(before, after)
        ids = {e.entry_id for e in result.entries}
        assert ids == {"job-1", "job-2", "job-3", "job-4"}

    def test_unchanged_entry_not_flagged(self, before, after):
        result = compare(before, after)
        job1 = next(e for e in result.entries if e.entry_id == "job-1")
        assert not job1.changed

    def test_modified_schedule_flagged(self, before, after):
        result = compare(before, after)
        job2 = next(e for e in result.entries if e.entry_id == "job-2")
        assert job2.changed
        assert job2.schedule_before == "*/5 * * * *"
        assert job2.schedule_after == "*/10 * * * *"

    def test_removed_entry_has_none_after(self, before, after):
        result = compare(before, after)
        job3 = next(e for e in result.entries if e.entry_id == "job-3")
        assert job3.schedule_after is None
        assert job3.status_after is None
        assert job3.changed

    def test_added_entry_has_none_before(self, before, after):
        result = compare(before, after)
        job4 = next(e for e in result.entries if e.entry_id == "job-4")
        assert job4.schedule_before is None
        assert job4.status_before is None
        assert job4.changed

    def test_changed_count(self, before, after):
        result = compare(before, after)
        assert result.changed_count == 3  # job-2 modified, job-3 removed, job-4 added

    def test_unchanged_count(self, before, after):
        result = compare(before, after)
        assert result.unchanged_count == 1  # job-1

    def test_status_reflects_errors(self):
        b = [_make_result("j", "s", "bad", errors=["e1"])]
        a = [_make_result("j", "s", "bad")]
        result = compare(b, a)
        entry = result.entries[0]
        assert entry.status_before == "error"
        assert entry.status_after == "valid"
        assert entry.changed

    def test_to_dict_structure(self, before, after):
        result = compare(before, after)
        d = result.to_dict()
        assert "total" in d
        assert "changed" in d
        assert "unchanged" in d
        assert "entries" in d
        assert isinstance(d["entries"], list)

    def test_empty_inputs_give_empty_result(self):
        result = compare([], [])
        assert result.entries == []
        assert result.changed_count == 0
