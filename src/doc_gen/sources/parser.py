"""File parsing dispatcher."""

from __future__ import annotations

from pathlib import Path

from doc_gen.sources.txt_parser import parse_text_file


def parse_file(path: Path) -> str:
    """Parse a file and return its text content."""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md", ".markdown"):
        return parse_text_file(path)
    raise ValueError(f"Unsupported file type: {suffix}. Supported: .txt, .md")
