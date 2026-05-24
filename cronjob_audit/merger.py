"""Merge multiple lists of ValidationResult into a single deduplicated collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from cronjob_audit.validator import ValidationResult


@dataclass
class MergeConflict:
    """Represents two entries with the same entry_id but different schedules."""

    entry_id: str
    schedules: List[str]
    services: List[str]

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "schedules": self.schedules,
            "services": self.services,
        }


@dataclass
class MergeResult:
    """Outcome of merging multiple ValidationResult collections."""

    entries: List[ValidationResult] = field(default_factory=list)
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def to_dict(self) -> dict:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "has_conflicts": self.has_conflicts,
        }


def merge(
    *collections: Iterable[ValidationResult],
    prefer_service: Optional[str] = None,
) -> MergeResult:
    """Merge one or more ValidationResult iterables.

    Entries are keyed by ``entry_id``.  When two entries share the same id but
    carry different cron schedules a :class:`MergeConflict` is recorded.  If
    *prefer_service* is given, that service's entry wins the conflict;
    otherwise the first-seen entry is kept.
    """
    seen: Dict[str, ValidationResult] = {}
    conflicts: List[MergeConflict] = []

    for collection in collections:
        for result in collection:
            eid = result.entry_id
            if eid not in seen:
                seen[eid] = result
                continue

            existing = seen[eid]
            existing_schedule = existing.expression.raw if existing.expression else ""
            new_schedule = result.expression.raw if result.expression else ""

            if existing_schedule == new_schedule:
                continue

            conflicts.append(
                MergeConflict(
                    entry_id=eid,
                    schedules=[existing_schedule, new_schedule],
                    services=[
                        existing.service or "",
                        result.service or "",
                    ],
                )
            )

            if prefer_service and result.service == prefer_service:
                seen[eid] = result

    return MergeResult(entries=list(seen.values()), conflicts=conflicts)
