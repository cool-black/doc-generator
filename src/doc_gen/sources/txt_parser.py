"""Text and Markdown file parser."""

from __future__ import annotations

from pathlib import Path


def parse_text_file(path: Path) -> str:
    """Read a text/markdown file and return its content."""
    return path.read_text(encoding="utf-8")
