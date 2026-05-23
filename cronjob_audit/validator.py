"""Validation utilities for cron expressions across multiple services."""

from dataclasses import dataclass, field
from typing import List, Optional
from .parser import CronExpression, CronParseError, parse_cron


@dataclass
class ValidationResult:
    """Result of validating a single cron entry."""
    service: str
    name: str
    schedule: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    parsed: Optional[CronExpression] = None

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "name": self.name,
            "schedule": self.schedule,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "parsed": self.parsed.to_dict() if self.parsed else None,
        }


SUSPICIOUS_PATTERNS = [
    ("* * * * *", "Schedule runs every minute — may cause high load"),
    ("*/1 * * * *", "Schedule runs every minute — may cause high load"),
]


def validate_entry(service: str, name: str, schedule: str) -> ValidationResult:
    """Validate a single cron schedule entry."""
    errors: List[str] = []
    warnings: List[str] = []
    parsed: Optional[CronExpression] = None

    try:
        parsed = parse_cron(schedule)
    except CronParseError as exc:
        errors.append(str(exc))
        return ValidationResult(
            service=service,
            name=name,
            schedule=schedule,
            is_valid=False,
            errors=errors,
        )

    for pattern, warning in SUSPICIOUS_PATTERNS:
        if schedule.strip() == pattern:
            warnings.append(warning)

    return ValidationResult(
        service=service,
        name=name,
        schedule=schedule,
        is_valid=True,
        warnings=warnings,
        parsed=parsed,
    )


def validate_all(entries: List[dict]) -> List[ValidationResult]:
    """Validate a list of cron entry dicts with keys: service, name, schedule."""
    results = []
    for entry in entries:
        result = validate_entry(
            service=entry.get("service", "unknown"),
            name=entry.get("name", "unnamed"),
            schedule=entry.get("schedule", ""),
        )
        results.append(result)
    return results
