"""Filter annotated entries by tags, service, or validity."""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from cronjob_audit.annotator import AnnotatedEntry


def by_tag(entries: Iterable[AnnotatedEntry], tag: str) -> List[AnnotatedEntry]:
    """Return entries that carry the given tag."""
    return [e for e in entries if tag in e.tags]


def by_service(
    entries: Iterable[AnnotatedEntry], service: str
) -> List[AnnotatedEntry]:
    """Return entries belonging to the given service."""
    return [e for e in entries if e.result.entry.get("service") == service]


def by_validity(
    entries: Iterable[AnnotatedEntry], *, valid: bool
) -> List[AnnotatedEntry]:
    """Return only valid or only invalid entries depending on *valid* flag."""
    return [e for e in entries if e.result.is_valid == valid]


def has_warnings(entries: Iterable[AnnotatedEntry]) -> List[AnnotatedEntry]:
    """Return entries that have at least one warning."""
    return [e for e in entries if e.result.warnings]


def by_predicate(
    entries: Iterable[AnnotatedEntry],
    predicate: Callable[[AnnotatedEntry], bool],
) -> List[AnnotatedEntry]:
    """Generic filter: return entries for which *predicate* returns True."""
    return [e for e in entries if predicate(e)]


def search(
    entries: Iterable[AnnotatedEntry],
    *,
    tag: Optional[str] = None,
    service: Optional[str] = None,
    valid: Optional[bool] = None,
    warnings_only: bool = False,
) -> List[AnnotatedEntry]:
    """Convenience multi-criteria filter; criteria are ANDed together."""
    result: List[AnnotatedEntry] = list(entries)
    if tag is not None:
        result = by_tag(result, tag)
    if service is not None:
        result = by_service(result, service)
    if valid is not None:
        result = by_validity(result, valid=valid)
    if warnings_only:
        result = has_warnings(result)
    return result
