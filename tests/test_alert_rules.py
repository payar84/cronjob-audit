"""Tests for pre-built alert rules in cronjob_audit.alert_rules."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from cronjob_audit.alert_rules import (
    ALL_RULES,
    RULE_EVERY_HOUR,
    RULE_EVERY_MINUTE,
    RULE_INVALID,
    RULE_MIDNIGHT_ONLY,
    RULE_NO_SERVICE,
    RULE_WARNING,
)
from cronjob_audit.alerter import AlertRule, evaluate


def _r(schedule="0 * * * *", errors=None, warnings=None, service="svc"):
    entry = SimpleNamespace(entry_id="j", service=service, schedule=schedule)
    return SimpleNamespace(
        entry=entry,
        schedule=schedule,
        errors=errors or [],
        warnings=warnings or [],
    )


class TestRuleInvalid:
    def test_fires_on_errors(self):
        assert RULE_INVALID.predicate(_r(errors=["bad"]))

    def test_silent_on_clean(self):
        assert not RULE_INVALID.predicate(_r())


class TestRuleWarning:
    def test_fires_on_warnings(self):
        assert RULE_WARNING.predicate(_r(warnings=["watch out"]))

    def test_silent_on_clean(self):
        assert not RULE_WARNING.predicate(_r())


class TestRuleEveryMinute:
    def test_fires_for_star_expression(self):
        assert RULE_EVERY_MINUTE.predicate(_r(schedule="* * * * *"))

    def test_silent_for_hourly(self):
        assert not RULE_EVERY_MINUTE.predicate(_r(schedule="0 * * * *"))


class TestRuleEveryHour:
    def test_fires_when_minute_is_star(self):
        assert RULE_EVERY_HOUR.predicate(_r(schedule="* * * * *"))
        assert RULE_EVERY_HOUR.predicate(_r(schedule="* 6 * * *"))

    def test_silent_for_fixed_minute(self):
        assert not RULE_EVERY_HOUR.predicate(_r(schedule="0 * * * *"))


class TestRuleNoService:
    def test_fires_when_service_empty(self):
        assert RULE_NO_SERVICE.predicate(_r(service=""))

    def test_silent_when_service_present(self):
        assert not RULE_NO_SERVICE.predicate(_r(service="billing"))


class TestRuleMidnightOnly:
    def test_fires_for_midnight_cron(self):
        assert RULE_MIDNIGHT_ONLY.predicate(_r(schedule="0 0 * * *"))

    def test_fires_for_at_daily_alias(self):
        assert RULE_MIDNIGHT_ONLY.predicate(_r(schedule="@daily"))

    def test_silent_for_other_schedule(self):
        assert not RULE_MIDNIGHT_ONLY.predicate(_r(schedule="0 6 * * *"))


class TestAllRules:
    def test_all_rules_is_list_of_alert_rules(self):
        assert isinstance(ALL_RULES, list)
        for rule in ALL_RULES:
            assert isinstance(rule, AlertRule)

    def test_all_rules_contains_six_entries(self):
        assert len(ALL_RULES) == 6

    def test_evaluate_with_all_rules_returns_report(self):
        results = [_r(errors=["e"], warnings=["w"])]
        report = evaluate(results, ALL_RULES)
        assert report.total >= 2
