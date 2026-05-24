"""Compare two sets of ValidationResults and produce a structured comparison report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronjob_audit.validator import ValidationResult


@dataclass
class CompareEntry:
    entry_id: str
    service: str
    schedule_before: Optional[str]
    schedule_after: Optional[str]
    status_before: Optional[str]
    status_after: Optional[str]
    changed: bool

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "service": self.service,
            "schedule_before": self.schedule_before,
            "schedule_after": self.schedule_after,
            "status_before": self.status_before,
            "status_after": self.status_after,
            "changed": self.changed,
        }


@dataclass
class CompareResult:
    entries: List[CompareEntry] = field(default_factory=list)

    @property
    def changed_count(self) -> int:
        return sum(1 for e in self.entries if e.changed)

    @property
    def unchanged_count(self) -> int:
        return len(self.entries) - self.changed_count

    def to_dict(self) -> dict:
        return {
            "total": len(self.entries),
            "changed": self.changed_count,
            "unchanged": self.unchanged_count,
            "entries": [e.to_dict() for e in self.entries],
        }


def _result_status(result: ValidationResult) -> str:
    if result.errors:
        return "error"
    if result.warnings:
        return "warning"
    return "valid"


def compare(
    before: List[ValidationResult],
    after: List[ValidationResult],
) -> CompareResult:
    """Compare two lists of ValidationResult by entry_id and return a CompareResult."""
    before_map: Dict[str, ValidationResult] = {r.entry.entry_id: r for r in before}
    after_map: Dict[str, ValidationResult] = {r.entry.entry_id: r for r in after}

    all_ids = sorted(set(before_map) | set(after_map))
    entries: List[CompareEntry] = []

    for entry_id in all_ids:
        b = before_map.get(entry_id)
        a = after_map.get(entry_id)

        sched_before = b.entry.schedule if b else None
        sched_after = a.entry.schedule if a else None
        status_before = _result_status(b) if b else None
        status_after = _result_status(a) if a else None
        service = (b or a).entry.service  # type: ignore[union-attr]

        changed = (sched_before != sched_after) or (status_before != status_after)

        entries.append(
            CompareEntry(
                entry_id=entry_id,
                service=service,
                schedule_before=sched_before,
                schedule_after=sched_after,
                status_before=status_before,
                status_after=status_after,
                changed=changed,
            )
        )

    return CompareResult(entries=entries)
