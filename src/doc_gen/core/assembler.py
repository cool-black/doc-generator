"""Document assembly - combine chapters into final document."""

from __future__ import annotations

import re
from datetime import datetime


def assemble_document(
    title: str,
    chapters: list[tuple[str, str]],
    metadata: dict[str, str] | None = None,
) -> str:
    """Assemble chapters into a final Markdown document with TOC.

    Args:
        title: Document title.
        chapters: List of (chapter_title, chapter_content).
        metadata: Optional YAML frontmatter fields.
    """
    parts: list[str] = []

    # YAML frontmatter
    meta = metadata or {}
    meta.setdefault("title", title)
    meta.setdefault("generated_at", datetime.now().isoformat())

    parts.append("---")
    for key, value in meta.items():
        parts.append(f"{key}: {value}")
    parts.append("---")
    parts.append("")

    # Title
    parts.append(f"# {title}")
    parts.append("")

    # Table of Contents
    parts.append("## Table of Contents")
    parts.append("")
    for i, (ch_title, _) in enumerate(chapters, 1):
        # Strip number prefix for clean TOC entry
        clean_title = _strip_number_prefix(ch_title)
        anchor = _make_anchor(clean_title)
        parts.append(f"{i}. [{clean_title}](#{anchor})")
    parts.append("")

    # Chapters
    for i, (ch_title, ch_content) in enumerate(chapters, 1):
        # Strip number prefix to avoid duplicate numbering (e.g., "1. 开篇导读" -> "开篇导读")
        clean_title = _strip_number_prefix(ch_title)
        parts.append(f"## {i}. {clean_title}")
        parts.append("")
        parts.append(ch_content.strip())
        parts.append("")

    return "\n".join(parts)


def _make_anchor(text: str) -> str:
    """Convert heading text to Markdown anchor."""
    anchor = text.lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"[\s]+", "-", anchor)
    return anchor


def _strip_number_prefix(title: str) -> str:
    """Strip leading number prefix like '1. ' or '1.1. ' from title."""
    return re.sub(r"^(\d+\.)+\s*", "", title)
