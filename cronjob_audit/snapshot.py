"""Snapshot utilities: capture and restore ValidationResult collections for later comparison."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


class SnapshotError(Exception):
    """Raised when a snapshot cannot be saved or loaded."""


@dataclass
class Snapshot:
    label: str
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"label": self.label, "entries": self.entries}


def capture(label: str, results: list) -> Snapshot:
    """Serialise a list of ValidationResult-like objects into a Snapshot."""
    serialised = []
    for r in results:
        serialised.append(
            {
                "entry_id": r.entry.entry_id,
                "service": r.entry.service,
                "schedule": r.entry.schedule,
                "errors": list(r.errors),
                "warnings": list(r.warnings),
            }
        )
    return Snapshot(label=label, entries=serialised)


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Write a Snapshot to a JSON file."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snapshot.to_dict(), fh, indent=2)
    except OSError as exc:
        raise SnapshotError(f"Could not write snapshot to {path!r}: {exc}") from exc


def load_snapshot(path: str) -> Snapshot:
    """Read a Snapshot from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Could not load snapshot from {path!r}: {exc}") from exc

    if "label" not in data or "entries" not in data:
        raise SnapshotError("Snapshot file is missing required keys 'label' and 'entries'.")

    return Snapshot(label=data["label"], entries=data["entries"])
