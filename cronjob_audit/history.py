"""Persist and retrieve tracking history for cron audit sessions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from cronjob_audit.snapshot import Snapshot, save_snapshot, load_snapshot
from cronjob_audit.tracker import TrackReport, track


class HistoryError(Exception):
    """Raised when history operations fail."""


@dataclass
class HistoryStore:
    directory: Path
    snapshots: List[Snapshot] = field(default_factory=list)

    def add(self, snapshot: Snapshot) -> None:
        """Append a snapshot to the store and persist it."""
        self.snapshots.append(snapshot)
        dest = self.directory / f"{snapshot.label}.json"
        save_snapshot(snapshot, dest)

    def replay(self) -> TrackReport:
        """Produce a TrackReport across all stored snapshots in order."""
        return track(self.snapshots)

    def to_dict(self) -> dict:
        return {
            "directory": str(self.directory),
            "snapshot_count": len(self.snapshots),
            "labels": [s.label for s in self.snapshots],
        }


def load_history(directory: str | Path) -> HistoryStore:
    """Load all snapshots from *directory* sorted by filename."""
    path = Path(directory)
    if not path.is_dir():
        raise HistoryError(f"Directory not found: {path}")

    store = HistoryStore(directory=path)
    for snap_file in sorted(path.glob("*.json")):
        try:
            snap = load_snapshot(snap_file)
            store.snapshots.append(snap)
        except Exception as exc:  # pragma: no cover
            raise HistoryError(f"Failed to load {snap_file}: {exc}") from exc
    return store
