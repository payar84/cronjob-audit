"""Tests for cronjob_audit.snapshot."""

from __future__ import annotations

import json
import pathlib
from types import SimpleNamespace

import pytest

from cronjob_audit.snapshot import (
    Snapshot,
    SnapshotError,
    capture,
    load_snapshot,
    save_snapshot,
)


def _make_result(entry_id, service, schedule, errors=None, warnings=None):
    entry = SimpleNamespace(entry_id=entry_id, service=service, schedule=schedule)
    return SimpleNamespace(entry=entry, errors=errors or [], warnings=warnings or [])


@pytest.fixture()
def results():
    return [
        _make_result("j1", "svc-a", "0 * * * *"),
        _make_result("j2", "svc-b", "*/5 * * * *", warnings=["frequent"]),
    ]


class TestCapture:
    def test_returns_snapshot(self, results):
        snap = capture("v1", results)
        assert isinstance(snap, Snapshot)

    def test_label_preserved(self, results):
        snap = capture("release-2", results)
        assert snap.label == "release-2"

    def test_entry_count(self, results):
        snap = capture("v1", results)
        assert len(snap.entries) == 2

    def test_entry_fields(self, results):
        snap = capture("v1", results)
        e = snap.entries[0]
        assert e["entry_id"] == "j1"
        assert e["service"] == "svc-a"
        assert e["schedule"] == "0 * * * *"
        assert e["errors"] == []
        assert e["warnings"] == []

    def test_warnings_captured(self, results):
        snap = capture("v1", results)
        e = snap.entries[1]
        assert "frequent" in e["warnings"]

    def test_empty_results_gives_empty_snapshot(self):
        snap = capture("empty", [])
        assert snap.entries == []

    def test_to_dict_has_required_keys(self, results):
        snap = capture("v1", results)
        d = snap.to_dict()
        assert "label" in d
        assert "entries" in d


class TestSaveAndLoad:
    def test_round_trip(self, results, tmp_path):
        path = str(tmp_path / "snap.json")
        snap = capture("rt", results)
        save_snapshot(snap, path)
        loaded = load_snapshot(path)
        assert loaded.label == "rt"
        assert len(loaded.entries) == 2

    def test_file_is_valid_json(self, results, tmp_path):
        path = tmp_path / "snap.json"
        save_snapshot(capture("v", results), str(path))
        data = json.loads(path.read_text())
        assert data["label"] == "v"

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(SnapshotError):
            load_snapshot(str(tmp_path / "missing.json"))

    def test_load_invalid_json_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not-json")
        with pytest.raises(SnapshotError):
            load_snapshot(str(bad))

    def test_load_missing_keys_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"label": "x"}))
        with pytest.raises(SnapshotError, match="missing required keys"):
            load_snapshot(str(bad))
