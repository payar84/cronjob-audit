"""Compute next run times and human-readable descriptions for cron expressions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from croniter import croniter, CroniterBadCronError

from cronjob_audit.parser import CronExpression


class SchedulerError(Exception):
    """Raised when next-run computation fails."""


def next_run(
    expr: CronExpression,
    after: Optional[datetime] = None,
) -> datetime:
    """Return the next datetime the cron expression will fire.

    Args:
        expr: A parsed :class:`CronExpression` instance.
        after: Reference point; defaults to *now* in UTC.

    Returns:
        A timezone-aware :class:`datetime` in UTC.

    Raises:
        SchedulerError: If the schedule string is not supported by croniter.
    """
    if after is None:
        after = datetime.now(tz=timezone.utc)

    schedule = " ".join([
        expr.minute,
        expr.hour,
        expr.day_of_month,
        expr.month,
        expr.day_of_week,
    ])

    try:
        it = croniter(schedule, after)
        next_dt: datetime = it.get_next(datetime)
        return next_dt.replace(tzinfo=timezone.utc)
    except CroniterBadCronError as exc:
        raise SchedulerError(f"Cannot compute next run for '{schedule}': {exc}") from exc


def describe(expr: CronExpression) -> str:
    """Return a short human-readable description of the cron expression.

    The description is intentionally simple and does not aim to cover every
    edge-case of the cron syntax.
    """
    if expr.minute == "*" and expr.hour == "*":
        return "Runs every minute"
    if expr.minute == "0" and expr.hour == "*":
        return "Runs at the start of every hour"
    if expr.minute == "0" and expr.hour == "0":
        return "Runs once a day at midnight"
    if expr.minute.startswith("*/"):
        interval = expr.minute[2:]
        return f"Runs every {interval} minute(s)"
    if expr.hour.startswith("*/"):
        interval = expr.hour[2:]
        return f"Runs every {interval} hour(s)"
    return (
        f"Runs at minute {expr.minute} of hour {expr.hour} "
        f"on day-of-month {expr.day_of_month}, "
        f"month {expr.month}, day-of-week {expr.day_of_week}"
    )
