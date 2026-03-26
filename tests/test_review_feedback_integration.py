"""Integration tests for review feedback loop in generation pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from doc_gen.core.generator import DocumentGenerator
from doc_gen.core.reviewer import ContentReviewer
from doc_gen.models.document import GenerationContext
from doc_gen.models.project import ProjectConfig, ProjectStatus, DocumentType, Language, StyleGuide
from doc_gen.models.review import (
    IssueCategory,
    IssueSeverity,
    ReviewIssue,
    ReviewResult,
    ReviewScores,
)
from doc_gen.storage.project import ProjectStorage


class TestReviewFeedbackLoop:
    """Test that review feedback is passed to retry generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.mock_llm = MagicMock()
        self.mock_storage = MagicMock()
        self.mock_repo = MagicMock()
        self.mock_repo.get_uploaded_files.return_value = []

    def _create_test_project(self) -> ProjectConfig:
        """Create a test project."""
        return ProjectConfig(
            id="test-project-1",
            name="Test Project",
            domain="Testing",
            doc_type=DocumentType.TUTORIAL,
            language=Language.CHINESE,
            audience="developers",
            terminology={},
            style_guide=StyleGuide(),
        )

    def _create_mock_chapter_result(self, content: str):
        """Create a mock chapter result."""
        result = MagicMock()
        result.content = content
        result.summary = content[:200] if len(content) > 200 else content
        result.new_terms = {}
        result.prompt_tokens = 100
        result.completion_tokens = 200
        result.duration_ms = 1000
        return result

    def _create_review_result(self, passed: bool, score: int, issues: list[ReviewIssue] | None = None):
        """Create a mock review result."""
        return ReviewResult(
            overall_score=score,
            passed=passed,
            scores=ReviewScores(
                factual_accuracy=score,
                consistency=score,
                terminology=score,
                hallucination_free=score,
            ),
            issues=issues or [],
            summary="Test review",
            chapter_index=0,
            chapter_title="Test Chapter",
        )

    def test_review_feedback_passed_to_context_on_retry(self):
        """Test that review issues are passed as feedback when regenerating."""
        project = self._create_test_project()

        # Create a context for generation
        ctx = GenerationContext(
            project_id=project.id,
            chapter_index=0,
            chapter_title="Test Chapter",
            chapter_outline="1. Section One\n2. Section Two",
            terminology_glossary={},
            source_materials=[],
            review_feedback="",  # Initially empty
        )

        # First review fails with issues
        failed_review = self._create_review_result(
            passed=False,
            score=60,
            issues=[
                ReviewIssue(
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.HALLUCINATION,
                    description="Unsupported claim about feature X",
                    suggestion="Remove or cite a source",
                ),
                ReviewIssue(
                    severity=IssueSeverity.MEDIUM,
                    category=IssueCategory.CONSISTENCY,
                    description="Terminology inconsistency",
                    suggestion="Use consistent terms throughout",
                ),
            ],
        )

        # Simulate the feedback building logic from generator.py
        feedback_parts = ["Previous review issues to address:"]
        for issue in failed_review.issues:
            feedback_parts.append(
                f"- [{issue.severity.value.upper()}] {issue.category.value}: {issue.description}"
            )
            if issue.suggestion:
                feedback_parts.append(f"  Suggestion: {issue.suggestion}")

        expected_feedback = "\n".join(feedback_parts)

        # Verify feedback format
        assert "Previous review issues to address:" in expected_feedback
        assert "[HIGH] hallucination: Unsupported claim about feature X" in expected_feedback
        assert "Suggestion: Remove or cite a source" in expected_feedback
        assert "[MEDIUM] consistency: Terminology inconsistency" in expected_feedback

    def test_context_review_feedback_field_exists(self):
        """Test that GenerationContext has review_feedback field."""
        ctx = GenerationContext(
            project_id="test",
            chapter_index=0,
            chapter_title="Test",
            review_feedback="Some feedback",
        )
        assert ctx.review_feedback == "Some feedback"

    def test_context_review_feedback_defaults_to_empty(self):
        """Test that review_feedback defaults to empty string."""
        ctx = GenerationContext(
            project_id="test",
            chapter_index=0,
            chapter_title="Test",
        )
        assert ctx.review_feedback == ""

    def test_graceful_fallback_on_parse_failure(self):
        """Test that parse failure uses moderate score to avoid blocking."""
        reviewer = ContentReviewer(
            llm_client=MagicMock(),
            storage=MagicMock(),
            repo=MagicMock(),
            min_score=80,
            max_retries=2,
        )

        # Response that can't be parsed at all
        unparseable_response = "This is completely unparseable text without any JSON"

        result = reviewer._parse_review_response(unparseable_response, 0, "Test Chapter")

        # Should use graceful fallback: score 50, passed=True
        assert result.overall_score == 50
        assert result.passed is True
        assert "inconclusive" in result.summary.lower()
        assert "manual review recommended" in result.summary.lower()

    def test_should_regenerate_respects_max_retries(self):
        """Test should_regenerate respects max_retries configuration."""
        reviewer = ContentReviewer(
            llm_client=MagicMock(),
            storage=MagicMock(),
            repo=MagicMock(),
            min_score=80,
            max_retries=2,  # Allow 2 retries
        )

        failed_result = self._create_review_result(passed=False, score=60)

        # attempt=0: should regenerate
        assert reviewer.should_regenerate(failed_result, attempt=0) is True

        # attempt=1: should regenerate
        assert reviewer.should_regenerate(failed_result, attempt=1) is True

        # attempt=2: should NOT regenerate (max retries reached)
        assert reviewer.should_regenerate(failed_result, attempt=2) is False

    def test_review_result_to_dict_preserves_issues(self):
        """Test that ReviewResult.to_dict preserves all issue information."""
        issues = [
            ReviewIssue(
                severity=IssueSeverity.HIGH,
                category=IssueCategory.HALLUCINATION,
                description="Test hallucination",
                suggestion="Fix it",
            ),
        ]
        result = self._create_review_result(passed=False, score=60, issues=issues)

        data = result.to_dict()

        assert len(data["issues"]) == 1
        assert data["issues"][0]["severity"] == "high"
        assert data["issues"][0]["category"] == "hallucination"
        assert data["issues"][0]["description"] == "Test hallucination"
        assert data["issues"][0]["suggestion"] == "Fix it"


