"""Assign custom tags to validation results based on configurable rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Sequence

from cronjob_audit.validator import ValidationResult


@dataclass
class TagRule:
    """A rule that maps a predicate over a ValidationResult to a tag string."""

    tag: str
    predicate: Callable[[ValidationResult], bool]


@dataclass
class TaggedResult:
    """A ValidationResult decorated with zero or more tags."""

    result: ValidationResult
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "result": self.result.to_dict(),
            "tags": self.tags,
        }


# --------------------------------------------------------------------------- #
# Built-in rules                                                               #
# --------------------------------------------------------------------------- #

DEFAULT_RULES: List[TagRule] = [
    TagRule("valid", lambda r: r.is_valid and not r.warnings),
    TagRule("warning", lambda r: bool(r.warnings)),
    TagRule("invalid", lambda r: not r.is_valid),
    TagRule(
        "frequent",
        lambda r: r.is_valid and r.entry.schedule in ("* * * * *", "*/1 * * * *"),
    ),
    TagRule(
        "daily",
        lambda r: r.is_valid and r.entry.schedule.startswith("0 0 * * *"),
    ),
    TagRule(
        "hourly",
        lambda r: r.is_valid and r.entry.schedule.startswith("0 * * * *"),
    ),
]


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def tag(
    result: ValidationResult,
    rules: Sequence[TagRule] | None = None,
) -> TaggedResult:
    """Apply *rules* to *result* and return a TaggedResult.

    If *rules* is ``None`` the built-in :data:`DEFAULT_RULES` are used.
    """
    active_rules = DEFAULT_RULES if rules is None else list(rules)
    assigned = [rule.tag for rule in active_rules if rule.predicate(result)]
    return TaggedResult(result=result, tags=assigned)


def tag_all(
    results: Sequence[ValidationResult],
    rules: Sequence[TagRule] | None = None,
) -> List[TaggedResult]:
    """Apply :func:`tag` to every result in *results*."""
    return [tag(r, rules) for r in results]
