"""Tests for error recovery and resume functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from doc_gen.config.models import AppConfig, LLMConfig
from doc_gen.core.generator import DocumentGenerator
from doc_gen.models.document import ChapterResult, GenerationContext
from doc_gen.models.outline import Outline, OutlineSection
from doc_gen.models.project import DocumentType, ProjectConfig, ProjectStatus
from doc_gen.storage.database import Database
from doc_gen.storage.project import ProjectStorage
from doc_gen.storage.repository import ProjectRepository


pytestmark = pytest.mark.anyio


@pytest.fixture
def temp_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Create temporary directories for testing."""
    base_dir = tmp_path / "projects"
    db_path = tmp_path / "test.db"
    return base_dir, db_path


@pytest.fixture
def app_config() -> AppConfig:
    """Create test app config."""
    return AppConfig(
        llm=LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key",
        ),
    )


@pytest.fixture
def project(temp_dirs: tuple[Path, Path], app_config: AppConfig) -> tuple[ProjectConfig, ProjectRepository, ProjectStorage]:
    """Create a test project with storage."""
    base_dir, db_path = temp_dirs
    db = Database(db_path)
    repo = ProjectRepository(db)
    storage = ProjectStorage(base_dir)

    project = ProjectConfig(
        id="test-project",
        name="Test Project",
        domain="Testing",
        doc_type=DocumentType.TUTORIAL,
        audience="Developers",
    )

    repo.create(project)
    storage.create_project_dirs(project.id)

    return project, repo, storage


class TestGetLastGeneratedChapter:
    """Test retrieving the last successfully generated chapter index."""

    def test_no_chapters_generated(self, project: tuple[ProjectConfig, ProjectRepository, ProjectStorage]) -> None:
        """Should return -1 when no chapters exist."""
        proj, repo, storage = project

        last_index = storage.get_last_generated_chapter(proj.id)

        assert last_index == -1

    def test_returns_highest_chapter_index(self, project: tuple[ProjectConfig, ProjectRepository, ProjectStorage]) -> None:
        """Should return the highest chapter index from existing files."""
        proj, repo, storage = project

        # Create chapter files with gaps
        storage.save_chapter(proj.id, 1, "intro", "Intro content")
        storage.save_chapter(proj.id, 3, "middle", "Middle content")  # Gap at index 2

        last_index = storage.get_last_generated_chapter(proj.id)

        assert last_index == 3

    def test_ignores_non_numeric_filenames(self, project: tuple[ProjectConfig, ProjectRepository, ProjectStorage]) -> None:
        """Should ignore files that don't follow the numeric naming pattern."""
        proj, repo, storage = project

        storage.save_chapter(proj.id, 1, "intro", "Intro content")
        # Create invalid file
        chapters_dir = storage.project_dir(proj.id) / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)
        (chapters_dir / "invalid_file.md").write_text("Invalid content")

        last_index = storage.get_last_generated_chapter(proj.id)

        assert last_index == 1


