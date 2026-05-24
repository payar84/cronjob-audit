"""Tests for cronjob_audit.differ."""

import pytest
from cronjob_audit.differ import diff_entries, DiffResult, DiffEntry


OLD_ENTRIES = [
    {"service": "billing", "name": "monthly_invoice", "schedule": "0 9 1 * *", "command": "invoice.sh"},
    {"service": "billing", "name": "daily_report", "schedule": "0 8 * * *", "command": "report.sh"},
    {"service": "infra", "name": "cleanup", "schedule": "30 3 * * 0", "command": "cleanup.sh"},
]

NEW_ENTRIES = [
    {"service": "billing", "name": "monthly_invoice", "schedule": "0 9 1 * *", "command": "invoice.sh"},
    {"service": "billing", "name": "daily_report", "schedule": "0 7 * * *", "command": "report.sh"},  # schedule changed
    {"service": "infra", "name": "backup", "schedule": "0 2 * * *", "command": "backup.sh"},  # new
    # cleanup removed
]


class TestDiffEntries:
    def test_returns_diff_result(self):
        result = diff_entries(OLD_ENTRIES, NEW_ENTRIES)
        assert isinstance(result, DiffResult)

    def test_detects_added_entry(self):
        result = diff_entries(OLD_ENTRIES, NEW_ENTRIES)
        assert len(result.added) == 1
        added = result.added[0]
        assert added.name == "backup"
        assert added.service == "infra"
        assert added.change_type == "added"
        assert added.new_schedule == "0 2 * * *"
        assert added.old_schedule is None

    def test_detects_removed_entry(self):
        result = diff_entries(OLD_ENTRIES, NEW_ENTRIES)
        assert len(result.removed) == 1
        removed = result.removed[0]
        assert removed.name == "cleanup"
        assert removed.change_type == "removed"
        assert removed.old_schedule == "30 3 * * 0"
        assert removed.new_schedule is None

    def test_detects_modified_schedule(self):
        result = diff_entries(OLD_ENTRIES, NEW_ENTRIES)
        assert len(result.modified) == 1
        mod = result.modified[0]
        assert mod.name == "daily_report"
        assert mod.change_type == "modified"
        assert mod.old_schedule == "0 8 * * *"
        assert mod.new_schedule == "0 7 * * *"

    def test_unchanged_entry_not_in_diff(self):
        result = diff_entries(OLD_ENTRIES, NEW_ENTRIES)
        names = [e.name for e in result.all_changes()]
        assert "monthly_invoice" not in names

    def test_has_changes_true_when_diffs_exist(self):
        result = diff_entries(OLD_ENTRIES, NEW_ENTRIES)
        assert result.has_changes is True

    def test_has_changes_false_when_identical(self):
        result = diff_entries(OLD_ENTRIES, OLD_ENTRIES)
        assert result.has_changes is False

    def test_empty_old_all_added(self):
        result = diff_entries([], NEW_ENTRIES)
        assert len(result.added) == len(NEW_ENTRIES)
        assert len(result.removed) == 0
        assert len(result.modified) == 0

    def test_empty_new_all_removed(self):
        result = diff_entries(OLD_ENTRIES, [])
        assert len(result.removed) == len(OLD_ENTRIES)
        assert len(result.added) == 0

    def test_to_dict_structure(self):
        result = diff_entries(OLD_ENTRIES, NEW_ENTRIES)
        d = result.to_dict()
        assert "added" in d
        assert "removed" in d
        assert "modified" in d
        assert d["summary"]["added"] == 1
        assert d["summary"]["removed"] == 1
        assert d["summary"]["modified"] == 1

    def test_command_change_detected(self):
        old = [{"service": "svc", "name": "job", "schedule": "* * * * *", "command": "old.sh"}]
        new = [{"service": "svc", "name": "job", "schedule": "* * * * *", "command": "new.sh"}]
        result = diff_entries(old, new)
        assert len(result.modified) == 1
        assert result.modified[0].old_command == "old.sh"
        assert result.modified[0].new_command == "new.sh"
