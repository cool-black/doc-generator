"""Tests for content review and quality assurance system."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from doc_gen.models.review import (
    IssueCategory,
    IssueSeverity,
    QualityMetrics,
    ReviewIssue,
    ReviewResult,
    ReviewScores,
)
from doc_gen.core.reviewer import ContentReviewer


class TestReviewModels:
    """Test review data models."""

    def test_review_issue_creation(self):
        """Test ReviewIssue dataclass."""
        issue = ReviewIssue(
            severity=IssueSeverity.HIGH,
            category=IssueCategory.HALLUCINATION,
            description="Test description",
            suggestion="Fix it",
        )
        assert issue.severity == IssueSeverity.HIGH
        assert issue.category == IssueCategory.HALLUCINATION
        assert issue.description == "Test description"
        assert issue.suggestion == "Fix it"

    def test_review_scores_average(self):
        """Test ReviewScores average calculation."""
        scores = ReviewScores(
            factual_accuracy=80,
            consistency=90,
            terminology=85,
            hallucination_free=95,
        )
        assert scores.average == 87.5

    def test_review_result_has_hallucination(self):
        """Test ReviewResult hallucination detection."""
        result_without = ReviewResult(
            overall_score=90,
            passed=True,
            issues=[
                ReviewIssue(
                    severity=IssueSeverity.LOW,
                    category=IssueCategory.CONSISTENCY,
                    description="Minor issue",
                    suggestion="Fix",
                ),
            ],
        )
        assert not result_without.has_hallucination

        result_with = ReviewResult(
            overall_score=60,
            passed=False,
            issues=[
                ReviewIssue(
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.HALLUCINATION,
                    description="Made up fact",
                    suggestion="Remove",
                ),
            ],
        )
        assert result_with.has_hallucination

    def test_quality_metrics_calculation(self):
        """Test QualityMetrics calculations."""
        metrics = QualityMetrics()

        # Add some reviews
        metrics.add_review(ReviewResult(overall_score=90, passed=True))
        metrics.add_review(ReviewResult(overall_score=70, passed=False))
        metrics.add_review(ReviewResult(overall_score=85, passed=True))

        assert metrics.total_chapters == 3
        assert metrics.passed_chapters == 2
        assert metrics.failed_chapters == 1
        assert metrics.pass_rate == (2 / 3) * 100
        assert metrics.average_score == (90 + 70 + 85) / 3

    def test_quality_metrics_hallucination_rate(self):
        """Test hallucination rate calculation."""
        metrics = QualityMetrics()

        # Add reviews with and without hallucinations
        metrics.add_review(ReviewResult(
            overall_score=90, passed=True, issues=[]
        ))
        metrics.add_review(ReviewResult(
            overall_score=70, passed=False, issues=[
                ReviewIssue(
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.HALLUCINATION,
                    description="Hallucination",
                    suggestion="Remove",
                ),
            ],
        ))

        assert metrics.hallucination_count == 1
        assert metrics.hallucination_rate == 50.0


class TestContentReviewer:
    """Test ContentReviewer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.mock_llm = MagicMock()
        self.mock_storage = MagicMock()
        self.mock_repo = MagicMock()

        self.reviewer = ContentReviewer(
            llm_client=self.mock_llm,
            storage=self.mock_storage,
            repo=self.mock_repo,
            min_score=80,
            max_retries=2,
        )

    def test_should_regenerate_passed(self):
        """Test should_regenerate for passed review."""
        result = ReviewResult(
            overall_score=90,
            passed=True,
            chapter_index=0,
            chapter_title="Test",
        )
        assert not self.reviewer.should_regenerate(result, attempt=0)

    def test_should_regenerate_failed_first_attempt(self):
        """Test should_regenerate for failed review on first attempt."""
        result = ReviewResult(
            overall_score=60,
            passed=False,
            chapter_index=0,
            chapter_title="Test",
        )
        assert self.reviewer.should_regenerate(result, attempt=0)

    def test_should_regenerate_max_retries_reached(self):
        """Test should_regenerate when max retries reached."""
        result = ReviewResult(
            overall_score=60,
            passed=False,
            chapter_index=0,
            chapter_title="Test",
        )
        # max_retries=2, so attempt=2 is the 3rd attempt (initial + 2 retries)
        assert not self.reviewer.should_regenerate(result, attempt=2)

    def test_get_metrics_report(self):
        """Test quality metrics report generation."""
        # Add some reviews to metrics
        self.reviewer.metrics.add_review(ReviewResult(
            overall_score=90, passed=True, issues=[]
        ))
        self.reviewer.metrics.add_review(ReviewResult(
            overall_score=85, passed=True, issues=[]
        ))

        report = self.reviewer.get_metrics_report()

        assert report["metrics"]["total_chapters"] == 2
        assert report["metrics"]["passed_chapters"] == 2
        assert report["thresholds"]["min_score"] == 80
        assert report["thresholds"]["max_retries"] == 2

    def test_parse_review_response_valid(self):
        """Test parsing valid review response."""
        response = '''
        {
            "overall_score": 85,
            "passed": true,
            "scores": {
                "factual_accuracy": 90,
                "consistency": 85,
                "terminology": 80,
                "hallucination_free": 85
            },
            "issues": [
                {
                    "severity": "low",
                    "category": "consistency",
                    "description": "Minor formatting issue",
                    "suggestion": "Fix formatting"
                }
            ],
            "summary": "Good chapter overall"
        }
        '''

        result = self.reviewer._parse_review_response(response, 0, "Test Chapter")

        assert result.overall_score == 85
        assert result.passed is True
        assert result.scores.factual_accuracy == 90
        assert len(result.issues) == 1
        assert result.issues[0].severity == IssueSeverity.LOW

    def test_parse_review_response_with_code_block(self):
        """Test parsing review response wrapped in markdown code block."""
        response = '''
        ```json
        {
            "overall_score": 90,
            "passed": true,
            "scores": {
                "factual_accuracy": 90,
                "consistency": 90,
                "terminology": 90,
                "hallucination_free": 90
            },
            "issues": [],
            "summary": "Excellent"
        }
        ```
        '''

        result = self.reviewer._parse_review_response(response, 0, "Test")

        assert result.overall_score == 90
        assert result.passed is True

    def test_parse_review_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        response = "This is not valid JSON"

        result = self.reviewer._parse_review_response(response, 0, "Test")

        assert result.overall_score == 0
        assert result.passed is False
        assert "Failed to parse" in result.summary

    def test_parse_review_response_empty(self):
        """Test parsing empty response."""
        result = self.reviewer._parse_review_response("", 0, "Test")

        assert result.overall_score == 0
        assert result.passed is False
        assert "Empty review response" in result.summary

    def test_parse_review_response_extract_score_fallback(self):
        """Test extracting score from malformed JSON."""
        # Malformed response but contains score
        response = 'Some text before {"overall_score": 85, "passed": true} some text after'

        result = self.reviewer._parse_review_response(response, 0, "Test")

        assert result.overall_score == 85
        assert result.passed is True
        assert "fallback" in result.summary

    def test_generate_recommendations_high_hallucination(self):
        """Test recommendations for high hallucination rate."""
        # Add reviews with hallucinations
        for _ in range(10):
            self.reviewer.metrics.add_review(ReviewResult(
                overall_score=70,
                passed=False,
                issues=[
                    ReviewIssue(
                        severity=IssueSeverity.HIGH,
                        category=IssueCategory.HALLUCINATION,
                        description="Hallucination",
                        suggestion="Fix",
                    ),
                ],
            ))

        recommendations = self.reviewer._generate_recommendations()

        assert len(recommendations) > 0
        assert "Hallucination rate is above 5%" in recommendations[0]

    def test_generate_recommendations_low_pass_rate(self):
        """Test recommendations for low pass rate."""
        # Add mostly failed reviews
        for _ in range(5):
            self.reviewer.metrics.add_review(ReviewResult(
                overall_score=60, passed=False, issues=[]
            ))
        self.reviewer.metrics.add_review(ReviewResult(
            overall_score=90, passed=True, issues=[]
        ))

        recommendations = self.reviewer._generate_recommendations()

        assert any("Pass rate is below 80%" in r for r in recommendations)


