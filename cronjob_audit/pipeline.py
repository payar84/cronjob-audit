"""High-level pipeline: load -> normalise -> validate -> annotate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronjob_audit.annotator import AnnotatedEntry, annotate_all
from cronjob_audit.loader import LoaderError, load_entries
from cronjob_audit.normaliser import NormaliseError, normalise
from cronjob_audit.validator import ValidationResult, validate_all


@dataclass
class PipelineWarning:
    entry_id: str
    message: str


@dataclass
class PipelineResult:
    annotated: List[AnnotatedEntry] = field(default_factory=list)
    warnings: List[PipelineWarning] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.annotated)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "skipped_count": self.skipped_count,
            "warnings": [
                {"entry_id": w.entry_id, "message": w.message}
                for w in self.warnings
            ],
            "skipped": self.skipped,
            "annotated": [a.to_dict() for a in self.annotated],
        }


def run_pipeline(
    path: str,
    *,
    service_filter: Optional[str] = None,
    skip_invalid_schedules: bool = False,
) -> PipelineResult:
    """Execute the full audit pipeline for *path*.

    Parameters
    ----------
    path:
        Path to the YAML/JSON jobs file passed to :func:`load_entries`.
    service_filter:
        When provided, only entries whose ``service`` matches are processed.
    skip_invalid_schedules:
        If *True*, entries whose schedule cannot be normalised are silently
        skipped instead of raising an error.
    """
    try:
        raw_entries = load_entries(path)
    except LoaderError as exc:
        raise RuntimeError(f"Failed to load entries from '{path}': {exc}") from exc

    if service_filter:
        raw_entries = [
            e for e in raw_entries if e.get("service") == service_filter
        ]

    pipeline_warnings: List[PipelineWarning] = []
    skipped: List[str] = []
    normalised_entries = []

    for entry in raw_entries:
        entry_id = entry.get("id", entry.get("name", "<unknown>"))
        schedule = entry.get("schedule", "")
        try:
            norm_result = normalise(schedule)
        except NormaliseError as exc:
            if skip_invalid_schedules:
                skipped.append(entry_id)
                continue
            raise RuntimeError(
                f"Cannot normalise schedule for '{entry_id}': {exc}"
            ) from exc

        if norm_result.changes:
            pipeline_warnings.append(
                PipelineWarning(
                    entry_id=entry_id,
                    message=f"schedule normalised: {'; '.join(norm_result.changes)}",
                )
            )

        normalised_entries.append({**entry, "schedule": norm_result.canonical})

    validation_results: List[ValidationResult] = validate_all(normalised_entries)
    annotated: List[AnnotatedEntry] = annotate_all(validation_results)

    return PipelineResult(
        annotated=annotated,
        warnings=pipeline_warnings,
        skipped=skipped,
    )
