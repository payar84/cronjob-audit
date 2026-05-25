"""Tests for cronjob_audit.tagger."""

from __future__ import annotations

import pytest

from cronjob_audit.tagger import (
    DEFAULT_RULES,
    TagRule,
    TaggedResult,
    tag,
    tag_all,
)
from cronjob_audit.validator import ValidationResult


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _make_result(
    schedule: str = "0 9 * * 1",
    is_valid: bool = True,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    service: str = "svc",
) -> ValidationResult:
    class _Entry:
        pass

    entry = _Entry()
    entry.schedule = schedule  # type: ignore[attr-defined]
    entry.service = service  # type: ignore[attr-defined]

    return ValidationResult(
        entry=entry,  # type: ignore[arg-type]
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
    )


# --------------------------------------------------------------------------- #
# Tests                                                                        #
# --------------------------------------------------------------------------- #


class TestTag:
    def test_returns_tagged_result(self):
        result = _make_result()
        tagged = tag(result)
        assert isinstance(tagged, TaggedResult)

    def test_result_preserved(self):
        result = _make_result()
        tagged = tag(result)
        assert tagged.result is result

    def test_valid_tag_assigned(self):
        result = _make_result(is_valid=True, warnings=[])
        tagged = tag(result)
        assert "valid" in tagged.tags

    def test_invalid_tag_assigned(self):
        result = _make_result(is_valid=False, errors=["bad field"])
        tagged = tag(result)
        assert "invalid" in tagged.tags
        assert "valid" not in tagged.tags

    def test_warning_tag_assigned(self):
        result = _make_result(is_valid=True, warnings=["runs every minute"])
        tagged = tag(result)
        assert "warning" in tagged.tags

    def test_frequent_tag_for_every_minute(self):
        result = _make_result(schedule="* * * * *")
        tagged = tag(result)
        assert "frequent" in tagged.tags

    def test_frequent_tag_for_step_one(self):
        result = _make_result(schedule="*/1 * * * *")
        tagged = tag(result)
        assert "frequent" in tagged.tags

    def test_daily_tag(self):
        result = _make_result(schedule="0 0 * * *")
        tagged = tag(result)
        assert "daily" in tagged.tags

    def test_hourly_tag(self):
        result = _make_result(schedule="0 * * * *")
        tagged = tag(result)
        assert "hourly" in tagged.tags

    def test_custom_rule_applied(self):
        rule = TagRule("my-service", lambda r: r.entry.service == "payments")
        result = _make_result(service="payments")
        tagged = tag(result, rules=[rule])
        assert "my-service" in tagged.tags

    def test_custom_rule_not_applied_when_predicate_false(self):
        rule = TagRule("my-service", lambda r: r.entry.service == "payments")
        result = _make_result(service="other")
        tagged = tag(result, rules=[rule])
        assert "my-service" not in tagged.tags

    def test_to_dict_contains_tags(self):
        result = _make_result()
        tagged = tag(result)
        d = tagged.to_dict()
        assert "tags" in d
        assert isinstance(d["tags"], list)


class TestTagAll:
    def test_returns_list_of_tagged_results(self):
        results = [_make_result(), _make_result(is_valid=False)]
        tagged = tag_all(results)
        assert len(tagged) == 2
        assert all(isinstance(t, TaggedResult) for t in tagged)

    def test_empty_input_gives_empty_output(self):
        assert tag_all([]) == []

    def test_each_entry_tagged_independently(self):
        r1 = _make_result(is_valid=True)
        r2 = _make_result(is_valid=False)
        t1, t2 = tag_all([r1, r2])
        assert "valid" in t1.tags
        assert "invalid" in t2.tags