class TestReviewIntegration:
    """Integration tests for review system."""

    def test_full_review_workflow(self):
        """Test complete review workflow."""
        metrics = QualityMetrics()

        # Simulate successful review
        success_result = ReviewResult(
            overall_score=90,
            passed=True,
            scores=ReviewScores(
                factual_accuracy=90,
                consistency=90,
                terminology=90,
                hallucination_free=90,
            ),
            issues=[],
            summary="Excellent quality",
        )
        metrics.add_review(success_result)

        # Simulate failed review
        fail_result = ReviewResult(
            overall_score=65,
            passed=False,
            scores=ReviewScores(
                factual_accuracy=70,
                consistency=60,
                terminology=65,
                hallucination_free=65,
            ),
            issues=[
                ReviewIssue(
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.HALLUCINATION,
                    description="Unsupported claim",
                    suggestion="Remove or cite source",
                ),
            ],
            summary="Needs improvement",
        )
        metrics.add_review(fail_result)

        # Verify metrics
        assert metrics.total_chapters == 2
        assert metrics.passed_chapters == 1
        assert metrics.failed_chapters == 1
        assert metrics.pass_rate == 50.0
        assert metrics.hallucination_count == 1
        assert metrics.hallucination_rate == 50.0

    def test_serialization_roundtrip(self):
        """Test serialization and deserialization of review results."""
        original = ReviewResult(
            overall_score=85,
            passed=True,
            scores=ReviewScores(
                factual_accuracy=90,
                consistency=85,
                terminology=80,
                hallucination_free=85,
            ),
            issues=[
                ReviewIssue(
                    severity=IssueSeverity.MEDIUM,
                    category=IssueCategory.CONSISTENCY,
                    description="Inconsistent terminology",
                    suggestion="Use consistent terms",
                ),
            ],
            summary="Good quality with minor issues",
            chapter_index=0,
            chapter_title="Introduction",
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = ReviewResult.from_dict(data)

        assert restored.overall_score == original.overall_score
        assert restored.passed == original.passed
        assert restored.scores.average == original.scores.average
        assert len(restored.issues) == len(original.issues)
        assert restored.issues[0].severity == original.issues[0].severity
        assert restored.chapter_title == original.chapter_title
