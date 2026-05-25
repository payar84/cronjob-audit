"""Tests for cronjob_audit.alert_rules built-in rules."""
import pytest
from cronjob_audit.alert_rules import (
    rule_invalid,
    rule_warning,
    rule_every_minute,
    rule_missing_service,
    rule_missing_id,
    DEFAULT_RULES,
)
from cronjob_audit.alerter import evaluate


def _r(schedule="0 * * * *", errors=None, warnings=None, service="svc", entry_id="j1"):
    class _FakeResult:
        def __init__(self):
            self.entry = {"id": entry_id, "service": service, "schedule": schedule}
            self.errors = errors or []
            self.warnings = warnings or []
    return _FakeResult()


class TestRuleInvalid:
    def test_fires_on_errors(self):
        assert rule_invalid.predicate(_r(errors=["bad field"]))

    def test_silent_on_clean(self):
        assert not rule_invalid.predicate(_r())


class TestRuleWarning:
    def test_fires_on_warnings_only(self):
        assert rule_warning.predicate(_r(warnings=["runs every minute"]))

    def test_silent_when_also_has_errors(self):
        assert not rule_warning.predicate(_r(errors=["e"], warnings=["w"]))

    def test_silent_when_clean(self):
        assert not rule_warning.predicate(_r())


class TestRuleEveryMinute:
    def test_fires_on_star_star_star_star_star(self):
        assert rule_every_minute.predicate(_r(schedule="* * * * *"))

    def test_fires_with_extra_whitespace(self):
        assert rule_every_minute.predicate(_r(schedule="  * * * * *  "))

    def test_silent_on_hourly(self):
        assert not rule_every_minute.predicate(_r(schedule="0 * * * *"))


class TestRuleMissingService:
    def test_fires_when_service_empty(self):
        assert rule_missing_service.predicate(_r(service=""))

    def test_fires_when_service_whitespace(self):
        assert rule_missing_service.predicate(_r(service="   "))

    def test_silent_when_service_present(self):
        assert not rule_missing_service.predicate(_r(service="billing"))


class TestRuleMissingId:
    def test_fires_when_id_empty(self):
        assert rule_missing_id.predicate(_r(entry_id=""))

    def test_silent_when_id_present(self):
        assert not rule_missing_id.predicate(_r(entry_id="job-99"))


class TestDefaultRules:
    def test_default_rules_is_list(self):
        assert isinstance(DEFAULT_RULES, list)

    def test_default_rules_not_empty(self):
        assert len(DEFAULT_RULES) > 0

    def test_all_have_name(self):
        for rule in DEFAULT_RULES:
            assert rule.name

    def test_evaluate_with_defaults_returns_report(self):
        from cronjob_audit.alerter import AlertReport
        report = evaluate([_r()], DEFAULT_RULES)
        assert isinstance(report, AlertReport)

    def test_evaluate_every_minute_triggers_finding(self):
        report = evaluate([_r(schedule="* * * * *")], DEFAULT_RULES)
        names = [f.rule_name for f in report.findings]
        assert "every_minute_schedule" in names

    def test_evaluate_invalid_triggers_finding(self):
        report = evaluate([_r(errors=["bad"])], DEFAULT_RULES)
        names = [f.rule_name for f in report.findings]
        assert "invalid_schedule" in names

    def test_evaluate_missing_service_triggers_finding(self):
        report = evaluate([_r(service="")], DEFAULT_RULES)
        names = [f.rule_name for f in report.findings]
        assert "missing_service" in names
