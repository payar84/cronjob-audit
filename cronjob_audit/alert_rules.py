"""Built-in AlertRule definitions for common cron audit findings."""
from __future__ import annotations

from cronjob_audit.alerter import AlertRule
from cronjob_audit.validator import ValidationResult


def _schedule(result: ValidationResult) -> str:
    return result.entry.get("schedule", "")


rule_invalid: AlertRule = AlertRule(
    name="invalid_schedule",
    description="Cron expression has one or more validation errors.",
    severity="error",
    predicate=lambda r: bool(r.errors),
)

rule_warning: AlertRule = AlertRule(
    name="schedule_warning",
    description="Cron expression triggered a validation warning.",
    severity="warning",
    predicate=lambda r: bool(r.warnings) and not r.errors,
)

rule_every_minute: AlertRule = AlertRule(
    name="every_minute_schedule",
    description="Job runs every minute (* * * * *), which may cause resource pressure.",
    severity="warning",
    predicate=lambda r: _schedule(r).strip() == "* * * * *",
)

rule_missing_service: AlertRule = AlertRule(
    name="missing_service",
    description="Entry has no service field or service is empty.",
    severity="warning",
    predicate=lambda r: not r.entry.get("service", "").strip(),
)

rule_missing_id: AlertRule = AlertRule(
    name="missing_entry_id",
    description="Entry has no id field or id is empty.",
    severity="warning",
    predicate=lambda r: not str(r.entry.get("id", "")).strip(),
)

rule_high_frequency: AlertRule = AlertRule(
    name="high_frequency_schedule",
    description="Job schedule runs more than once per minute via step values.",
    severity="error",
    predicate=lambda r: (
        len(_schedule(r).split()) == 5
        and _schedule(r).split()[0].startswith("*/")
        and int(_schedule(r).split()[0][2:]) < 1
    ) if len(_schedule(r).split()) == 5 and _schedule(r).split()[0].startswith("*/") else False,
)

DEFAULT_RULES: list[AlertRule] = [
    rule_invalid,
    rule_warning,
    rule_every_minute,
    rule_missing_service,
    rule_missing_id,
]
