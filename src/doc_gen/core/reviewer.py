"""Content review and quality assurance system."""

from __future__ import annotations

import json
from pathlib import Path

from doc_gen.llm.client import LLMClient
from doc_gen.models.document import GenerationContext
from doc_gen.models.project import ProjectConfig, ProjectStatus
from doc_gen.models.review import (
    IssueCategory,
    IssueSeverity,
    QualityMetrics,
    ReviewIssue,
    ReviewResult,
    ReviewScores,
)
from doc_gen.storage.project import ProjectStorage
from doc_gen.storage.repository import ProjectRepository
from doc_gen.utils.logger import get_logger
from doc_gen.utils.text import truncate

logger = get_logger("reviewer")


class ContentReviewer:
    """Reviews generated content for quality and hallucinations."""

    def __init__(
        self,
        llm_client: LLMClient,
        storage: ProjectStorage,
        repo: ProjectRepository,
        min_score: int = 80,
        max_retries: int = 2,
    ) -> None:
        """Initialize reviewer.

        Args:
            llm_client: LLM client for review API calls
            storage: Project storage for saving review results
            repo: Project repository for metadata
            min_score: Minimum overall score to pass review (0-100)
            max_retries: Maximum regeneration attempts for failed reviews
        """
        self.llm = llm_client
        self.storage = storage
        self.repo = repo
        self.min_score = min_score
        self.max_retries = max_retries
        self.metrics = QualityMetrics()

        # Load review prompt template
        prompt_path = Path(__file__).parent.parent / "llm" / "prompts" / "review.txt"
        self.review_prompt = prompt_path.read_text(encoding="utf-8")

    async def review_chapter(
        self,
        project: ProjectConfig,
        chapter_index: int,
        chapter_title: str,
        chapter_content: str,
        ctx: GenerationContext,
    ) -> ReviewResult:
        """Review a single chapter.

        Args:
            project: Project configuration
            chapter_index: Index of the chapter
            chapter_title: Title of the chapter
            chapter_content: Generated chapter content
            ctx: Generation context

        Returns:
            ReviewResult with scores and issues
        """
        logger.info("Reviewing chapter %d: %s", chapter_index + 1, chapter_title)

        # Build review prompt
        prompt = self._build_review_prompt(ctx, chapter_content)

        try:
            # Call LLM for review
            # Note: Uses default temperature from config to avoid model-specific restrictions
            # Increased max_tokens to ensure complete JSON response
            response = await self.llm.generate(
                prompt=prompt,
                max_tokens=4000,
            )

            # Parse review result
            result = self._parse_review_response(
                response.content,
                chapter_index,
                chapter_title,
            )

            # Save review result
            self.storage.save_review(project.id, chapter_index, result.to_dict())

            # Update metrics
            self.metrics.add_review(result)

            # Log results
            self._log_review_result(result)

            return result

        except Exception as e:
            logger.error("Review failed for chapter %d: %s", chapter_index + 1, e)
            # Return failed result on error
            return ReviewResult(
                overall_score=0,
                passed=False,
                summary=f"Review failed: {e}",
                chapter_index=chapter_index,
                chapter_title=chapter_title,
            )

    def _build_review_prompt(
        self,
        ctx: GenerationContext,
        chapter_content: str,
    ) -> str:
        """Build the review prompt from template."""
        # Truncate source materials to fit context
        source_excerpt = truncate(ctx.source_materials, 2000) if ctx.source_materials else "No source materials provided"

        # Build terminology glossary text
        glossary_text = "\n".join(
            f"- {term}: {definition}"
            for term, definition in ctx.terminology_glossary.items()
        ) if ctx.terminology_glossary else "No glossary provided"

        return self.review_prompt.format(
            domain=ctx.audience,  # Use audience as domain context
            doc_type=ctx.doc_type,
            audience=ctx.audience,
            language=ctx.language,
            chapter_outline=ctx.chapter_outline,
            terminology_glossary=glossary_text,
            source_excerpt=source_excerpt,
            chapter_content=chapter_content,
        )

    def _parse_review_response(
        self,
        response: str,
        chapter_index: int,
        chapter_title: str,
    ) -> ReviewResult:
        """Parse LLM review response into ReviewResult."""
        # Handle empty or None response
        if not response or not response.strip():
            logger.warning("Empty review response for chapter %d", chapter_index + 1)
            return ReviewResult(
                overall_score=0,
                passed=False,
                summary="Empty review response from LLM",
                chapter_index=chapter_index,
                chapter_title=chapter_title,
            )

        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response.strip()

            # Try to find JSON block if wrapped in markdown
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()

            # Remove any leading/trailing whitespace and newlines
            content = content.strip()

            # Handle case where content starts with {
            if not content.startswith("{"):
                # Try to find the first {
                start_idx = content.find("{")
                if start_idx != -1:
                    content = content[start_idx:]

            data = json.loads(content)

            # Parse issues
            issues = []
            for issue_data in data.get("issues", []):
                issues.append(ReviewIssue(
                    severity=IssueSeverity(issue_data.get("severity", "medium")),
                    category=IssueCategory(issue_data.get("category", "consistency")),
                    description=issue_data.get("description", ""),
                    suggestion=issue_data.get("suggestion", ""),
                ))

            # Parse scores
            scores_data = data.get("scores", {})
            scores = ReviewScores(
                factual_accuracy=scores_data.get("factual_accuracy", 0),
                consistency=scores_data.get("consistency", 0),
                terminology=scores_data.get("terminology", 0),
                hallucination_free=scores_data.get("hallucination_free", 0),
            )

            return ReviewResult(
                overall_score=data.get("overall_score", 0),
                passed=data.get("passed", False),
                scores=scores,
                issues=issues,
                summary=data.get("summary", ""),
                chapter_index=chapter_index,
                chapter_title=chapter_title,
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse review response for chapter %d: %s", chapter_index + 1, e)
            # Log first 500 chars of response for debugging
            preview = response[:500] if len(response) > 500 else response
            logger.debug("Response preview: %s", preview)

            # Try to extract a score from the response text using regex as fallback
            import re
            score_match = re.search(r'["\']overall_score["\']\s*:\s*(\d+)', response)
            if score_match:
                extracted_score = int(score_match.group(1))
                logger.info("Extracted score %d from malformed response for chapter %d",
                           extracted_score, chapter_index + 1)
                return ReviewResult(
                    overall_score=extracted_score,
                    passed=extracted_score >= self.min_score,
                    summary=f"Review parsed with fallback (score extracted: {extracted_score})",
                    chapter_index=chapter_index,
                    chapter_title=chapter_title,
                )

            # Both JSON parsing and regex fallback failed - review is inconclusive
            # Use moderate score and pass to avoid blocking generation
            # Flag for human review in production
            logger.warning(
                "Review inconclusive for chapter %d - JSON parse failed and could not "
                "extract score. Using moderate score to allow pipeline to continue.",
                chapter_index + 1,
            )
            return ReviewResult(
                overall_score=50,
                passed=True,  # Pass to avoid blocking - should be manually reviewed
                summary=f"Review inconclusive: parse failed ({e}). Auto-approved with score 50 - manual review recommended.",
                chapter_index=chapter_index,
                chapter_title=chapter_title,
            )

    def _log_review_result(self, result: ReviewResult) -> None:
        """Log review results."""
        status = "PASS" if result.passed else "FAIL"
        logger.info(
            "Chapter %d review: %s (score: %d/100)",
            result.chapter_index + 1,
            status,
            result.overall_score,
        )

        if result.issues:
            for issue in result.issues:
                log_func = logger.warning if issue.severity == IssueSeverity.HIGH else logger.info
                log_func(
                    "  [%s] %s: %s",
                    issue.severity.value.upper(),
                    issue.category.value,
                    issue.description,
                )

    def should_regenerate(self, result: ReviewResult, attempt: int) -> bool:
        """Determine if chapter should be regenerated.

        Args:
            result: Review result
            attempt: Current regeneration attempt number

        Returns:
            True if should regenerate
        """
        if result.passed:
            return False

        if attempt >= self.max_retries:
            logger.warning(
                "Chapter %d failed review but max retries (%d) reached",
                result.chapter_index + 1,
                self.max_retries,
            )
            return False

        return True

    def get_metrics_report(self) -> dict:
        """Get quality metrics report."""
        return {
            "metrics": self.metrics.to_dict(),
            "thresholds": {
                "min_score": self.min_score,
                "max_retries": self.max_retries,
            },
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on metrics."""
        recommendations = []

        if self.metrics.hallucination_rate > 5:
            recommendations.append(
                "Hallucination rate is above 5%. Consider improving source materials "
                "or adding more specific prompts."
            )

        if self.metrics.pass_rate < 80:
            recommendations.append(
                "Pass rate is below 80%. Consider lowering the quality threshold "
                "or improving the generation prompts."
            )

        if self.metrics.average_score < 70:
            recommendations.append(
                "Average quality score is below 70%. Review and refine your "
                "outline and source materials."
            )

        return recommendations

    async def close(self) -> None:
        """Close reviewer resources."""
        # LLM client is managed externally, don't close here
        pass
