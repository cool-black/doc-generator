"""Token optimization and context compression utilities."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any


class CompressionStrategy(Enum):
    """Strategies for compressing context."""

    TRUNCATE = "truncate"  # Simple truncation with ellipsis
    HEAD_ONLY = "head_only"  # Keep only the beginning of each source
    SELECTIVE = "selective"  # Keep sources matching keywords
    SUMMARIZE = "summarize"  # Extract key sentences (placeholder)


def truncate_text(text: str, target_chars: int, preserve_sentences: bool = True) -> str:
    """Truncate text to target length.

    Args:
        text: Text to truncate
        target_chars: Target character count
        preserve_sentences: If True, try to end at sentence boundary

    Returns:
        Truncated text with ellipsis if truncated
    """
    if len(text) <= target_chars:
        return text

    if not preserve_sentences:
        return text[: target_chars - 3].rstrip() + "..."

    # Try to find sentence boundary
    truncated = text[:target_chars]

    # Look for the last sentence ending
    last_period = truncated.rfind(". ")
    last_newline = truncated.rfind("\n\n")

    # Use the later of the two boundaries
    cut_point = max(last_period + 1, last_newline)

    if cut_point > target_chars * 0.5:  # Only use if we keep at least 50%
        return truncated[:cut_point].rstrip() + "..."

    return truncated[: target_chars - 3].rstrip() + "..."


def compress_context(
    sources: list[str],
    strategy: CompressionStrategy = CompressionStrategy.TRUNCATE,
    max_total_chars: int = 8000,
    keywords: list[str] | None = None,
) -> list[str]:
    """Compress source materials to fit within token budget.

    Args:
        sources: List of source material strings
        strategy: Compression strategy to use
        max_total_chars: Maximum total characters for all sources
        keywords: Keywords for SELECTIVE strategy

    Returns:
        List of compressed source strings
    """
    if not sources:
        return []

    # Calculate per-source budget
    per_source_budget = max_total_chars // len(sources)

    if strategy == CompressionStrategy.HEAD_ONLY:
        # Keep only first 30% of each source
        return [_extract_head(s, per_source_budget) for s in sources]

    if strategy == CompressionStrategy.SELECTIVE and keywords:
        # Score and prioritize sources
        scored = [
            (s, _score_relevance(s, keywords)) for s in sources
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Take top sources until budget is filled
        result = []
        remaining_budget = max_total_chars

        for source, score in scored:
            if score == 0:
                continue  # Skip irrelevant sources
            budget = min(per_source_budget, remaining_budget)
            compressed = truncate_text(source, budget)
            result.append(compressed)
            remaining_budget -= len(compressed)

            if remaining_budget < per_source_budget // 2:
                break

        return result if result else [truncate_text(sources[0], max_total_chars)]

    # Default: TRUNCATE - evenly distribute budget
    return [truncate_text(s, per_source_budget) for s in sources]


def _extract_head(text: str, max_chars: int) -> str:
    """Extract the head/introduction of a text."""
    # Take first paragraph or up to max_chars
    paragraphs = text.split("\n\n")
    if paragraphs:
        first_para = paragraphs[0]
        if len(first_para) > max_chars:
            return truncate_text(first_para, max_chars)
        return first_para

    return truncate_text(text, max_chars)


def _score_relevance(text: str, keywords: list[str]) -> int:
    """Score text relevance based on keyword matches."""
    text_lower = text.lower()
    score = 0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        count = text_lower.count(keyword_lower)
        score += count * len(keyword)  # Weight by keyword length
    return score


class TokenBudget:
    """Manages token budget allocation for generation."""

    def __init__(self, total_limit: int = 128000) -> None:
        """Initialize budget with total token limit.

        Args:
            total_limit: Maximum tokens for the entire request
        """
        self.total_limit = total_limit
        self._allocations: dict[str, int] = {}
        self._reserved = 0

    def reserve(self, category: str, tokens: int) -> int:
        """Reserve tokens for a category.

        Args:
            category: Category name (e.g., 'system', 'output')
            tokens: Number of tokens to reserve

        Returns:
            Reserved token count

        Raises:
            ValueError: If reservation exceeds total budget
        """
        if self._reserved + tokens > self.total_limit:
            raise ValueError(
                f"Cannot reserve {tokens} tokens. "
                f"Used: {self._reserved}, Limit: {self.total_limit}"
            )

        self._allocations[category] = tokens
        self._reserved += tokens
        return tokens

    def get_allocation_for(self, category: str) -> int:
        """Get allocated tokens for a category."""
        return self._allocations.get(category, 0)

    @property
    def remaining(self) -> int:
        """Get remaining unallocated tokens."""
        return self.total_limit - self._reserved

    def available_for_context(self) -> int:
        """Get tokens available for context/sources."""
        # Reserve 20% buffer for safety
        return int(self.remaining * 0.8)

    def estimate_chars_for_tokens(self, tokens: int) -> int:
        """Estimate character count for given tokens.

        Uses ~4 chars per token for English text.
        """
        return tokens * 4

    def estimate_tokens_for_text(self, text: str) -> int:
        """Estimate token count for text."""
        return max(1, len(text) // 4)

    def compress_sources_if_needed(
        self,
        sources: list[str],
        strategy: CompressionStrategy = CompressionStrategy.TRUNCATE,
        keywords: list[str] | None = None,
    ) -> list[str]:
        """Compress sources if they exceed available budget.

        Args:
            sources: Source materials
            strategy: Compression strategy
            keywords: Optional keywords for relevance scoring

        Returns:
            Compressed sources
        """
        total_chars = sum(len(s) for s in sources)
        available_chars = self.estimate_chars_for_tokens(self.available_for_context())

        if total_chars <= available_chars:
            return sources  # No compression needed

        return compress_context(
            sources,
            strategy=strategy,
            max_total_chars=available_chars,
            keywords=keywords,
        )
