"""Annotate cron entries with human-readable descriptions and metadata tags."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronjob_audit.scheduler import describe
from cronjob_audit.validator import ValidationResult


@dataclass
class AnnotatedEntry:
    """A validation result enriched with human-readable annotations."""

    result: ValidationResult
    description: str
    tags: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "entry": self.result.to_dict(),
            "description": self.description,
            "tags": self.tags,
            "note": self.note,
        }


def _derive_tags(result: ValidationResult) -> List[str]:
    """Derive searchable tags from a validation result."""
    tags: List[str] = []

    if result.is_valid and not result.warnings:
        tags.append("healthy")
    if result.warnings:
        tags.append("warning")
    if not result.is_valid:
        tags.append("invalid")

    schedule = result.entry.get("schedule", "")
    if schedule == "* * * * *":
        tags.append("every-minute")
    if schedule.startswith("0 0"):
        tags.append("daily")
    if schedule.startswith("0 * "):
        tags.append("hourly")

    service = result.entry.get("service")
    if service:
        tags.append(f"service:{service}")

    return tags


def annotate(result: ValidationResult) -> AnnotatedEntry:
    """Annotate a single ValidationResult."""
    schedule = result.entry.get("schedule", "")
    try:
        description = describe(schedule)
    except Exception:
        description = "Unable to describe schedule"

    tags = _derive_tags(result)

    note: Optional[str] = None
    if not result.is_valid:
        note = "Validation failed: " + "; ".join(result.errors)
    elif result.warnings:
        note = "Warnings: " + "; ".join(result.warnings)

    return AnnotatedEntry(result=result, description=description, tags=tags, note=note)


def annotate_all(results: List[ValidationResult]) -> List[AnnotatedEntry]:
    """Annotate a list of ValidationResults."""
    return [annotate(r) for r in results]
