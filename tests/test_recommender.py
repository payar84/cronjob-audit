"""Tests for cronjob_audit.recommender."""

from __future__ import annotations

import pytest

from cronjob_audit.recommender import Recommendation, RecommendReport, recommend
from cronjob_audit.validator import ValidationResult


def _make_result(schedule: str, entry_id: str = "job-1", service: str = "svc") -> ValidationResult:
    return ValidationResult(
        entry={"id": entry_id, "service": service, "schedule": schedule},
        errors=[],
        warnings=[],
    )


class TestRecommend:
    def test_returns_recommend_report(self):
        report = recommend([])
        assert isinstance(report, RecommendReport)

    def test_empty_input_gives_no_recommendations(self):
        report = recommend([])
        assert report.total == 0
        assert report.recommendations == []

    def test_every_minute_gets_recommendation(self):
        report = recommend([_make_result("* * * * *")])
        assert report.total == 1
        rec = report.recommendations[0]
        assert isinstance(rec, Recommendation)
        assert rec.suggestion == "0 * * * *"

    def test_step_one_minute_gets_recommendation(self):
        report = recommend([_make_result("*/1 * * * *")])
        assert report.total == 1
        assert report.recommendations[0].suggestion == "0 * * * *"

    def test_step_two_minute_is_high_frequency(self):
        report = recommend([_make_result("*/2 * * * *")])
        assert report.total == 1
        rec = report.recommendations[0]
        assert "frequently" in rec.reason.lower()

    def test_step_four_minute_is_high_frequency(self):
        report = recommend([_make_result("*/4 * * * *")])
        assert report.total == 1

    def test_step_five_minute_no_recommendation(self):
        report = recommend([_make_result("*/5 * * * *")])
        assert report.total == 0

    def test_hourly_schedule_no_recommendation(self):
        report = recommend([_make_result("0 * * * *")])
        assert report.total == 0

    def test_daily_schedule_no_recommendation(self):
        report = recommend([_make_result("0 2 * * *")])
        assert report.total == 0

    def test_entry_id_and_service_preserved(self):
        report = recommend([_make_result("* * * * *", entry_id="abc", service="payments")])
        rec = report.recommendations[0]
        assert rec.entry_id == "abc"
        assert rec.service == "payments"

    def test_current_schedule_preserved(self):
        report = recommend([_make_result("* * * * *")])
        assert report.recommendations[0].current_schedule == "* * * * *"

    def test_multiple_entries_only_flagged_ones_appear(self):
        results = [
            _make_result("* * * * *", entry_id="j1"),
            _make_result("0 3 * * *", entry_id="j2"),
            _make_result("*/2 * * * *", entry_id="j3"),
        ]
        report = recommend(results)
        assert report.total == 2
        ids = {r.entry_id for r in report.recommendations}
        assert ids == {"j1", "j3"}

    def test_to_dict_structure(self):
        report = recommend([_make_result("* * * * *", entry_id="x", service="s")])
        d = report.to_dict()
        assert d["total"] == 1
        assert len(d["recommendations"]) == 1
        rec_d = d["recommendations"][0]
        assert set(rec_d.keys()) == {"entry_id", "service", "current_schedule", "suggestion", "reason"}
