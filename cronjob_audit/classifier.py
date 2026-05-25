"""Classify cron entries into frequency buckets based on their schedule."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .validator import ValidationResult


FREQUENCY_LABELS = (
    "minutely",
    "hourly",
    "daily",
    "weekly",
    "monthly",
    "yearly",
    "custom",
)


@dataclass
class ClassifiedEntry:
    result: ValidationResult
    frequency: str
    confidence: str  # 'exact' | 'inferred' | 'unknown'

    def to_dict(self) -> dict:
        return {
            "entry": self.result.entry,
            "schedule": self.result.schedule,
            "frequency": self.frequency,
            "confidence": self.confidence,
        }


def _classify_schedule(schedule: str) -> tuple[str, str]:
    """Return (frequency_label, confidence) for a cron schedule string."""
    aliases = {
        "@yearly": ("yearly", "exact"),
        "@annually": ("yearly", "exact"),
        "@monthly": ("monthly", "exact"),
        "@weekly": ("weekly", "exact"),
        "@daily": ("daily", "exact"),
        "@midnight": ("daily", "exact"),
        "@hourly": ("hourly", "exact"),
    }
    if schedule in aliases:
        return aliases[schedule]

    parts = schedule.split()
    if len(parts) != 5:
        return ("custom", "unknown")

    minute, hour, dom, month, dow = parts

    if minute == "*" and hour == "*" and dom == "*" and month == "*" and dow == "*":
        return ("minutely", "exact")
    if minute != "*" and hour == "*" and dom == "*" and month == "*" and dow == "*":
        return ("hourly", "exact")
    if minute != "*" and hour != "*" and dom == "*" and month == "*" and dow == "*":
        return ("daily", "exact")
    if minute != "*" and hour != "*" and dom == "*" and month == "*" and dow != "*":
        return ("weekly", "exact")
    if minute != "*" and hour != "*" and dom != "*" and month == "*" and dow == "*":
        return ("monthly", "exact")
    if minute != "*" and hour != "*" and dom != "*" and month != "*" and dow == "*":
        return ("yearly", "exact")

    if "/" in minute or "/" in hour:
        return ("custom", "inferred")

    return ("custom", "inferred")


def classify(result: ValidationResult) -> ClassifiedEntry:
    """Classify a single ValidationResult."""
    freq, confidence = _classify_schedule(result.schedule)
    return ClassifiedEntry(result=result, frequency=freq, confidence=confidence)


def classify_all(results: List[ValidationResult]) -> List[ClassifiedEntry]:
    """Classify a list of ValidationResults."""
    return [classify(r) for r in results]
