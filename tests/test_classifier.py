"""Tests for cronjob_audit.classifier."""

from __future__ import annotations

import pytest

from cronjob_audit.classifier import (
    ClassifiedEntry,
    classify,
    classify_all,
    _classify_schedule,
)
from cronjob_audit.validator import ValidationResult


def _make_result(schedule: str, entry: str = "svc") -> ValidationResult:
    return ValidationResult(
        entry=entry,
        schedule=schedule,
        errors=[],
        warnings=[],
    )


# ---------------------------------------------------------------------------
# _classify_schedule unit tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("alias,expected", [
    ("@yearly", "yearly"),
    ("@annually", "yearly"),
    ("@monthly", "monthly"),
    ("@weekly", "weekly"),
    ("@daily", "daily"),
    ("@midnight", "daily"),
    ("@hourly", "hourly"),
])
def test_aliases_classified_exactly(alias, expected):
    freq, confidence = _classify_schedule(alias)
    assert freq == expected
    assert confidence == "exact"


def test_every_minute_is_minutely():
    freq, confidence = _classify_schedule("* * * * *")
    assert freq == "minutely"
    assert confidence == "exact"


def test_hourly_five_fields():
    freq, confidence = _classify_schedule("5 * * * *")
    assert freq == "hourly"
    assert confidence == "exact"


def test_daily_five_fields():
    freq, confidence = _classify_schedule("0 3 * * *")
    assert freq == "daily"
    assert confidence == "exact"


def test_weekly_five_fields():
    freq, confidence = _classify_schedule("0 9 * * 1")
    assert freq == "weekly"
    assert confidence == "exact"


def test_monthly_five_fields():
    freq, confidence = _classify_schedule("0 6 1 * *")
    assert freq == "monthly"
    assert confidence == "exact"


def test_yearly_five_fields():
    freq, confidence = _classify_schedule("0 0 1 1 *")
    assert freq == "yearly"
    assert confidence == "exact"


def test_step_expression_is_custom_inferred():
    freq, confidence = _classify_schedule("*/15 * * * *")
    assert freq == "custom"
    assert confidence == "inferred"


def test_invalid_field_count_is_custom_unknown():
    freq, confidence = _classify_schedule("0 * *")
    assert freq == "custom"
    assert confidence == "unknown"


# ---------------------------------------------------------------------------
# classify / classify_all
# ---------------------------------------------------------------------------

def test_classify_returns_classified_entry():
    result = _make_result("0 0 * * *")
    ce = classify(result)
    assert isinstance(ce, ClassifiedEntry)


def test_classify_preserves_result():
    result = _make_result("@daily", entry="backup-svc")
    ce = classify(result)
    assert ce.result is result


def test_classify_all_returns_list_of_same_length():
    results = [_make_result(s) for s in ["@daily", "* * * * *", "0 3 * * *"]]
    classified = classify_all(results)
    assert len(classified) == 3


def test_to_dict_contains_expected_keys():
    ce = classify(_make_result("@weekly", entry="report-svc"))
    d = ce.to_dict()
    assert set(d.keys()) == {"entry", "schedule", "frequency", "confidence"}
    assert d["frequency"] == "weekly"
    assert d["confidence"] == "exact"


def test_classify_all_empty_input():
    assert classify_all([]) == []
