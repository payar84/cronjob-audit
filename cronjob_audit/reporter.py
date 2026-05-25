"""Generate JSON and plain-text audit reports from validation results."""

from __future__ import annotations

import json
from typing import List

from cronjob_audit.validator import ValidationResult
from cronjob_audit.scheduler import describe, next_run, SchedulerError


def _summary(results: List[ValidationResult]) -> dict:
    valid = sum(1 for r in results if r.is_valid)
    warnings = sum(1 for r in results if r.warnings)
    errors = sum(1 for r in results if r.errors)
    return {
        "total": len(results),
        "valid": valid,
        "with_warnings": warnings,
        "with_errors": errors,
    }


def _enrich(result: ValidationResult) -> dict:
    """Attach next-run time and description to a serialised ValidationResult."""
    data = result.to_dict()
    expr = result.entry.expression
    if expr is not None:
        try:
            data["next_run"] = next_run(expr).isoformat()
        except SchedulerError:
            data["next_run"] = None
        data["description"] = describe(expr)
    else:
        data["next_run"] = None
        data["description"] = None
    return data


def _format_entry(result: ValidationResult) -> List[str]:
    """Return lines representing a single entry in the plain-text report."""
    lines: List[str] = []
    status = "OK" if result.is_valid else "FAIL"
    expr = result.entry.expression
    desc = describe(expr) if expr else "(unparsed)"
    lines.append(f"[{status}] {result.entry.raw!r}")
    lines.append(f"       {desc}")
    for w in result.warnings:
        lines.append(f"  WARN  {w}")
    for e in result.errors:
        lines.append(f"  ERROR {e}")
    return lines


def generate_json_report(results: List[ValidationResult]) -> str:
    """Return a JSON string containing the full audit report."""
    report = {
        "summary": _summary(results),
        "entries": [_enrich(r) for r in results],
    }
    return json.dumps(report, indent=2)


def generate_text_report(results: List[ValidationResult]) -> str:
    """Return a human-readable plain-text audit report."""
    lines: List[str] = []
    summary = _summary(results)
    lines.append("=== Cron Audit Report ===")
    lines.append(
        f"Total: {summary['total']}  "
        f"Valid: {summary['valid']}  "
        f"Warnings: {summary['with_warnings']}  "
        f"Errors: {summary['with_errors']}"
    )
    lines.append("")
    for result in results:
        lines.extend(_format_entry(result))
    return "\n".join(lines)
