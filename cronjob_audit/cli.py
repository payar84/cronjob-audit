"""Command-line interface for cronjob-audit."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from cronjob_audit.loader import load_entries, LoaderError
from cronjob_audit.merger import merge
from cronjob_audit.reporter import generate_json_report, generate_text_report
from cronjob_audit.validator import validate_all


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronjob-audit",
        description="Parse, validate, and report on cron schedules.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more cron definition files (YAML/JSON).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--prefer-service",
        metavar="SERVICE",
        default=None,
        help="When merging conflicts, prefer entries from this service.",
    )
    parser.add_argument(
        "--fail-on-conflict",
        action="store_true",
        help="Exit with code 2 if any schedule conflicts are detected after merge.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 if any validation errors are present.",
    )
    return parser


def _render(results, fmt: str) -> str:
    if fmt == "json":
        return generate_json_report(results)
    return generate_text_report(results)


def _load_and_validate(path: str):
    """Load entries from *path* and run validation, returning validated results.

    Raises ``SystemExit`` (via ``return 1`` in the caller) on loader failure;
    instead this helper raises ``LoaderError`` so the caller can handle it
    uniformly and print a consistent error message.
    """
    entries = load_entries(path)
    return list(validate_all(entries))


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    collections = []
    for path in args.files:
        try:
            results = _load_and_validate(path)
        except LoaderError as exc:
            print(f"[error] Could not load {path!r}: {exc}", file=sys.stderr)
            return 1
        collections.append(results)

    merge_result = merge(*collections, prefer_service=args.prefer_service)

    if args.fail_on_conflict and merge_result.has_conflicts:
        for conflict in merge_result.conflicts:
            print(
                f"[conflict] {conflict.entry_id}: "
                f"{conflict.schedules[0]!r} vs {conflict.schedules[1]!r}",
                file=sys.stderr,
            )
        return 2

    print(_render(merge_result.entries, args.format))

    if args.fail_on_error:
        has_errors = any(not r.is_valid for r in merge_result.entries)
        return 1 if has_errors else 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
