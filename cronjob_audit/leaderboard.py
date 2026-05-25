"""Build a human-readable leaderboard from ranked cron entries."""
from __future__ import annotations

from typing import List

from cronjob_audit.ranker import RankEntry, RankResult

_GRADE_COLOUR = {"A": "✅", "B": "🟢", "C": "🟡", "D": "🟠", "F": "🔴"}
_COL_WIDTHS = (5, 24, 20, 22, 7, 4)
_HEADERS = ("Rank", "Entry ID", "Service", "Schedule", "Score", "Grade")


def _row(entry: RankEntry) -> str:
    icon = _GRADE_COLOUR.get(entry.grade, "")
    cols = (
        str(entry.rank),
        entry.entry_id[:22],
        entry.service[:18],
        entry.schedule[:20],
        f"{entry.score:.1f}",
        f"{icon} {entry.grade}",
    )
    return "  ".join(c.ljust(w) for c, w in zip(cols, _COL_WIDTHS))


def _separator() -> str:
    return "  ".join("-" * w for w in _COL_WIDTHS)


def render_leaderboard(
    result: RankResult,
    title: str = "Cron Job Health Leaderboard",
    limit: int | None = None,
) -> str:
    """Render a RankResult as a plain-text leaderboard table.

    Args:
        result: A :class:`RankResult` produced by :func:`ranker.rank`.
        title:  Heading printed above the table.
        limit:  If given, only the first *limit* rows are shown.

    Returns:
        A multi-line string ready for printing to a terminal or log.
    """
    entries: List[RankEntry] = result.entries
    if limit is not None:
        entries = entries[:limit]

    header_row = "  ".join(h.ljust(w) for h, w in zip(_HEADERS, _COL_WIDTHS))
    lines: List[str] = [
        title,
        "=" * len(title),
        header_row,
        _separator(),
    ]
    for entry in entries:
        lines.append(_row(entry))

    lines.append(_separator())
    lines.append(f"Total entries shown: {len(entries)} / {len(result.entries)}")
    return "\n".join(lines)
