"""Chapter content generation."""

from __future__ import annotations

import time

from doc_gen.llm.client import LLMClient
from doc_gen.llm.providers import load_prompt
from doc_gen.models.document import ChapterResult, GenerationContext
from doc_gen.utils.logger import get_logger

logger = get_logger("content")


async def generate_chapter(
    ctx: GenerationContext,
    llm: LLMClient,
) -> ChapterResult:
    """Generate content for a single chapter."""
    logger.info("Generating chapter %d: %s", ctx.chapter_index + 1, ctx.chapter_title)

    # Build terminology string
    term_lines = [f"- {k}: {v}" for k, v in ctx.terminology_glossary.items()]
    terminology_str = "\n".join(term_lines) if term_lines else "(No glossary yet)"
    logger.debug("  Using %d terminology entries", len(ctx.terminology_glossary))

    # Build source materials string
    source_str = ""
    if ctx.source_materials:
        source_str = "Source Materials:\n" + "\n---\n".join(
            s[:1000] for s in ctx.source_materials[:3]
        )

    prompt = load_prompt(
        "chapter",
        doc_type=ctx.doc_type,
        audience=ctx.audience,
        style_tone=ctx.style_tone,
        style_person=ctx.style_person,
        language=ctx.language,
        chapter_index=str(ctx.chapter_index + 1),
        chapter_title=ctx.chapter_title,
        chapter_outline=ctx.chapter_outline or ctx.chapter_title,
        terminology=terminology_str,
        preceding_context=ctx.preceding_context or "(First chapter)",
        source_materials=source_str,
        review_feedback=ctx.review_feedback,
    )

    logger.debug("  Prompt length: %d chars", len(prompt))

    start = time.monotonic()
    logger.info("  Calling LLM...")
    response = await llm.generate(
        prompt=prompt,
        system="You are an expert technical writer. Write clear, accurate, well-structured content.",
    )
    duration_ms = int((time.monotonic() - start) * 1000)

    logger.info(
        "Chapter %d '%s' generated in %dms",
        ctx.chapter_index + 1,
        ctx.chapter_title,
        duration_ms,
    )

    # Extract a summary (first ~200 chars)
    content = response.content
    summary = content[:200].rsplit(".", 1)[0] + "." if len(content) > 200 else content

    return ChapterResult(
        index=ctx.chapter_index,
        title=ctx.chapter_title,
        content=content,
        summary=summary,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        duration_ms=duration_ms,
    )
