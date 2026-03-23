"""Document generation context models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerationContext(BaseModel):
    """Context passed to LLM for each chapter generation."""

    project_id: str
    chapter_index: int
    chapter_title: str
    chapter_outline: str = ""
    outline_summary: str = ""
    preceding_context: str = ""
    terminology_glossary: dict[str, str] = Field(default_factory=dict)
    source_materials: list[str] = Field(default_factory=list)
    style_tone: str = "technical"
    style_person: str = "third"
    audience: str = ""
    doc_type: str = "tutorial"
    language: str = "zh"


class ChapterResult(BaseModel):
    """Result of generating a single chapter."""

    index: int
    title: str
    content: str
    summary: str = ""
    new_terms: dict[str, str] = Field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: int = 0
