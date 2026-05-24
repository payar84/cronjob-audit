"""High-level summariser: combines aggregation, grouping, and annotation counts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from cronjob_audit.aggregator import AggregateStats, aggregate
from cronjob_audit.validator import ValidationResult


@dataclass
class Summary:
    stats: AggregateStats
    tag_counts: Dict[str, int]
    health_ratio: float  # valid / total, or 1.0 if total == 0

    def to_dict(self) -> dict:
        return {
            "stats": self.stats.to_dict(),
            "tag_counts": self.tag_counts,
            "health_ratio": round(self.health_ratio, 4),
        }


def _count_tags(results: Sequence[ValidationResult]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for result in results:
        tags: List[str] = getattr(result, "tags", []) or []
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def summarise(results: Sequence[ValidationResult], top_n: int = 5) -> Summary:
    """Build a Summary from a sequence of ValidationResult objects."""
    stats = aggregate(results, top_n=top_n)
    tag_counts = _count_tags(results)
    health_ratio = (stats.valid / stats.total) if stats.total > 0 else 1.0
    return Summary(stats=stats, tag_counts=tag_counts, health_ratio=health_ratio)
