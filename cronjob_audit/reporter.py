"""Generate human-readable and machine-readable reports from validation results."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from cronjob_audit.validator import ValidationResult
from cronjob_audit.scorer import score, ScoreResult


def _summary(results: List[ValidationResult]) -> Dict[str, Any]:
    scored: ScoreResult = score(results)
    return {
        "total": scored.total,
        "valid": scored.valid,
        "warnings": scored.warnings,
        "errors": scored.errors,
        "score": scored.score,
        "grade": scored.grade,
    }


def _enrich(result: ValidationResult) -> Dict[str, Any]:
    status = "error" if not result.is_valid else ("warning" if result.warnings else "ok")
    return {
        "entry_id": result.entry_id,
        "service": result.service,
        "schedule": result.schedule,
        "status": status,
        "errors": result.errors,
        "warnings": result.warnings,
    }


def _format_entry(result: ValidationResult) -> str:
    status = "ERROR" if not result.is_valid else ("WARN" if result.warnings else "OK")
    lines = [f"[{status}] {result.entry_id} ({result.service}) — {result.schedule}"]
    for err in result.errors:
        lines.append(f"  error   : {err}")
    for warn in result.warnings:
        lines.append(f"  warning : {warn}")
    return "\n".join(lines)


def generate_json_report(results: List[ValidationResult]) -> str:
    """Return a JSON string containing a summary and per-entry details."""
    payload = {
        "summary": _summary(results),
        "entries": [_enrich(r) for r in results],
    }
    return json.dumps(payload, indent=2)


def generate_text_report(results: List[ValidationResult]) -> str:
    """Return a plain-text report suitable for console output."""
    summary = _summary(results)
    header = (
        f"Cron Audit Report\n"
        f"{'=' * 40}\n"
        f"Total : {summary['total']}  "
        f"Valid : {summary['valid']}  "
        f"Warnings : {summary['warnings']}  "
        f"Errors : {summary['errors']}\n"
        f"Score : {summary['score']:.1f} / 100  Grade : {summary['grade']}\n"
        f"{'=' * 40}"
    )
    body = "\n".join(_format_entry(r) for r in results)
    return f"{header}\n{body}" if body else header
