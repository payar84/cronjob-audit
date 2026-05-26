"""Render a human-readable timeline from a TrackReport."""
from __future__ import annotations

from typing import List

from cronjob_audit.tracker import TrackReport, TrackEntry

_WIDTH = 60


def _bar(changed: int, total: int, width: int = 20) -> str:
    if total == 0:
        return "-" * width
    filled = round(changed / total * width)
    return "#" * filled + "-" * (width - filled)


def _format_entry(entry: TrackEntry, index: int) -> str:
    lines: List[str] = []
    cr = entry.compare_result
    if cr is None:
        lines.append(f"  [{index:>3}] {entry.label}  (baseline — no prior snapshot)")
    else:
        bar = _bar(cr.changed_count, cr.total)
        lines.append(
            f"  [{index:>3}] {entry.label}  "
            f"changed={cr.changed_count}/{cr.total}  [{bar}]"
        )
    return "\n".join(lines)


def render_timeline(report: TrackReport) -> str:
    """Return a plain-text timeline string for *report*."""
    if not report.entries:
        return "No snapshots recorded."

    header = "=" * _WIDTH
    title = "CRON AUDIT TIMELINE".center(_WIDTH)
    sub = f"  Snapshots: {report.total}  |  Sessions with changes: {report.changed_count}"
    divider = "-" * _WIDTH

    rows = [header, title, sub, divider]
    for i, entry in enumerate(report.entries):
        rows.append(_format_entry(entry, i))
    rows.append(header)
    return "\n".join(rows)
