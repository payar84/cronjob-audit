"""Command-line interface for cronjob-audit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronjob_audit.loader import LoaderError, load_entries
from cronjob_audit.validator import validate_all
from cronjob_audit.exporter import ExportError, export_csv, export_markdown
from cronjob_audit.reporter import generate_json_report, generate_text_report

_FORMATS = ("json", "text", "csv", "markdown")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronjob-audit",
        description="Parse, validate, and report on cron schedules.",
    )
    p.add_argument("input", help="Path to YAML/JSON file containing cron entries")
    p.add_argument(
        "--format", "-f",
        choices=_FORMATS,
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    p.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 if any entry has errors",
    )
    return p


def _render(results, fmt: str) -> str:
    if fmt == "json":
        return generate_json_report(results)
    if fmt == "text":
        return generate_text_report(results)
    if fmt == "csv":
        return export_csv(results)
    if fmt == "markdown":
        return export_markdown(results)
    raise ValueError(f"Unknown format: {fmt}")


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        entries = load_entries(Path(args.input))
    except (LoaderError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    results = validate_all(entries)

    try:
        output = _render(results, args.format)
    except (ExportError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    if args.fail_on_error and any(r.status == "error" for r in results):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
