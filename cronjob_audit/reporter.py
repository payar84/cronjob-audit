"""Report generation for cron audit validation results."""

import json
from typing import List, IO
from .validator import ValidationResult


def _summary(results: List[ValidationResult]) -> dict:
    total = len(results)
    valid = sum(1 for r in results if r.is_valid)
    invalid = total - valid
    warned = sum(1 for r in results if r.warnings)
    return {"total": total, "valid": valid, "invalid": invalid, "with_warnings": warned}


def generate_json_report(results: List[ValidationResult], stream: IO[str]) -> None:
    """Write a JSON report of validation results to the given stream."""
    report = {
        "summary": _summary(results),
        "entries": [r.to_dict() for r in results],
    }
    json.dump(report, stream, indent=2)
    stream.write("\n")


def generate_text_report(results: List[ValidationResult], stream: IO[str]) -> None:
    """Write a human-readable text report to the given stream."""
    summary = _summary(results)
    stream.write("=== Cron Audit Report ===\n")
    stream.write(
        f"Total: {summary['total']}  "
        f"Valid: {summary['valid']}  "
        f"Invalid: {summary['invalid']}  "
        f"Warnings: {summary['with_warnings']}\n"
    )
    stream.write("\n")

    for r in results:
        status = "OK" if r.is_valid else "FAIL"
        stream.write(f"[{status}] {r.service} / {r.name}  ({r.schedule})\n")
        for err in r.errors:
            stream.write(f"  ERROR: {err}\n")
        for warn in r.warnings:
            stream.write(f"  WARN:  {warn}\n")

    stream.write("\n=== End of Report ===\n")
