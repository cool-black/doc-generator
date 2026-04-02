"""Tests for data models."""

from doc_gen.core.assembler import assemble_document
from doc_gen.core.outline import parse_outline_markdown
from doc_gen.models.document import ChapterResult, GenerationContext
from doc_gen.models.outline import Outline, OutlineSection
from doc_gen.models.project import (
    DesignBrief,
    DocumentType,
    Granularity,
    ProjectConfig,
    ProjectStatus,
)
from doc_gen.utils.text import slugify, truncate


class TestProjectModels:
    def test_project_config_defaults(self):
        p = ProjectConfig(name="test")
        assert p.status == ProjectStatus.CREATED
        assert p.doc_type == DocumentType.TUTORIAL
        assert p.granularity == Granularity.STANDARD
        assert len(p.id) == 12

    def test_project_status_values(self):
        assert ProjectStatus.CREATED.value == "created"
        assert ProjectStatus.COMPLETED.value == "completed"

    def test_document_type_values(self):
        assert len(list(DocumentType)) == 6

    def test_granularity_values(self):
        assert len(list(Granularity)) == 4

    def test_design_brief_prompt_context(self):
        brief = DesignBrief(
            goal_type="systematic_guide",
            audience_level="beginner",
            learning_mode="standard",
            focus_mode="balanced",
            selected_modules=["roadmap", "glossary"],
            scope_guidance="Build practical intuition first",
            notes="Prefer short examples",
        )

        context = brief.to_prompt_context()
        assert "Goal Type: systematic_guide" in context
        assert "Selected Modules: roadmap, glossary" in context
        assert "Notes: Prefer short examples" in context


class TestOutlineModels:
    def test_outline_to_markdown(self):
        outline = Outline(
            title="Test Doc",
            sections=[
                OutlineSection(
                    title="Introduction",
                    level=1,
                    children=[
                        OutlineSection(title="Background", level=2),
                    ],
                ),
            ],
        )
        md = outline.to_markdown()
        assert "# Test Doc" in md
        assert "## Introduction" in md
        assert "### Background" in md

    def test_chapter_titles(self):
        outline = Outline(
            title="Doc",
            sections=[
                OutlineSection(title="Ch1", level=1),
                OutlineSection(title="Ch2", level=1),
            ],
        )
        assert outline.chapter_titles() == ["Ch1", "Ch2"]


class TestOutlineParsing:
    def test_parse_simple_outline(self):
        md = """# My Document

## Introduction
An intro chapter.

## Core Concepts

### Types
### Patterns

## Conclusion
"""
        outline = parse_outline_markdown(md)
        assert outline.title == "My Document"
        assert len(outline.sections) == 3
        assert outline.sections[0].title == "Introduction"
        assert outline.sections[0].description == "An intro chapter."
        assert len(outline.sections[1].children) == 2

    def test_parse_empty(self):
        outline = parse_outline_markdown("")
        assert outline.title == "Document"
        assert len(outline.sections) == 0


class TestAssembler:
    def test_assemble_basic(self):
        chapters = [
            ("Introduction", "Welcome to the doc."),
            ("Basics", "Here are the basics."),
        ]
        result = assemble_document("My Doc", chapters)
        assert "# My Doc" in result
        assert "## Table of Contents" in result
        assert "[Introduction]" in result
        assert "## 1. Introduction" in result
        assert "Welcome to the doc." in result


class TestTextUtils:
    def test_slugify(self):
        assert slugify("Hello World!") == "hello_world"
        assert slugify("Chapter 1: Intro") == "chapter_1_intro"
        assert slugify("") == "untitled"

    def test_truncate(self):
        assert truncate("short", 100) == "short"
        long_text = "word " * 200
        result = truncate(long_text, 50)
        assert len(result) <= 55  # 50 + "..."
        assert result.endswith("...")


class TestGenerationContext:
    def test_defaults(self):
        ctx = GenerationContext(
            project_id="abc",
            chapter_index=0,
            chapter_title="Intro",
        )
        assert ctx.style_tone == "technical"
        assert ctx.terminology_glossary == {}


class TestChapterResult:
    def test_creation(self):
        result = ChapterResult(
            index=0,
            title="Intro",
            content="Content here",
        )
        assert result.summary == ""
        assert result.duration_ms == 0