class TestResumeFromCheckpoint:
    """Test resuming document generation from a checkpoint."""

    async def test_skip_already_generated_chapters(
        self,
        temp_dirs: tuple[Path, Path],
        app_config: AppConfig,
    ) -> None:
        """Should skip chapters that already exist and continue from next."""
        base_dir, db_path = temp_dirs
        db = Database(db_path)
        repo = ProjectRepository(db)
        storage = ProjectStorage(base_dir)

        project = ProjectConfig(
            id="test-resume",
            name="Test Resume",
            status=ProjectStatus.GENERATING,
        )
        repo.create(project)
        storage.create_project_dirs(project.id)

        # Pre-generate first chapter
        storage.save_chapter(project.id, 1, "chapter-one", "Already generated")

        # Save outline with 3 sections
        outline = Outline(
            title="Test",
            sections=[
                OutlineSection(title="Chapter One", children=[]),
                OutlineSection(title="Chapter Two", children=[]),
                OutlineSection(title="Chapter Three", children=[]),
            ],
        )
        outline_md = "# Test\n\n## Chapter One\n\n## Chapter Two\n\n## Chapter Three"
        storage.save_outline(project.id, outline_md)

        generator = DocumentGenerator(app_config, repo, storage, enable_review=False)

        with patch("doc_gen.core.generator.generate_chapter", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = ChapterResult(
                index=0,
                title="Test",
                content="Generated content",
                summary="Summary",
                prompt_tokens=100,
                completion_tokens=50,
                duration_ms=1000,
                new_terms={},
            )

            await generator.generate_content(project)

            # Should only generate chapters 2 and 3 (indices 1 and 2)
            assert mock_gen.call_count == 2

            # Verify first call is for chapter 2
            first_call_ctx = mock_gen.call_args_list[0][0][0]
            assert first_call_ctx.chapter_index == 1  # Second section (0-indexed)
            assert first_call_ctx.chapter_title == "Chapter Two"

    async def test_regenerate_from_scratch_if_no_chapters(
        self, temp_dirs: tuple[Path, Path], app_config: AppConfig
    ) -> None:
        """Should generate all chapters if none exist."""
        base_dir, db_path = temp_dirs
        db = Database(db_path)
        repo = ProjectRepository(db)
        storage = ProjectStorage(base_dir)

        project = ProjectConfig(
            id="test-full",
            name="Test Full",
            status=ProjectStatus.GENERATING,
        )
        repo.create(project)
        storage.create_project_dirs(project.id)

        outline_md = "# Test\n\n## Chapter One\n\n## Chapter Two"
        storage.save_outline(project.id, outline_md)

        generator = DocumentGenerator(app_config, repo, storage, enable_review=False)

        with patch("doc_gen.core.generator.generate_chapter", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = ChapterResult(
                index=0,
                title="Test",
                content="Generated content",
                summary="Summary",
                prompt_tokens=100,
                completion_tokens=50,
                duration_ms=1000,
                new_terms={},
            )

            await generator.generate_content(project)

            # Should generate both chapters
            assert mock_gen.call_count == 2


class TestContextRestoration:
    """Test that context is properly restored when resuming."""

    async def test_preceding_summary_from_last_generated(
        self, temp_dirs: tuple[Path, Path], app_config: AppConfig
    ) -> None:
        """Should use summary from last generated chapter as preceding context."""
        base_dir, db_path = temp_dirs
        db = Database(db_path)
        repo = ProjectRepository(db)
        storage = ProjectStorage(base_dir)

        project = ProjectConfig(
            id="test-context",
            name="Test Context",
            status=ProjectStatus.GENERATING,
        )
        repo.create(project)
        storage.create_project_dirs(project.id)

        # Save chapter with extractable summary
        chapter_content = """# Chapter One

This is the first chapter with some content that can be summarized.

## Section 1.1

More details here."""
        storage.save_chapter(project.id, 1, "chapter-one", chapter_content)

        outline_md = "# Test\n\n## Chapter One\n\n## Chapter Two"
        storage.save_outline(project.id, outline_md)

        generator = DocumentGenerator(app_config, repo, storage, enable_review=False)

        with patch("doc_gen.core.generator.generate_chapter", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = ChapterResult(
                index=0,
                title="Test",
                content="Generated content",
                summary="Summary",
                prompt_tokens=100,
                completion_tokens=50,
                duration_ms=1000,
                new_terms={},
            )

            await generator.generate_content(project)

            # Verify context passed to chapter 2 generation
            ctx = mock_gen.call_args[0][0]
            assert ctx.preceding_context != ""
            # Should contain summary/excerpt from chapter 1

    async def test_generates_missing_chapter_when_existing_files_have_gaps(
        self, temp_dirs: tuple[Path, Path], app_config: AppConfig
    ) -> None:
        """Should fill missing chapter gaps instead of skipping by max chapter index."""
        base_dir, db_path = temp_dirs
        db = Database(db_path)
        repo = ProjectRepository(db)
        storage = ProjectStorage(base_dir)

        project = ProjectConfig(
            id="test-gap",
            name="Test Gap",
            status=ProjectStatus.GENERATING,
        )
        repo.create(project)
        storage.create_project_dirs(project.id)

        storage.save_chapter(project.id, 1, "chapter-one", "Chapter 1")
        storage.save_chapter(project.id, 3, "chapter-three", "Chapter 3")

        outline_md = "# Test\n\n## Chapter One\n\n## Chapter Two\n\n## Chapter Three"
        storage.save_outline(project.id, outline_md)

        generator = DocumentGenerator(app_config, repo, storage, enable_review=False)

        with patch("doc_gen.core.generator.generate_chapter", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = ChapterResult(
                index=1,
                title="Chapter Two",
                content="Generated chapter 2",
                summary="Summary",
                prompt_tokens=100,
                completion_tokens=50,
                duration_ms=1000,
                new_terms={},
            )

            await generator.generate_content(project)

            assert mock_gen.call_count == 1
            ctx = mock_gen.call_args[0][0]
            assert ctx.chapter_index == 1
            assert ctx.chapter_title == "Chapter Two"
            chapters = storage.load_chapters(project.id)
            assert [name for name, _ in chapters] == [
                "01_chapter-one.md",
                "02_chapter_two.md",
                "03_chapter-three.md",
            ]
