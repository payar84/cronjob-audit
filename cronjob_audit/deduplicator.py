"""Deduplicator: identify and remove duplicate cron entries across services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from cronjob_audit.validator import ValidationResult


@dataclass
class DeduplicateResult:
    """Outcome of a deduplication pass over a collection of validation results."""

    unique: List[ValidationResult]
    duplicates: List[Tuple[ValidationResult, ValidationResult]]

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)

    @property
    def unique_count(self) -> int:
        return len(self.unique)

    def to_dict(self) -> dict:
        return {
            "unique_count": self.unique_count,
            "duplicate_count": self.duplicate_count,
            "unique": [r.to_dict() for r in self.unique],
            "duplicates": [
                {"original": a.to_dict(), "duplicate": b.to_dict()}
                for a, b in self.duplicates
            ],
        }


def _entry_key(result: ValidationResult) -> Tuple[str, str]:
    """Return a normalised (service, schedule) key used to detect duplicates."""
    service = (result.entry.get("service") or "").strip().lower()
    schedule = (result.entry.get("schedule") or "").strip()
    return (service, schedule)


def deduplicate(
    results: Sequence[ValidationResult],
    *,
    cross_service: bool = False,
) -> DeduplicateResult:
    """Deduplicate *results* by (service, schedule) key.

    Parameters
    ----------
    results:
        Flat list of :class:`ValidationResult` objects to inspect.
    cross_service:
        When *True*, duplicates are detected regardless of service — only the
        schedule string is used as the key.  Defaults to *False*.
    """
    seen: Dict[Tuple, ValidationResult] = {}
    unique: List[ValidationResult] = []
    duplicates: List[Tuple[ValidationResult, ValidationResult]] = []

    for result in results:
        service, schedule = _entry_key(result)
        key: Tuple = (schedule,) if cross_service else (service, schedule)

        if key in seen:
            duplicates.append((seen[key], result))
        else:
            seen[key] = result
            unique.append(result)

    return DeduplicateResult(unique=unique, duplicates=duplicates)