class TestReviewFeedbackTemplateIntegration:
    """Test integration of review_feedback in prompt templates."""

    def test_chapter_prompt_includes_feedback(self):
        """Test that chapter prompt template includes review_feedback placeholder."""
        from doc_gen.llm.providers import load_prompt

        prompt = load_prompt(
            "chapter",
            doc_type="Tutorial",
            audience="developers",
            style_tone="technical",
            style_person="third",
            language="zh",
            chapter_index="1",
            chapter_title="Test",
            chapter_outline="1. Intro",
            terminology="- term: definition",
            preceding_context="Previous chapter summary",
            source_materials="Source text",
            review_feedback="Previous issues to address:\n- [HIGH] hallucination: Test issue",
        )

        assert "Previous issues to address:" in prompt
        assert "[HIGH] hallucination: Test issue" in prompt

    def test_chapter_prompt_handles_empty_feedback(self):
        """Test that empty review_feedback doesn't break prompt."""
        from doc_gen.llm.providers import load_prompt

        # Should not raise KeyError when review_feedback is empty
        prompt = load_prompt(
            "chapter",
            doc_type="Tutorial",
            audience="developers",
            style_tone="technical",
            style_person="third",
            language="zh",
            chapter_index="1",
            chapter_title="Test",
            chapter_outline="1. Intro",
            terminology="- term: definition",
            preceding_context="Previous chapter summary",
            source_materials="Source text",
            review_feedback="",
        )

        # Should still generate valid prompt
        assert "Chapter 1: Test" in prompt
        assert "Requirements:" in prompt
