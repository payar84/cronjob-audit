"""Tests for cronjob_audit.alerter."""
from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from cronjob_audit.alerter import (
    AlertFinding,
    AlertReport,
    AlertRule,
    RULE_HAS_ERRORS,
    RULE_HAS_WARNINGS,
    RULE_EVERY_MINUTE,
    evaluate,
)


def _make_result(
    entry_id: str = "job-1",
    service: str = "svc",
    schedule: str = "0 * * * *",
    errors: List[str] | None = None,
    warnings: List[str] | None = None,
):
    entry = SimpleNamespace(entry_id=entry_id, service=service, schedule=schedule)
    result = SimpleNamespace(
        entry=entry,
        schedule=schedule,
        errors=errors or [],
        warnings=warnings or [],
    )
    return result


class TestEvaluate:
    def test_returns_alert_report(self):
        report = evaluate([], [])
        assert isinstance(report, AlertReport)

    def test_no_findings_for_empty_input(self):
        report = evaluate([], [RULE_HAS_ERRORS])
        assert report.total == 0

    def test_no_findings_when_no_rules(self):
        r = _make_result(errors=["bad field"])
        report = evaluate([r], [])
        assert report.total == 0

    def test_detects_error_entry(self):
        r = _make_result(errors=["invalid minute"])
        report = evaluate([r], [RULE_HAS_ERRORS])
        assert report.total == 1
        assert report.findings[0].rule_name == "has_errors"

    def test_detects_warning_entry(self):
        r = _make_result(warnings=["runs every minute"])
        report = evaluate([r], [RULE_HAS_WARNINGS])
        assert report.total == 1

    def test_clean_entry_produces_no_finding(self):
        r = _make_result()
        report = evaluate([r], [RULE_HAS_ERRORS, RULE_HAS_WARNINGS])
        assert report.total == 0

    def test_every_minute_rule_fires(self):
        r = _make_result(schedule="* * * * *")
        report = evaluate([r], [RULE_EVERY_MINUTE])
        assert report.total == 1
        assert report.findings[0].rule_name == "every_minute"

    def test_every_minute_rule_does_not_fire_for_other(self):
        r = _make_result(schedule="0 0 * * *")
        report = evaluate([r], [RULE_EVERY_MINUTE])
        assert report.total == 0

    def test_multiple_rules_can_both_fire(self):
        r = _make_result(errors=["e"], warnings=["w"])
        report = evaluate([r], [RULE_HAS_ERRORS, RULE_HAS_WARNINGS])
        assert report.total == 2

    def test_fired_rules_lists_unique_names(self):
        r1 = _make_result(entry_id="a", errors=["e"])
        r2 = _make_result(entry_id="b", errors=["e"])
        report = evaluate([r1, r2], [RULE_HAS_ERRORS])
        assert report.fired_rules == ["has_errors"]

    def test_finding_preserves_entry_metadata(self):
        r = _make_result(entry_id="cron-99", service="billing", errors=["x"])
        report = evaluate([r], [RULE_HAS_ERRORS])
        f = report.findings[0]
        assert f.entry_id == "cron-99"
        assert f.service == "billing"

    def test_custom_rule(self):
        rule = AlertRule(
            name="daily_only",
            description="Must run daily.",
            predicate=lambda r: r.schedule != "0 0 * * *",
        )
        r = _make_result(schedule="0 6 * * *")
        report = evaluate([r], [rule])
        assert report.total == 1
        assert report.findings[0].rule_name == "daily_only"

    def test_to_dict_structure(self):
        r = _make_result(errors=["e"])
        report = evaluate([r], [RULE_HAS_ERRORS])
        d = report.to_dict()
        assert "total_findings" in d
        assert "fired_rules" in d
        assert "findings" in d
        assert d["total_findings"] == 1

    def test_finding_to_dict(self):
        f = AlertFinding(
            rule_name="has_errors",
            rule_description="desc",
            entry_id="j1",
            service="svc",
            schedule="* * * * *",
        )
        d = f.to_dict()
        assert d["rule"] == "has_errors"
        assert d["entry_id"] == "j1"
