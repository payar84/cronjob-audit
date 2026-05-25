"""Tests for cronjob_audit.scorer."""
from __future__ import annotations

import pytest

from cronjob_audit.scorer import ScoreResult, score
from cronjob_audit.validator import ValidationResult


def _make_result(
    is_valid: bool = True,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    service: str = "svc",
) -> ValidationResult:
    return ValidationResult(
        entry_id="job-1",
        service=service,
        schedule="* * * * *",
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
    )


class TestScore:
    def test_returns_score_result(self):
        result = score([_make_result()])
        assert isinstance(result, ScoreResult)

    def test_empty_input_perfect_score(self):
        r = score([])
        assert r.score == 100.0
        assert r.grade == "A"
        assert r.total == 0

    def test_all_valid_no_warnings_perfect_score(self):
        results = [_make_result() for _ in range(5)]
        r = score(results)
        assert r.score == 100.0
        assert r.grade == "A"

    def test_errors_reduce_score(self):
        results = [_make_result(is_valid=False, errors=["bad field"]) for _ in range(5)]
        r = score(results)
        assert r.score < 100.0
        assert r.errors == 5

    def test_warnings_reduce_score_less_than_errors(self):
        warn_results = [_make_result(warnings=["runs every minute"]) for _ in range(5)]
        err_results = [_make_result(is_valid=False, errors=["bad field"]) for _ in range(5)]
        r_warn = score(warn_results)
        r_err = score(err_results)
        assert r_warn.score > r_err.score

    def test_total_counts_all_results(self):
        results = [_make_result() for _ in range(7)]
        r = score(results)
        assert r.total == 7

    def test_valid_count_excludes_errors_and_warnings(self):
        results = [
            _make_result(),
            _make_result(is_valid=False, errors=["err"]),
            _make_result(warnings=["warn"]),
        ]
        r = score(results)
        assert r.valid == 1
        assert r.errors == 1
        assert r.warnings == 1

    def test_grade_f_for_all_errors(self):
        results = [_make_result(is_valid=False, errors=["e"]) for _ in range(10)]
        r = score(results)
        assert r.grade == "F"

    def test_score_never_exceeds_100(self):
        results = [_make_result() for _ in range(100)]
        r = score(results)
        assert r.score <= 100.0

    def test_score_never_below_zero(self):
        results = [_make_result(is_valid=False, errors=["e"]) for _ in range(100)]
        r = score(results)
        assert r.score >= 0.0

    def test_to_dict_contains_expected_keys(self):
        r = score([_make_result()])
        d = r.to_dict()
        assert set(d.keys()) == {"total", "valid", "warnings", "errors", "score", "grade"}

    def test_to_dict_score_is_rounded(self):
        results = [_make_result(warnings=["w"]), _make_result(is_valid=False, errors=["e"])]
        r = score(results)
        d = r.to_dict()
        assert isinstance(d["score"], float)
        assert d["score"] == round(r.score, 2)
