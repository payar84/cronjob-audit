"""Watchdog: detect cron jobs that have not run recently or are overdue."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from cronjob_audit.scheduler import next_run
from cronjob_audit.validator import ValidationResult


class WatchdogError(Exception):
    """Raised when watchdog evaluation cannot proceed."""


@dataclass
class WatchdogEntry:
    entry_id: str
    service: str
    schedule: str
    last_run: Optional[datetime]  # None means never ran
    overdue: bool
    minutes_overdue: float
    next_expected: Optional[datetime]

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "service": self.service,
            "schedule": self.schedule,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "overdue": self.overdue,
            "minutes_overdue": round(self.minutes_overdue, 2),
            "next_expected": self.next_expected.isoformat() if self.next_expected else None,
        }


@dataclass
class WatchdogReport:
    entries: List[WatchdogEntry] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def overdue_count(self) -> int:
        return sum(1 for e in self.entries if e.overdue)

    @property
    def never_ran_count(self) -> int:
        return sum(1 for e in self.entries if e.last_run is None)

    def to_dict(self) -> dict:
        return {
            "checked_at": self.checked_at.isoformat(),
            "total": self.total,
            "overdue_count": self.overdue_count,
            "never_ran_count": self.never_ran_count,
            "entries": [e.to_dict() for e in self.entries],
        }


def _minutes_since(last_run: datetime, now: datetime) -> float:
    delta = now - last_run
    return delta.total_seconds() / 60.0


def evaluate(
    results: Sequence[ValidationResult],
    last_runs: dict,  # mapping entry_id -> datetime | None
    now: Optional[datetime] = None,
    grace_minutes: float = 5.0,
) -> WatchdogReport:
    """Evaluate which jobs are overdue given their last-run timestamps."""
    if now is None:
        now = datetime.now(timezone.utc)

    entries: List[WatchdogEntry] = []
    for result in results:
        entry_id = result.entry.get("id", "")
        service = result.entry.get("service", "unknown")
        schedule = result.entry.get("schedule", "")
        last_run = last_runs.get(entry_id)

        if not schedule or result.errors:
            continue

        try:
            nxt = next_run(schedule, now)
        except Exception:
            nxt = None

        overdue = False
        minutes_overdue = 0.0

        if last_run is None:
            overdue = True
            minutes_overdue = float("inf")
        else:
            elapsed = _minutes_since(last_run, now)
            try:
                nxt_after_last = next_run(schedule, last_run)
                expected_by = nxt_after_last
                if now > expected_by:
                    gap = (now - expected_by).total_seconds() / 60.0
                    if gap > grace_minutes:
                        overdue = True
                        minutes_overdue = gap
            except Exception:
                pass

        entries.append(
            WatchdogEntry(
                entry_id=entry_id,
                service=service,
                schedule=schedule,
                last_run=last_run,
                overdue=overdue,
                minutes_overdue=minutes_overdue if minutes_overdue != float("inf") else -1.0,
                next_expected=nxt,
            )
        )

    return WatchdogReport(entries=entries, checked_at=now)
