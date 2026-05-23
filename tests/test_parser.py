"""Tests for cronjob_audit.parser module."""

import pytest
from cronjob_audit.parser import (
    CronExpression,
    CronParseError,
    parse_cron,
)


class TestParseCron:
    def test_basic_expression(self):
        expr = parse_cron("0 12 * * 1")
        assert isinstance(expr, CronExpression)
        assert expr.minute == "0"
        assert expr.hour == "12"
        assert expr.day_of_month == "*"
        assert expr.month == "*"
        assert expr.day_of_week == "1"
        assert expr.command is None

    def test_expression_with_command(self):
        expr = parse_cron("30 6 * * * /usr/bin/backup.sh --quiet")
        assert expr.minute == "30"
        assert expr.hour == "6"
        assert expr.command == "/usr/bin/backup.sh --quiet"

    def test_every_minute(self):
        expr = parse_cron("* * * * *")
        assert expr.minute == "*"
        assert expr.raw == "* * * * *"

    def test_step_values(self):
        expr = parse_cron("*/5 */2 * * *")
        assert expr.minute == "*/5"
        assert expr.hour == "*/2"

    def test_range_values(self):
        expr = parse_cron("0 9-17 * * 1-5")
        assert expr.hour == "9-17"
        assert expr.day_of_week == "1-5"

    def test_list_values(self):
        expr = parse_cron("0 0 1,15 * *")
        assert expr.day_of_month == "1,15"

    def test_month_alias(self):
        expr = parse_cron("0 0 1 jan *")
        assert expr.month == "jan"

    def test_dow_alias(self):
        expr = parse_cron("0 8 * * mon")
        assert expr.day_of_week == "mon"

    def test_to_dict(self):
        expr = parse_cron("0 12 * * 1 /bin/run")
        d = expr.to_dict()
        assert d["minute"] == "0"
        assert d["command"] == "/bin/run"
        assert "raw" in d

    def test_strips_whitespace(self):
        expr = parse_cron("  0 12 * * 1  ")
        assert expr.raw == "0 12 * * 1"


class TestParseCronErrors:
    def test_empty_string_raises(self):
        with pytest.raises(CronParseError, match="must not be empty"):
            parse_cron("")

    def test_whitespace_only_raises(self):
        with pytest.raises(CronParseError, match="must not be empty"):
            parse_cron("   ")

    def test_too_few_fields_raises(self):
        with pytest.raises(CronParseError, match="Expected at least 5 fields"):
            parse_cron("0 12 * *")

    def test_invalid_minute_raises(self):
        with pytest.raises(CronParseError):
            parse_cron("60 12 * * *")

    def test_invalid_hour_raises(self):
        with pytest.raises(CronParseError):
            parse_cron("0 24 * * *")

    def test_invalid_month_raises(self):
        with pytest.raises(CronParseError):
            parse_cron("0 0 1 13 *")

    def test_invalid_dow_raises(self):
        with pytest.raises(CronParseError):
            parse_cron("0 0 * * 8")

    def test_invalid_step_raises(self):
        with pytest.raises(CronParseError):
            parse_cron("*/0 * * * *")

    def test_non_numeric_field_raises(self):
        with pytest.raises(CronParseError):
            parse_cron("abc 12 * * *")
