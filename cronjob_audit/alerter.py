"""Alert rule evaluation for cron audit results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Sequence

from cronjob_audit.validator import ValidationResult


@dataclass
class AlertRule:
    """A named predicate that fires when a result matches."""

    name: str
    description: str
    predicate: Callable[[ValidationResult], bool]


@dataclass
class AlertFinding:
    """A single rule match against a specific result."""

    rule_name: str
    rule_description: str
    entry_id: str
    service: str
    schedule: str

    def to_dict(self) -> dict:
        return {
            "rule": self.rule_name,
            "description": self.rule_description,
            "entry_id": self.entry_id,
            "service": self.service,
            "schedule": self.schedule,
        }


@dataclass
class AlertReport:
    """Aggregated output from running all alert rules."""

    findings: List[AlertFinding] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.findings)

    @property
    def fired_rules(self) -> List[str]:
        seen: list = []
        for f in self.findings:
            if f.rule_name not in seen:
                seen.append(f.rule_name)
        return seen

    def to_dict(self) -> dict:
        return {
            "total_findings": self.total,
            "fired_rules": self.fired_rules,
            "findings": [f.to_dict() for f in self.findings],
        }


# Built-in rules
RULE_HAS_ERRORS: AlertRule = AlertRule(
    name="has_errors",
    description="Entry has one or more validation errors.",
    predicate=lambda r: bool(r.errors),
)

RULE_HAS_WARNINGS: AlertRule = AlertRule(
    name="has_warnings",
    description="Entry has one or more validation warnings.",
    predicate=lambda r: bool(r.warnings),
)

RULE_EVERY_MINUTE: AlertRule = AlertRule(
    name="every_minute",
    description="Schedule runs every minute (* * * * *).",
    predicate=lambda r: getattr(r, "schedule", "") == "* * * * *",
)


def evaluate(
    results: Sequence[ValidationResult],
    rules: Sequence[AlertRule],
) -> AlertReport:
    """Evaluate *rules* against every result and return an AlertReport."""
    findings: List[AlertFinding] = []
    for result in results:
        entry = result.entry  # type: ignore[attr-defined]
        for rule in rules:
            if rule.predicate(result):
                findings.append(
                    AlertFinding(
                        rule_name=rule.name,
                        rule_description=rule.description,
                        entry_id=getattr(entry, "entry_id", ""),
                        service=getattr(entry, "service", ""),
                        schedule=getattr(entry, "schedule", ""),
                    )
                )
    return AlertReport(findings=findings)
