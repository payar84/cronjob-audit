"""Tests for cronjob_audit.tracker."""
import pytest
from unittest.mock import MagicMock
from cronjob_audit.tracker import track, TrackReport, TrackEntry, TrackerError
from cronjob_audit.snapshot import Snapshot
from cronjob_audit.validator import ValidationResult


def _make_result(entry_id: str, service: str = "svc", valid: bool = True) -> ValidationResult:
    raw = MagicMock()
    raw.entry_id = entry_id
    raw.service = service
    raw.schedule = "0 * * * *"
    raw.command = "echo hi"
    return ValidationResult(
        raw=raw,
        errors=[] if valid else ["bad field"],
        warnings=[],
    )


def _make_snapshot(label: str, entry_ids) -> Snapshot:
    results = [_make_result(eid) for eid in entry_ids]
    return Snapshot(label=label, results=results, meta={})


class TestTrack:
    def test_returns_track_report(self):
        snaps = [_make_snapshot("v1", ["a", "b"])]
        report = track(snaps)
        assert isinstance(report, TrackReport)

    def test_empty_input_gives_empty_report(self):
        report = track([])
        assert report.total == 0
        assert report.changed_count == 0
        assert report.unchanged_count == 0

    def test_single_snapshot_has_no_compare_result(self):
        snaps = [_make_snapshot("v1", ["a"])]
        report = track(snaps)
        assert report.entries[0].compare_result is None

    def test_two_snapshots_produces_compare_result(self):
        snaps = [
            _make_snapshot("v1", ["a", "b"]),
            _make_snapshot("v2", ["a", "b"]),
        ]
        report = track(snaps)
        assert report.entries[1].compare_result is not None

    def test_total_equals_snapshot_count(self):
        snaps = [_make_snapshot(f"v{i}", ["a"]) for i in range(4)]
        report = track(snaps)
        assert report.total == 4

    def test_unchanged_when_identical_snapshots(self):
        snaps = [
            _make_snapshot("v1", ["a", "b"]),
            _make_snapshot("v2", ["a", "b"]),
        ]
        report = track(snaps)
        assert report.changed_count == 0
        assert report.unchanged_count == report.total

    def test_changed_when_entry_added(self):
        snaps = [
            _make_snapshot("v1", ["a"]),
            _make_snapshot("v2", ["a", "b"]),
        ]
        report = track(snaps)
        assert report.changed_count >= 1

    def test_labels_preserved(self):
        snaps = [
            _make_snapshot("alpha", ["a"]),
            _make_snapshot("beta", ["a"]),
        ]
        report = track(snaps)
        labels = [e.label for e in report.entries]
        assert labels == ["alpha", "beta"]

    def test_to_dict_has_required_keys(self):
        snaps = [_make_snapshot("v1", ["a"])]
        report = track(snaps)
        d = report.to_dict()
        assert {"total", "changed", "unchanged", "entries"} <= d.keys()

    def test_entry_to_dict_without_compare(self):
        snaps = [_make_snapshot("v1", ["x"])]
        report = track(snaps)
        d = report.entries[0].to_dict()
        assert "compare_result" not in d
        assert d["label"] == "v1"

    def test_entry_to_dict_with_compare(self):
        snaps = [
            _make_snapshot("v1", ["x"]),
            _make_snapshot("v2", ["x"]),
        ]
        report = track(snaps)
        d = report.entries[1].to_dict()
        assert "compare_result" in d
