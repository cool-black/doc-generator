"""Text processing utilities."""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to a URL/filename-safe slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "_", text).strip("_")
    return text or "untitled"


def truncate(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length, breaking at word boundary."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.5:
        truncated = truncated[:last_space]
    return truncated + "..."
