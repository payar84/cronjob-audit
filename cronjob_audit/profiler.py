"""Profile cron entries to estimate execution frequency and resource pressure."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from cronjob_audit.validator import ValidationResult


@dataclass
class ProfileEntry:
    entry_id: str
    service: str
    schedule: str
    runs_per_day: float
    runs_per_hour: float
    pressure: str  # "low" | "medium" | "high" | "critical"

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "service": self.service,
            "schedule": self.schedule,
            "runs_per_day": self.runs_per_day,
            "runs_per_hour": self.runs_per_hour,
            "pressure": self.pressure,
        }


@dataclass
class ProfileReport:
    entries: List[ProfileEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def critical_count(self) -> int:
        return sum(1 for e in self.entries if e.pressure == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for e in self.entries if e.pressure == "high")

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "entries": [e.to_dict() for e in self.entries],
        }


def _runs_per_day(minute: str, hour: str) -> float:
    """Rough estimate of daily runs based on minute and hour fields."""
    def _slots(field_val: str, max_val: int) -> float:
        if field_val == "*":
            return float(max_val)
        if field_val.startswith("*/"):
            step = int(field_val[2:])
            return max_val / step
        return 1.0

    minute_slots = _slots(minute, 60)
    hour_slots = _slots(hour, 24)
    return round(minute_slots * hour_slots, 2)


def _pressure(runs_per_day: float) -> str:
    if runs_per_day >= 1440:
        return "critical"
    if runs_per_day >= 288:
        return "high"
    if runs_per_day >= 48:
        return "medium"
    return "low"


def profile(results: Sequence[ValidationResult]) -> ProfileReport:
    """Build a ProfileReport from a sequence of ValidationResult objects."""
    entries: List[ProfileEntry] = []
    for r in results:
        raw = r.entry
        schedule = raw.get("schedule", "")
        parts = schedule.split()
        if len(parts) < 5:
            continue
        minute, hour = parts[0], parts[1]
        rpd = _runs_per_day(minute, hour)
        rph = round(rpd / 24, 4)
        entries.append(
            ProfileEntry(
                entry_id=str(raw.get("id", "")),
                service=str(raw.get("service", "unknown")),
                schedule=schedule,
                runs_per_day=rpd,
                runs_per_hour=rph,
                pressure=_pressure(rpd),
            )
        )
    return ProfileReport(entries=entries)
