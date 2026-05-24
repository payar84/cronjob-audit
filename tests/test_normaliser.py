"""Tests for cronjob_audit.normaliser."""

import pytest

from cronjob_audit.normaliser import (
    NormaliseError,
    NormaliseResult,
    normalise,
)


class TestNormalise:
    def test_returns_normalise_result(self):
        result = normalise("0 0 * * *")
        assert isinstance(result, NormaliseResult)

    def test_plain_expression_unchanged(self):
        result = normalise("0 12 * * 1")
        assert result.canonical == "0 12 * * 1"
        assert result.changes == []

    def test_alias_daily_expanded(self):
        result = normalise("@daily")
        assert result.canonical == "0 0 * * *"
        assert result.alias_expanded is True

    def test_alias_midnight_expanded(self):
        result = normalise("@midnight")
        assert result.canonical == "0 0 * * *"
        assert result.alias_expanded is True

    def test_alias_hourly_expanded(self):
        result = normalise("@hourly")
        assert result.canonical == "0 * * * *"
        assert result.alias_expanded is True

    def test_alias_weekly_expanded(self):
        result = normalise("@weekly")
        assert result.canonical == "0 0 * * 0"

    def test_alias_monthly_expanded(self):
        result = normalise("@monthly")
        assert result.canonical == "0 0 1 * *"

    def test_alias_yearly_expanded(self):
        result = normalise("@yearly")
        assert result.canonical == "0 0 1 1 *"

    def test_alias_annually_expanded(self):
        result = normalise("@annually")
        assert result.canonical == "0 0 1 1 *"

    def test_alias_case_insensitive(self):
        result = normalise("@Daily")
        assert result.canonical == "0 0 * * *"
        assert result.alias_expanded is True

    def test_dow_name_replaced(self):
        result = normalise("0 9 * * Mon")
        assert result.canonical == "0 9 * * 1"
        assert any("Mon" in c for c in result.changes)

    def test_dow_range_replaced(self):
        result = normalise("0 9 * * Mon-Fri")
        assert result.canonical == "0 9 * * 1-5"

    def test_month_name_replaced(self):
        result = normalise("0 0 1 Jan *")
        assert result.canonical == "0 0 1 1 *"

    def test_month_list_replaced(self):
        result = normalise("0 0 1 Jan,Jul *")
        assert result.canonical == "0 0 1 1,7 *"

    def test_step_with_dow_name(self):
        result = normalise("0 0 * * Sun/2")
        assert result.canonical == "0 0 * * 0/2"

    def test_original_preserved(self):
        expr = "0 6 * * Mon"
        result = normalise(expr)
        assert result.original == expr

    def test_to_dict_keys(self):
        result = normalise("0 0 * * *")
        d = result.to_dict()
        assert set(d.keys()) == {"original", "canonical", "alias_expanded", "changes"}

    def test_too_few_fields_raises(self):
        with pytest.raises(NormaliseError):
            normalise("0 0 * *")

    def test_too_many_fields_raises(self):
        with pytest.raises(NormaliseError):
            normalise("0 0 * * * * extra")

    def test_whitespace_stripped(self):
        result = normalise("  0 0 * * *  ")
        assert result.canonical == "0 0 * * *"

    def test_no_changes_when_already_canonical(self):
        result = normalise("*/5 * * * *")
        assert result.changes == []
        assert result.alias_expanded is False
