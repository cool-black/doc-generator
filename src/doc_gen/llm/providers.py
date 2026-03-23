"""Prompt template loading."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template and substitute variables."""
    path = PROMPTS_DIR / f"{name}.txt"
    template = path.read_text(encoding="utf-8")
    return template.format(**kwargs) if kwargs else template
