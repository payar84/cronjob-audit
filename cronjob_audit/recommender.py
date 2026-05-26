"""Recommender: suggest schedule improvements based on validation results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from cronjob_audit.validator import ValidationResult


@dataclass
class Recommendation:
    entry_id: str
    service: str
    current_schedule: str
    suggestion: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "service": self.service,
            "current_schedule": self.current_schedule,
            "suggestion": self.suggestion,
            "reason": self.reason,
        }


@dataclass
class RecommendReport:
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.recommendations)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


_SUGGESTIONS: List[tuple] = [
    (
        lambda s: s == "* * * * *",
        "0 * * * *",
        "Running every minute is rarely necessary; consider hourly.",
    ),
    (
        lambda s: s.startswith("*/1 "),
        "0 * * * *",
        "*/1 is equivalent to * — consider a less frequent schedule.",
    ),
    (
        lambda s: _is_high_frequency(s),
        None,
        "Schedule runs very frequently; verify this is intentional.",
    ),
]


def _is_high_frequency(schedule: str) -> bool:
    """Return True when the minute field implies sub-5-minute runs."""
    parts = schedule.split()
    if len(parts) < 1:
        return False
    minute = parts[0]
    if minute == "*":
        return True
    if minute.startswith("*/"):
        try:
            step = int(minute[2:])
            return step < 5
        except ValueError:
            pass
    return False


def recommend(results: Sequence[ValidationResult]) -> RecommendReport:
    """Produce a :class:`RecommendReport` for the given validation results."""
    recs: List[Recommendation] = []

    for result in results:
        schedule = result.entry.get("schedule", "")
        entry_id = result.entry.get("id", "")
        service = result.entry.get("service", "")

        for predicate, suggestion, reason in _SUGGESTIONS:
            if predicate(schedule):
                recs.append(
                    Recommendation(
                        entry_id=entry_id,
                        service=service,
                        current_schedule=schedule,
                        suggestion=suggestion or schedule,
                        reason=reason,
                    )
                )
                break  # one recommendation per entry

    return RecommendReport(recommendations=recs)
