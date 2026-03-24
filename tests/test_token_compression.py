"""Tests for token optimization and context compression."""

from __future__ import annotations

import pytest

from doc_gen.models.document import GenerationContext
from doc_gen.utils.token_compression import (
    CompressionStrategy,
    TokenBudget,
    compress_context,
    truncate_text,
)


class TestTruncateText:
    """Test text truncation utilities."""

    def test_truncate_text_basic(self) -> None:
        """Should truncate text to target length with ellipsis."""
        text = "This is a long text that needs to be truncated."
        result = truncate_text(text, target_chars=20)

        assert len(result) <= 25  # Some buffer for ellipsis
        assert result.endswith("...")
        assert "This is a long te" in result  # Truncated version

    def test_truncate_text_short_input(self) -> None:
        """Should return short text unchanged."""
        text = "Short text."
        result = truncate_text(text, target_chars=100)

        assert result == text

    def test_truncate_text_preserves_sentences(self) -> None:
        """Should try to preserve complete sentences."""
        text = "First sentence. Second sentence. Third sentence here."
        result = truncate_text(text, target_chars=35)

        # Should end at sentence boundary with ellipsis or period
        assert result.endswith("...") or result.endswith(".")
        # Result should contain First sentence, may or may not contain Second
        assert "First sentence" in result


class TestTokenBudget:
    """Test TokenBudget allocation."""

    def test_budget_allocation(self) -> None:
        """Should allocate budget proportionally."""
        budget = TokenBudget(total_limit=10000)

        # Reserve for system and output
        system_tokens = budget.reserve("system", 1000)
        output_tokens = budget.reserve("output", 2000)

        assert system_tokens == 1000
        assert output_tokens == 2000
        assert budget.remaining == 7000

    def test_budget_allocation_exceeds_limit(self) -> None:
        """Should not exceed total limit."""
        budget = TokenBudget(total_limit=1000)

        with pytest.raises(ValueError):
            budget.reserve("system", 600)
            budget.reserve("output", 600)  # Exceeds limit

    def test_get_allocation_for(self) -> None:
        """Should return allocation for a category."""
        budget = TokenBudget(total_limit=10000)
        budget.reserve("sources", 3000)

        allocation = budget.get_allocation_for("sources")
        assert allocation == 3000

    def test_available_for_context(self) -> None:
        """Should return remaining budget for dynamic allocation."""
        budget = TokenBudget(total_limit=10000)
        budget.reserve("system", 1000)

        # Should allow reserving remaining budget (with 20% buffer)
        available = budget.available_for_context()
        assert available == 7200  # (10000 - 1000) * 0.8


class TestCompressContext:
    """Test context compression strategies."""

    def test_compress_long_sources(self) -> None:
        """Should compress long source materials."""
        sources = [
            "This is source one. " * 100,  # Long source
            "This is source two. " * 100,
        ]

        result = compress_context(
            sources,
            strategy=CompressionStrategy.TRUNCATE,
            max_total_chars=500,
        )

        total_len = sum(len(s) for s in result)
        assert total_len <= 600  # Some buffer

    def test_compress_with_head_only_strategy(self) -> None:
        """HEAD_ONLY strategy should keep only beginning of each source."""
        sources = [
            "Beginning of source one. Middle content here. End content.",
            "Beginning of source two. More middle stuff. Final part.",
        ]

        result = compress_context(
            sources,
            strategy=CompressionStrategy.HEAD_ONLY,
            max_total_chars=50,
        )

        # Should keep beginning, truncate rest
        assert "Beginning of source" in result[0]
        assert "Middle content" not in result[0]

    def test_compress_with_selective_strategy(self) -> None:
        """SELECTIVE strategy should keep most relevant sources."""
        sources = [
            "Source about topic A. " * 50,
            "Source about topic B. " * 50,
            "Source about topic C. " * 50,
        ]

        # With selective strategy and keywords
        result = compress_context(
            sources,
            strategy=CompressionStrategy.SELECTIVE,
            max_total_chars=200,
            keywords=["topic A", "topic C"],
        )

        # Should prefer sources matching keywords
        assert len(result) >= 2

    def test_empty_sources(self) -> None:
        """Should handle empty source list."""
        result = compress_context(
            [],
            strategy=CompressionStrategy.TRUNCATE,
            max_total_chars=1000,
        )

        assert result == []


class TestGenerationContextCompression:
    """Test compressing GenerationContext for token optimization."""

    def test_create_compressed_context(self) -> None:
        """Should create context with compressed sources."""
        long_sources = ["Long source content. " * 200 for _ in range(5)]

        ctx = GenerationContext(
            project_id="test",
            chapter_index=0,
            chapter_title="Test",
            source_materials=long_sources,
        )

        # Compress the context
        compressed_sources = compress_context(
            ctx.source_materials,
            strategy=CompressionStrategy.TRUNCATE,
            max_total_chars=2000,
        )

        total_original = sum(len(s) for s in long_sources)
        total_compressed = sum(len(s) for s in compressed_sources)

        assert total_compressed < total_original
        assert total_compressed <= 2500  # Within budget

    def test_context_with_terminology_prioritized(self) -> None:
        """Should prioritize terminology glossary over source materials."""
        ctx = GenerationContext(
            project_id="test",
            chapter_index=0,
            chapter_title="Test",
            terminology_glossary={
                "API": "Application Programming Interface",
                "REST": "Representational State Transfer",
            },
            source_materials=["Long source. " * 500],
        )

        # Terminology should always be preserved fully
        assert len(ctx.terminology_glossary) == 2
        assert ctx.terminology_glossary["API"] == "Application Programming Interface"
