"""Utilities for sorting lists of ValidationResult or AnnotatedEntry objects."""

from __future__ import annotations

from typing import Callable, Iterable, List, Literal, TypeVar, Union

from cronjob_audit.validator import ValidationResult
from cronjob_audit.annotator import AnnotatedEntry

Sortable = Union[ValidationResult, AnnotatedEntry]
SortKey = Literal["service", "schedule", "status", "entry_id"]

_STATUS_ORDER = {"valid": 0, "warning": 1, "error": 2}


def _get_result(item: Sortable) -> ValidationResult:
    """Unwrap AnnotatedEntry to its underlying ValidationResult."""
    if isinstance(item, AnnotatedEntry):
        return item.result
    return item


def _key_service(item: Sortable) -> str:
    return (_get_result(item).entry.get("service") or "").lower()


def _key_schedule(item: Sortable) -> str:
    return _get_result(item).entry.get("schedule", "")


def _key_status(item: Sortable) -> int:
    result = _get_result(item)
    if result.errors:
        return _STATUS_ORDER["error"]
    if result.warnings:
        return _STATUS_ORDER["warning"]
    return _STATUS_ORDER["valid"]


def _key_entry_id(item: Sortable) -> str:
    return (_get_result(item).entry.get("id") or "").lower()


_KEY_FUNCS: dict[SortKey, Callable[[Sortable], object]] = {
    "service": _key_service,
    "schedule": _key_schedule,
    "status": _key_status,
    "entry_id": _key_entry_id,
}


def sort_results(
    items: Iterable[Sortable],
    by: SortKey = "service",
    reverse: bool = False,
) -> List[Sortable]:
    """Return a sorted copy of *items*.

    Parameters
    ----------
    items:
        An iterable of :class:`~cronjob_audit.validator.ValidationResult` or
        :class:`~cronjob_audit.annotator.AnnotatedEntry` objects.
    by:
        Sort key – one of ``"service"``, ``"schedule"``, ``"status"``,
        ``"entry_id"``.
    reverse:
        When *True* the order is descending.

    Raises
    ------
    ValueError
        If *by* is not a recognised sort key.
    """
    if by not in _KEY_FUNCS:
        raise ValueError(
            f"Unknown sort key {by!r}. Choose from: {list(_KEY_FUNCS)}"
        )
    return sorted(items, key=_KEY_FUNCS[by], reverse=reverse)
