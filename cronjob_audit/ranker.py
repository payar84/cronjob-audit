"""Rank cron entries by health score and frequency risk."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronjob_audit.validator import ValidationResult
from cronjob_audit.scorer import ScoreResult, score


@dataclass
class RankEntry:
    rank: int
    entry_id: str
    service: str
    schedule: str
    score: float
    grade: str
    errors: List[str]
    warnings: List[str]

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "entry_id": self.entry_id,
            "service": self.service,
            "schedule": self.schedule,
            "score": self.score,
            "grade": self.grade,
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class RankResult:
    entries: List[RankEntry] = field(default_factory=list)

    def top(self, n: int = 5) -> List[RankEntry]:
        """Return the top-n highest ranked (healthiest) entries."""
        return self.entries[:n]

    def bottom(self, n: int = 5) -> List[RankEntry]:
        """Return the bottom-n lowest ranked (least healthy) entries."""
        return self.entries[-n:]

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}


def rank(results: List[ValidationResult]) -> RankResult:
    """Rank validation results from healthiest to least healthy.

    Entries are sorted by descending score, then alphabetically by entry_id
    for stable ordering.
    """
    scored: ScoreResult = score(results)
    scored_map = {sr.entry_id: sr for sr in scored.entries}

    rank_entries: List[RankEntry] = []
    for vr in results:
        sr = scored_map.get(vr.entry_id)
        if sr is None:
            continue
        rank_entries.append(
            RankEntry(
                rank=0,
                entry_id=vr.entry_id,
                service=vr.service,
                schedule=vr.schedule,
                score=sr.score,
                grade=sr.grade,
                errors=list(vr.errors),
                warnings=list(vr.warnings),
            )
        )

    rank_entries.sort(key=lambda e: (-e.score, e.entry_id))
    for i, entry in enumerate(rank_entries, start=1):
        entry.rank = i

    return RankResult(entries=rank_entries)
