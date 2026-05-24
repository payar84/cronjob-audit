"""Aggregate validation results into statistical summaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from cronjob_audit.validator import ValidationResult


@dataclass
class AggregateStats:
    total: int = 0
    valid: int = 0
    warnings: int = 0
    errors: int = 0
    by_service: Dict[str, int] = field(default_factory=dict)
    most_common_schedules: List[tuple] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "valid": self.valid,
            "warnings": self.warnings,
            "errors": self.errors,
            "by_service": self.by_service,
            "most_common_schedules": [
                {"schedule": s, "count": c} for s, c in self.most_common_schedules
            ],
        }


def aggregate(results: Sequence[ValidationResult], top_n: int = 5) -> AggregateStats:
    """Compute aggregate statistics over a collection of ValidationResult objects."""
    stats = AggregateStats()
    schedule_counts: Dict[str, int] = {}

    for result in results:
        stats.total += 1

        if result.errors:
            stats.errors += 1
        elif result.warnings:
            stats.warnings += 1
        else:
            stats.valid += 1

        service = getattr(result.entry, "service", None) or "unknown"
        stats.by_service[service] = stats.by_service.get(service, 0) + 1

        schedule = getattr(result.entry, "schedule", "") or ""
        if schedule:
            schedule_counts[schedule] = schedule_counts.get(schedule, 0) + 1

    stats.most_common_schedules = sorted(
        schedule_counts.items(), key=lambda x: x[1], reverse=True
    )[:top_n]

    return stats
