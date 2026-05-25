"""Assign a numeric health score to a collection of ValidationResults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronjob_audit.validator import ValidationResult

# Weights used when computing the composite score (0-100).
_ERROR_PENALTY = 20
_WARNING_PENALTY = 5
_BASE_SCORE = 100


@dataclass
class ScoreResult:
    """Outcome of scoring a collection of validation results."""

    total: int
    valid: int
    warnings: int
    errors: int
    score: float  # 0.0 – 100.0
    grade: str    # A / B / C / D / F

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "valid": self.valid,
            "warnings": self.warnings,
            "errors": self.errors,
            "score": round(self.score, 2),
            "grade": self.grade,
        }


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score(results: List[ValidationResult]) -> ScoreResult:
    """Compute a health score for *results*.

    Each error deducts *_ERROR_PENALTY* points and each warning deducts
    *_WARNING_PENALTY* points, both proportional to the share of affected
    entries so the score always stays in the 0-100 range.
    """
    total = len(results)
    if total == 0:
        return ScoreResult(
            total=0, valid=0, warnings=0, errors=0, score=100.0, grade="A"
        )

    error_count = sum(1 for r in results if not r.is_valid)
    warning_count = sum(
        1 for r in results if r.is_valid and r.warnings
    )
    valid_count = total - error_count - warning_count

    error_ratio = error_count / total
    warning_ratio = warning_count / total

    raw = _BASE_SCORE - (error_ratio * _ERROR_PENALTY * 5) - (warning_ratio * _WARNING_PENALTY * 2)
    final = max(0.0, min(100.0, raw))

    return ScoreResult(
        total=total,
        valid=valid_count,
        warnings=warning_count,
        errors=error_count,
        score=final,
        grade=_grade(final),
    )
