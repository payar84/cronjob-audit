"""Tests for cronjob_audit.history."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from cronjob_audit.history import HistoryStore, load_history, HistoryError
from cronjob_audit.snapshot import Snapshot
from cronjob_audit.validator import ValidationResult


def _make_result(entry_id: str) -> ValidationResult:
    raw = MagicMock()
    raw.entry_id = entry_id
    raw.service = "svc"
    raw.schedule = "0 0 * * *"
    raw.command = "backup"
    return ValidationResult(raw=raw, errors=[], warnings=[])


def _make_snapshot(label: str) -> Snapshot:
    return Snapshot(label=label, results=[_make_result("job-1")], meta={})


class TestHistoryStore:
    def test_add_appends_snapshot(self, tmp_path):
        store = HistoryStore(directory=tmp_path)
        snap = _make_snapshot("v1")
        with patch("cronjob_audit.history.save_snapshot"):
            store.add(snap)
        assert len(store.snapshots) == 1

    def test_add_saves_to_disk(self, tmp_path):
        store = HistoryStore(directory=tmp_path)
        snap = _make_snapshot("v1")
        with patch("cronjob_audit.history.save_snapshot") as mock_save:
            store.add(snap)
        mock_save.assert_called_once()

    def test_replay_returns_track_report(self, tmp_path):
        store = HistoryStore(directory=tmp_path)
        store.snapshots = [_make_snapshot("v1"), _make_snapshot("v2")]
        report = store.replay()
        assert report.total == 2

    def test_replay_empty_store(self, tmp_path):
        store = HistoryStore(directory=tmp_path)
        report = store.replay()
        assert report.total == 0

    def test_to_dict_has_keys(self, tmp_path):
        store = HistoryStore(directory=tmp_path)
        d = store.to_dict()
        assert {"directory", "snapshot_count", "labels"} <= d.keys()

    def test_to_dict_labels_match_snapshots(self, tmp_path):
        store = HistoryStore(directory=tmp_path)
        store.snapshots = [_make_snapshot("a"), _make_snapshot("b")]
        assert store.to_dict()["labels"] == ["a", "b"]


class TestLoadHistory:
    def test_raises_for_missing_directory(self):
        with pytest.raises(HistoryError):
            load_history("/nonexistent/path/xyz")

    def test_returns_empty_store_for_empty_dir(self, tmp_path):
        store = load_history(tmp_path)
        assert isinstance(store, HistoryStore)
        assert len(store.snapshots) == 0

    def test_loads_snapshots_from_directory(self, tmp_path):
        snap = _make_snapshot("run-001")
        snap_file = tmp_path / "run-001.json"
        with patch("cronjob_audit.history.load_snapshot", return_value=snap):
            snap_file.write_text(json.dumps({}))
            store = load_history(tmp_path)
        assert len(store.snapshots) == 1

    def test_directory_preserved_in_store(self, tmp_path):
        store = load_history(tmp_path)
        assert store.directory == tmp_path
