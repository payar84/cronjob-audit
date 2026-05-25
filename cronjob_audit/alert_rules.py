"""Pre-built AlertRule definitions for common audit scenarios."""
from __future__ import annotations

from cronjob_audit.alerter import AlertRule


def _schedule(result) -> str:  # type: ignore[return]
    return getattr(result, "schedule", "") or getattr(
        getattr(result, "entry", None), "schedule", ""
    )


RULE_INVALID: AlertRule = AlertRule(
    name="invalid",
    description="Entry failed validation with at least one error.",
    predicate=lambda r: bool(r.errors),
)

RULE_WARNING: AlertRule = AlertRule(
    name="warning",
    description="Entry produced at least one validation warning.",
    predicate=lambda r: bool(r.warnings),
)

RULE_EVERY_MINUTE: AlertRule = AlertRule(
    name="every_minute",
    description="Schedule fires every minute — may cause excessive load.",
    predicate=lambda r: _schedule(r) == "* * * * *",
)

RULE_EVERY_HOUR: AlertRule = AlertRule(
    name="every_hour",
    description="Schedule fires every hour (minute wildcard).",
    predicate=lambda r: _schedule(r).startswith("* "),
)

RULE_NO_SERVICE: AlertRule = AlertRule(
    name="no_service",
    description="Entry has no service label.",
    predicate=lambda r: not getattr(
        getattr(r, "entry", r), "service", None
    ),
)

RULE_MIDNIGHT_ONLY: AlertRule = AlertRule(
    name="midnight_only",
    description="Schedule runs only at midnight (0 0 * * *).",
    predicate=lambda r: _schedule(r) in {"0 0 * * *", "@midnight", "@daily"},
)

# Convenience collection of all built-in rules
ALL_RULES: list = [
    RULE_INVALID,
    RULE_WARNING,
    RULE_EVERY_MINUTE,
    RULE_EVERY_HOUR,
    RULE_NO_SERVICE,
    RULE_MIDNIGHT_ONLY,
]
