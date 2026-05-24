"""Export cron audit reports to various file formats (CSV, Markdown)."""

from __future__ import annotations

import csv
import io
from typing import List

from cronjob_audit.validator import ValidationResult


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_csv(results: List[ValidationResult]) -> str:
    """Serialise validation results to a CSV string.

    Args:
        results: List of ValidationResult objects to export.

    Returns:
        A CSV-formatted string with one row per entry.
    """
    if not isinstance(results, list):
        raise ExportError("results must be a list of ValidationResult objects")

    output = io.StringIO()
    fieldnames = ["service", "schedule", "command", "status", "errors", "warnings"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in results:
        writer.writerow({
            "service": r.entry.get("service", ""),
            "schedule": r.entry.get("schedule", ""),
            "command": r.entry.get("command", ""),
            "status": r.status,
            "errors": "; ".join(r.errors),
            "warnings": "; ".join(r.warnings),
        })

    return output.getvalue()


def export_markdown(results: List[ValidationResult]) -> str:
    """Serialise validation results to a Markdown table string.

    Args:
        results: List of ValidationResult objects to export.

    Returns:
        A Markdown-formatted string with a summary header and results table.
    """
    if not isinstance(results, list):
        raise ExportError("results must be a list of ValidationResult objects")

    total = len(results)
    ok = sum(1 for r in results if r.status == "ok")
    warn = sum(1 for r in results if r.status == "warning")
    err = sum(1 for r in results if r.status == "error")

    lines: List[str] = [
        "# Cron Audit Report",
        "",
        f"**Total:** {total} | **OK:** {ok} | **Warnings:** {warn} | **Errors:** {err}",
        "",
        "| Service | Schedule | Command | Status | Issues |",
        "| --- | --- | --- | --- | --- |",
    ]

    for r in results:
        service = r.entry.get("service", "")
        schedule = r.entry.get("schedule", "")
        command = r.entry.get("command", "")
        issues = "; ".join(r.errors + r.warnings) or "-"
        lines.append(f"| {service} | `{schedule}` | {command} | {r.status} | {issues} |")

    lines.append("")
    return "\n".join(lines)
