"""Cron expression parser for cronjob-audit."""

from dataclasses import dataclass
from typing import Optional

CRON_FIELD_NAMES = ["minute", "hour", "day_of_month", "month", "day_of_week"]

CRON_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 7),
}

MONTH_ALIASES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

DOW_ALIASES = {
    "sun": 0, "mon": 1, "tue": 2, "wed": 3,
    "thu": 4, "fri": 5, "sat": 6,
}


@dataclass
class CronExpression:
    raw: str
    minute: str
    hour: str
    day_of_month: str
    month: str
    day_of_week: str
    command: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "minute": self.minute,
            "hour": self.hour,
            "day_of_month": self.day_of_month,
            "month": self.month,
            "day_of_week": self.day_of_week,
            "command": self.command,
        }


class CronParseError(ValueError):
    """Raised when a cron expression cannot be parsed."""


def parse_cron(expression: str) -> CronExpression:
    """Parse a cron expression string into a CronExpression dataclass.

    Supports 5-field cron expressions with an optional trailing command.
    Raises CronParseError for invalid input.
    """
    if not expression or not expression.strip():
        raise CronParseError("Cron expression must not be empty.")

    parts = expression.strip().split()
    if len(parts) < 5:
        raise CronParseError(
            f"Expected at least 5 fields, got {len(parts)}: '{expression}'"
        )

    fields = parts[:5]
    command = " ".join(parts[5:]) if len(parts) > 5 else None

    for field_name, value in zip(CRON_FIELD_NAMES, fields):
        _validate_field(field_name, value)

    return CronExpression(
        raw=expression.strip(),
        minute=fields[0],
        hour=fields[1],
        day_of_month=fields[2],
        month=fields[3],
        day_of_week=fields[4],
        command=command,
    )


def _validate_field(field_name: str, value: str) -> None:
    """Validate a single cron field value."""
    min_val, max_val = CRON_FIELD_RANGES[field_name]
    aliases = MONTH_ALIASES if field_name == "month" else (
        DOW_ALIASES if field_name == "day_of_week" else {}
    )

    for part in value.split(","):
        _validate_part(field_name, part, min_val, max_val, aliases)


def _validate_part(field_name: str, part: str, min_val: int, max_val: int, aliases: dict) -> None:
    if part == "*":
        return
    if "/" in part:
        base, step = part.split("/", 1)
        if not step.isdigit() or int(step) < 1:
            raise CronParseError(f"Invalid step value in field '{field_name}': '{part}'")
        if base != "*":
            _validate_part(field_name, base, min_val, max_val, aliases)
        return
    if "-" in part:
        start, end = part.split("-", 1)
        _validate_number(field_name, start, min_val, max_val, aliases)
        _validate_number(field_name, end, min_val, max_val, aliases)
        return
    _validate_number(field_name, part, min_val, max_val, aliases)


def _validate_number(field_name: str, value: str, min_val: int, max_val: int, aliases: dict) -> None:
    resolved = aliases.get(value.lower(), value)
    if not str(resolved).isdigit():
        raise CronParseError(f"Invalid value '{value}' in field '{field_name}'")
    num = int(resolved)
    if not (min_val <= num <= max_val):
        raise CronParseError(
            f"Value {num} out of range [{min_val}, {max_val}] in field '{field_name}'"
        )
