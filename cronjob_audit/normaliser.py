"""Normalise cron schedule strings into a canonical form."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Well-known aliases and their canonical equivalents
_ALIASES: Dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
    "@every_minute": "* * * * *",
}

_DOW_NAMES: Dict[str, str] = {
    "sun": "0",
    "mon": "1",
    "tue": "2",
    "wed": "3",
    "thu": "4",
    "fri": "5",
    "sat": "6",
}

_MONTH_NAMES: Dict[str, str] = {
    "jan": "1", "feb": "2", "mar": "3", "apr": "4",
    "may": "5", "jun": "6", "jul": "7", "aug": "8",
    "sep": "9", "oct": "10", "nov": "11", "dec": "12",
}


class NormaliseError(Exception):
    """Raised when a schedule string cannot be normalised."""


@dataclass
class NormaliseResult:
    original: str
    canonical: str
    alias_expanded: bool = False
    changes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "canonical": self.canonical,
            "alias_expanded": self.alias_expanded,
            "changes": self.changes,
        }


def _replace_names(token: str, mapping: Dict[str, str]) -> str:
    """Replace named tokens (case-insensitive) with numeric equivalents."""
    lower = token.lower()
    return mapping.get(lower, token)


def _normalise_field(token: str, mapping: Dict[str, str]) -> str:
    """Normalise a single cron field, handling lists, ranges, and steps."""
    parts = token.split(",")
    normalised = []
    for part in parts:
        if "/" in part:
            base, step = part.split("/", 1)
            base = _replace_names(base, mapping)
            normalised.append(f"{base}/{step}")
        elif "-" in part:
            lo, hi = part.split("-", 1)
            lo = _replace_names(lo, mapping)
            hi = _replace_names(hi, mapping)
            normalised.append(f"{lo}-{hi}")
        else:
            normalised.append(_replace_names(part, mapping))
    return ",".join(normalised)


def normalise(schedule: str) -> NormaliseResult:
    """Return a NormaliseResult with the canonical form of *schedule*."""
    original = schedule.strip()
    changes: List[str] = []
    alias_expanded = False

    # Expand well-known aliases first
    if original.lower() in _ALIASES:
        canonical = _ALIASES[original.lower()]
        changes.append(f"expanded alias '{original}' -> '{canonical}'")
        alias_expanded = True
        return NormaliseResult(
            original=original,
            canonical=canonical,
            alias_expanded=alias_expanded,
            changes=changes,
        )

    fields = original.split()
    if len(fields) not in (5, 6):
        raise NormaliseError(
            f"Expected 5 or 6 fields, got {len(fields)}: '{original}'"
        )

    # minute hour dom month dow [command]
    field_mappings = [{}, {}, {}, _MONTH_NAMES, _DOW_NAMES]
    normalised_fields = []
    for i, (f, mapping) in enumerate(zip(fields[:5], field_mappings)):
        nf = _normalise_field(f, mapping)
        if nf != f:
            changes.append(f"field {i}: '{f}' -> '{nf}'")
        normalised_fields.append(nf)

    canonical = " ".join(normalised_fields)
    return NormaliseResult(
        original=original,
        canonical=canonical,
        alias_expanded=alias_expanded,
        changes=changes,
    )
