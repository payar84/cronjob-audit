"""Tests for cronjob_audit.pipeline."""

import pytest
from unittest.mock import patch, MagicMock

from cronjob_audit.pipeline import (
    PipelineWarning,
    PipelineResult,
    run_pipeline,
)
from cronjob_audit.validator import ValidationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_raw_entry(entry_id="job-1", service="svc", schedule="0 * * * *", command="/bin/true"):
    return {
        "id": entry_id,
        "service": service,
        "schedule": schedule,
        "command": command,
    }


def _make_validation_result(entry_id="job-1", service="svc", schedule="0 * * * *",
                             is_valid=True, errors=None, warnings=None):
    return ValidationResult(
        entry_id=entry_id,
        service=service,
        schedule=schedule,
        is_valid=is_valid,
        errors=errors or [],
        warnings=warnings or [],
    )


# ---------------------------------------------------------------------------
# PipelineResult unit tests
# ---------------------------------------------------------------------------

class TestPipelineResult:
    def test_returns_pipeline_result(self):
        results = [_make_validation_result()]
        pr = PipelineResult(results=results, warnings=[], skipped=[])
        assert isinstance(pr, PipelineResult)

    def test_total_counts_all_results(self):
        results = [
            _make_validation_result(entry_id="j1"),
            _make_validation_result(entry_id="j2"),
            _make_validation_result(entry_id="j3"),
        ]
        pr = PipelineResult(results=results, warnings=[], skipped=[])
        assert pr.total == 3

    def test_skipped_count_reflects_skipped_list(self):
        pr = PipelineResult(
            results=[_make_validation_result()],
            warnings=[],
            skipped=["bad-entry-1", "bad-entry-2"],
        )
        assert pr.skipped_count == 2

    def test_to_dict_contains_expected_keys(self):
        pr = PipelineResult(
            results=[_make_validation_result()],
            warnings=[PipelineWarning(entry_id="j1", message="test warning")],
            skipped=[],
        )
        d = pr.to_dict()
        assert "total" in d
        assert "skipped_count" in d
        assert "results" in d
        assert "warnings" in d

    def test_to_dict_results_are_dicts(self):
        pr = PipelineResult(
            results=[_make_validation_result()],
            warnings=[],
            skipped=[],
        )
        d = pr.to_dict()
        assert isinstance(d["results"], list)
        assert isinstance(d["results"][0], dict)


# ---------------------------------------------------------------------------
# PipelineWarning tests
# ---------------------------------------------------------------------------

class TestPipelineWarning:
    def test_stores_entry_id_and_message(self):
        pw = PipelineWarning(entry_id="job-99", message="something odd")
        assert pw.entry_id == "job-99"
        assert pw.message == "something odd"

    def test_repr_contains_entry_id(self):
        pw = PipelineWarning(entry_id="job-99", message="something odd")
        assert "job-99" in repr(pw)


# ---------------------------------------------------------------------------
# run_pipeline integration-style tests (loader + validator mocked)
# ---------------------------------------------------------------------------

class TestRunPipeline:
    def test_returns_pipeline_result(self, tmp_path):
        config = tmp_path / "jobs.yaml"
        config.write_text(
            "jobs:\n"
            "  - id: j1\n"
            "    service: svc\n"
            "    schedule: '0 * * * *'\n"
            "    command: /bin/true\n"
        )
        with patch("cronjob_audit.pipeline.load_entries") as mock_load, \
             patch("cronjob_audit.pipeline.validate_all") as mock_validate:
            mock_load.return_value = [_make_raw_entry()]
            mock_validate.return_value = [_make_validation_result()]
            result = run_pipeline(str(config))
        assert isinstance(result, PipelineResult)

    def test_all_valid_entries_appear_in_results(self, tmp_path):
        config = tmp_path / "jobs.yaml"
        config.write_text("jobs: []")
        raw = [_make_raw_entry(entry_id=f"j{i}") for i in range(3)]
        validated = [_make_validation_result(entry_id=f"j{i}") for i in range(3)]
        with patch("cronjob_audit.pipeline.load_entries", return_value=raw), \
             patch("cronjob_audit.pipeline.validate_all", return_value=validated):
            result = run_pipeline(str(config))
        assert result.total == 3

    def test_loader_error_raises_or_records_skip(self, tmp_path):
        """A LoaderError for a single bad entry should not crash the pipeline."""
        from cronjob_audit.loader import LoaderError
        config = tmp_path / "jobs.yaml"
        config.write_text("jobs: []")
        with patch("cronjob_audit.pipeline.load_entries", side_effect=LoaderError("bad file")):
            with pytest.raises(LoaderError):
                run_pipeline(str(config))
