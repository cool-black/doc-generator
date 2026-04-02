"""Project domain models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    CREATED = "created"
    OUTLINE_DRAFT = "outline_draft"
    OUTLINE_CONFIRMED = "outline_confirmed"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    COMPLETED = "completed"


class DocumentType(str, Enum):
    TUTORIAL = "tutorial"
    TECHNICAL_MANUAL = "technical_manual"
    ACADEMIC_PAPER = "academic_paper"
    KNOWLEDGE_HANDBOOK = "knowledge_handbook"
    API_DOCUMENTATION = "api_documentation"
    LEARNING_GUIDE = "learning_guide"


class Granularity(str, Enum):
    OVERVIEW = "overview"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    DEEP_DIVE = "deep_dive"


class Language(str, Enum):
    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"


class TermDefinition(BaseModel):
    primary: str
    aliases: list[str] = Field(default_factory=list)
    definition: str = ""


class StyleGuide(BaseModel):
    tone: str = "technical"
    tense: str = "present"
    person: str = "third"


class DesignBrief(BaseModel):
    goal_type: str = "systematic_guide"
    audience_level: str = "intermediate"
    learning_mode: str = "standard"
    focus_mode: str = "balanced"
    selected_modules: list[str] = Field(default_factory=list)
    scope_guidance: str = ""
    notes: str = ""

    def to_prompt_context(self) -> str:
        modules = ", ".join(self.selected_modules) if self.selected_modules else "none"
        lines = [
            f"- Goal Type: {self.goal_type}",
            f"- Audience Level: {self.audience_level}",
            f"- Learning Mode: {self.learning_mode}",
            f"- Focus Mode: {self.focus_mode}",
            f"- Selected Modules: {modules}",
            f"- Scope Guidance: {self.scope_guidance or 'not specified'}",
        ]
        if self.notes:
            lines.append(f"- Notes: {self.notes}")
        return "\n".join(lines)


class ProjectConfig(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: ProjectStatus = ProjectStatus.CREATED

    # Requirements
    domain: str = ""
    doc_type: DocumentType = DocumentType.TUTORIAL
    audience: str = ""
    granularity: Granularity = Granularity.STANDARD
    language: Language = Language.CHINESE

    # Sources
    user_files: list[str] = Field(default_factory=list)

    # Generation settings
    style_guide: StyleGuide = Field(default_factory=StyleGuide)
    terminology: dict[str, TermDefinition] = Field(default_factory=dict)

    # Output settings
    output_dir: Optional[str] = None  # Custom output directory (None = use default)
