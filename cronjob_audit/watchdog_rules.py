"""Pre-built watchdog rules for common overdue scenarios."""
from __future__ import annotations

from typing import Callable

from cronjob_audit.watchdog import WatchdogEntry

# A rule is a callable that receives a WatchdogEntry and returns True if it fires.
WatchdogRule = Callable[[WatchdogEntry], bool]


def rule_never_ran() -> WatchdogRule:
    """Fire for jobs that have never run."""
    def _check(entry: WatchdogEntry) -> bool:
        return entry.last_run is None
    _check.__name__ = "never_ran"
    return _check


def rule_overdue() -> WatchdogRule:
    """Fire for any job flagged as overdue."""
    def _check(entry: WatchdogEntry) -> bool:
        return entry.overdue
    _check.__name__ = "overdue"
    return _check


def rule_overdue_by(threshold_minutes: float) -> WatchdogRule:
    """Fire when a job is overdue by more than *threshold_minutes*."""
    def _check(entry: WatchdogEntry) -> bool:
        return entry.overdue and entry.minutes_overdue >= threshold_minutes
    _check.__name__ = f"overdue_by_{threshold_minutes}m"
    return _check


def rule_service(service_name: str) -> WatchdogRule:
    """Fire only for entries belonging to *service_name*."""
    def _check(entry: WatchdogEntry) -> bool:
        return entry.service == service_name and entry.overdue
    _check.__name__ = f"service_{service_name}"
    return _check


def apply_rules(
    entries: list,
    rules: list,
) -> dict:
    """Return a mapping of rule name -> list of matching WatchdogEntry objects."""
    findings: dict = {}
    for rule in rules:
        name = getattr(rule, "__name__", repr(rule))
        findings[name] = [e for e in entries if rule(e)]
    return findings
