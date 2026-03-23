"""Outline generation logic."""

from __future__ import annotations

import re

from doc_gen.llm.client import LLMClient, LLMResponse
from doc_gen.llm.providers import load_prompt
from doc_gen.models.outline import Outline, OutlineSection
from doc_gen.models.project import ProjectConfig
from doc_gen.utils.logger import get_logger

logger = get_logger("outline")


async def generate_outline(
    config: ProjectConfig,
    llm: LLMClient,
    source_texts: list[str] | None = None,
) -> tuple[str, LLMResponse]:
    """Generate a document outline from project config.

    Returns (markdown_outline, llm_response).
    """
    source_context = ""
    if source_texts:
        combined = "\n\n---\n\n".join(source_texts[:5])  # limit to 5 sources
        source_context = f"Reference Materials:\n{combined[:3000]}"

    prompt = load_prompt(
        "outline",
        doc_type=config.doc_type.value.replace("_", " ").title(),
        domain=config.domain,
        audience=config.audience,
        granularity=config.granularity.value.replace("_", " "),
        language=config.language.value,
        source_context=source_context,
    )

    response = await llm.generate(
        prompt=prompt,
        system="You are an expert document architect. Generate clear, well-structured outlines.",
    )

    logger.info("Outline generated: %d tokens", response.completion_tokens)
    return response.content, response


def parse_outline_markdown(markdown: str) -> Outline:
    """Parse a Markdown outline into structured Outline object."""
    lines = markdown.strip().split("\n")
    title = "Document"
    sections: list[OutlineSection] = []
    stack: list[tuple[int, OutlineSection]] = []

    for line in lines:
        line = line.rstrip()
        heading_match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if not heading_match:
            # Append as description to last section
            if stack and line.strip():
                current = stack[-1][1]
                desc = line.strip()
                if current.description:
                    current.description += " " + desc
                else:
                    current.description = desc
            continue

        level = len(heading_match.group(1))
        text = heading_match.group(2).strip()

        if level == 1:
            title = text
            continue

        section = OutlineSection(title=text, level=level - 1)

        # Find parent: pop stack until we find a section with lower level
        while stack and stack[-1][0] >= level - 1:
            stack.pop()

        if stack:
            stack[-1][1].children.append(section)
        else:
            sections.append(section)

        stack.append((level - 1, section))

    return Outline(title=title, sections=sections)
