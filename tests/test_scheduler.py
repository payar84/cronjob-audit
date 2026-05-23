"""Tests for cronjob_audit.scheduler."""

from datetime import datetime, timezone

import pytest

from cronjob_audit.parser import CronExpression
from cronjob_audit.scheduler import SchedulerError, describe, next_run


def _expr(minute="*", hour="*", dom="*", month="*", dow="*") -> CronExpression:
    return CronExpression(
        minute=minute,
        hour=hour,
        day_of_month=dom,
        month=month,
        day_of_week=dow,
        command="echo test",
        raw="",
    )


class TestNextRun:
    _ref = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_every_minute_advances_by_one_minute(self):
        expr = _expr()
        result = next_run(expr, after=self._ref)
        assert result.minute == 1
        assert result.hour == 12

    def test_hourly_schedule(self):
        expr = _expr(minute="0")
        result = next_run(expr, after=self._ref)
        assert result.minute == 0
        assert result.hour == 13

    def test_daily_midnight(self):
        expr = _expr(minute="0", hour="0")
        result = next_run(expr, after=self._ref)
        assert result.day == 16
        assert result.hour == 0
        assert result.minute == 0

    def test_result_is_utc_aware(self):
        expr = _expr()
        result = next_run(expr, after=self._ref)
        assert result.tzinfo == timezone.utc

    def test_defaults_to_now_when_after_is_none(self):
        expr = _expr()
        result = next_run(expr)
        assert isinstance(result, datetime)

    def test_invalid_expression_raises_scheduler_error(self):
        expr = _expr(minute="99", hour="99")
        with pytest.raises(SchedulerError):
            next_run(expr, after=self._ref)


class TestDescribe:
    def test_every_minute(self):
        assert describe(_expr()) == "Runs every minute"

    def test_hourly(self):
        assert describe(_expr(minute="0")) == "Runs at the start of every hour"

    def test_daily_midnight(self):
        assert describe(_expr(minute="0", hour="0")) == "Runs once a day at midnight"

    def test_step_minutes(self):
        assert describe(_expr(minute="*/15")) == "Runs every 15 minute(s)"

    def test_step_hours(self):
        assert describe(_expr(minute="30", hour="*/6")) == "Runs every 6 hour(s)"

    def test_specific_schedule(self):
        result = describe(_expr(minute="30", hour="9", dom="1", month="*", dow="1"))
        assert "minute 30" in result
        assert "hour 9" in result
