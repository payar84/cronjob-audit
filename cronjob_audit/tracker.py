"""Track changes to cron entries over time using snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronjob_audit.snapshot import Snapshot
from cronjob_audit.comparator import CompareResult, compare


class TrackerError(Exception):
    """Raised when tracking operations fail."""


@dataclass
class TrackEntry:
    label: str
    snapshot: Snapshot
    compare_result: Optional[CompareResult] = None

    def to_dict(self) -> dict:
        d = {
            "label": self.label,
            "snapshot": self.snapshot.to_dict(),
        }
        if self.compare_result is not None:
            d["compare_result"] = self.compare_result.to_dict()
        return d


@dataclass
class TrackReport:
    entries: List[TrackEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def changed_count(self) -> int:
        return sum(
            1 for e in self.entries
            if e.compare_result is not None and e.compare_result.changed_count > 0
        )

    @property
    def unchanged_count(self) -> int:
        return self.total - self.changed_count

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "changed": self.changed_count,
            "unchanged": self.unchanged_count,
            "entries": [e.to_dict() for e in self.entries],
        }


def track(snapshots: List[Snapshot]) -> TrackReport:
    """Build a TrackReport by comparing consecutive snapshots."""
    if not snapshots:
        return TrackReport()

    entries: List[TrackEntry] = []
    prev: Optional[Snapshot] = None

    for snap in snapshots:
        if prev is None:
            entries.append(TrackEntry(label=snap.label, snapshot=snap))
        else:
            result = compare(prev.results, snap.results)
            entries.append(
                TrackEntry(label=snap.label, snapshot=snap, compare_result=result)
            )
        prev = snap

    return TrackReport(entries=entries)
