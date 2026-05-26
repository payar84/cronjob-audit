"""Tests for cronjob_audit.watchdog_rules."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from cronjob_audit.watchdog import WatchdogEntry
from cronjob_audit.watchdog_rules import (
    rule_never_ran,
    rule_overdue,
    rule_overdue_by,
    rule_service,
    apply_rules,
)


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(
    entry_id="j1",
    service="svc",
    schedule="0 * * * *",
    last_run=None,
    overdue=False,
    minutes_overdue=0.0,
    next_expected=None,
):
    return WatchdogEntry(
        entry_id=entry_id,
        service=service,
        schedule=schedule,
        last_run=last_run,
        overdue=overdue,
        minutes_overdue=minutes_overdue,
        next_expected=next_expected,
    )


class TestRuleNeverRan:
    def test_fires_when_never_ran(self):
        e = _entry(last_run=None)
        assert rule_never_ran()(e) is True

    def test_does_not_fire_when_ran(self):
        e = _entry(last_run=NOW - timedelta(hours=1))
        assert rule_never_ran()(e) is False


class TestRuleOverdue:
    def test_fires_when_overdue(self):
        e = _entry(overdue=True)
        assert rule_overdue()(e) is True

    def test_does_not_fire_when_on_time(self):
        e = _entry(overdue=False)
        assert rule_overdue()(e) is False


class TestRuleOverdueBy:
    def test_fires_above_threshold(self):
        e = _entry(overdue=True, minutes_overdue=60.0)
        assert rule_overdue_by(30.0)(e) is True

    def test_does_not_fire_below_threshold(self):
        e = _entry(overdue=True, minutes_overdue=10.0)
        assert rule_overdue_by(30.0)(e) is False

    def test_does_not_fire_when_not_overdue(self):
        e = _entry(overdue=False, minutes_overdue=60.0)
        assert rule_overdue_by(30.0)(e) is False


class TestRuleService:
    def test_fires_for_matching_service_overdue(self):
        e = _entry(service="payments", overdue=True)
        assert rule_service("payments")(e) is True

    def test_does_not_fire_for_wrong_service(self):
        e = _entry(service="billing", overdue=True)
        assert rule_service("payments")(e) is False

    def test_does_not_fire_when_not_overdue(self):
        e = _entry(service="payments", overdue=False)
        assert rule_service("payments")(e) is False


class TestApplyRules:
    def test_returns_dict_keyed_by_rule_name(self):
        entries = [_entry(overdue=True), _entry(overdue=False)]
        result = apply_rules(entries, [rule_overdue()])
        assert "overdue" in result

    def test_correct_entries_matched(self):
        e1 = _entry(entry_id="j1", overdue=True)
        e2 = _entry(entry_id="j2", overdue=False)
        result = apply_rules([e1, e2], [rule_overdue()])
        assert len(result["overdue"]) == 1
        assert result["overdue"][0].entry_id == "j1"

    def test_empty_entries_gives_empty_findings(self):
        result = apply_rules([], [rule_overdue(), rule_never_ran()])
        for v in result.values():
            assert v == []

    def test_multiple_rules_all_evaluated(self):
        e = _entry(last_run=None, overdue=True, minutes_overdue=90.0)
        result = apply_rules([e], [rule_never_ran(), rule_overdue_by(60.0)])
        assert len(result) == 2
