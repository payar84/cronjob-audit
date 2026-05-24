"""Group and aggregate validated cron entries by various dimensions."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronjob_audit.validator import ValidationResult


@dataclass
class Group:
    """A named collection of ValidationResult entries."""

    key: str
    entries: List[ValidationResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def valid_count(self) -> int:
        return sum(1 for e in self.entries if e.is_valid)

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.entries if e.warnings)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.entries if not e.is_valid)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "total": self.total,
            "valid": self.valid_count,
            "warnings": self.warning_count,
            "errors": self.error_count,
            "entries": [e.to_dict() for e in self.entries],
        }


def group_by_service(results: List[ValidationResult]) -> Dict[str, Group]:
    """Group results by the 'service' metadata field."""
    buckets: Dict[str, List[ValidationResult]] = defaultdict(list)
    for result in results:
        service = (result.entry.get("service") or "unknown") if result.entry else "unknown"
        buckets[service].append(result)
    return {key: Group(key=key, entries=entries) for key, entries in sorted(buckets.items())}


def group_by_status(results: List[ValidationResult]) -> Dict[str, Group]:
    """Group results into 'valid', 'warning', and 'error' buckets."""
    buckets: Dict[str, List[ValidationResult]] = defaultdict(list)
    for result in results:
        if not result.is_valid:
            buckets["error"].append(result)
        elif result.warnings:
            buckets["warning"].append(result)
        else:
            buckets["valid"].append(result)
    return {key: Group(key=key, entries=entries) for key, entries in sorted(buckets.items())}


def summarise_groups(groups: Dict[str, Group]) -> List[dict]:
    """Return a list of summary dicts for each group (without entry detail)."""
    return [
        {"key": g.key, "total": g.total, "valid": g.valid_count,
         "warnings": g.warning_count, "errors": g.error_count}
        for g in groups.values()
    ]
