"""Tests for project version history functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from doc_gen.models.project import ProjectConfig, ProjectStatus
from doc_gen.storage.database import Database
from doc_gen.storage.project import ProjectStorage
from doc_gen.storage.repository import ProjectRepository
from doc_gen.storage.version_history import VersionHistory


@pytest.fixture
def version_setup(tmp_path: Path) -> tuple[VersionHistory, ProjectRepository, ProjectStorage, str]:
    """Create version history with test project."""
    db_path = tmp_path / "test.db"
    base_dir = tmp_path / "projects"

    db = Database(db_path)
    repo = ProjectRepository(db)
    storage = ProjectStorage(base_dir)
    version_history = VersionHistory(db, storage)

    project = ProjectConfig(
        id="test-project",
        name="Test Project",
        domain="Testing",
        status=ProjectStatus.CREATED,
    )

    repo.create(project)
    storage.create_project_dirs(project.id)

    return version_history, repo, storage, project.id


class TestVersionHistory:
    """Test version history management."""

    def test_create_version(self, version_setup: tuple) -> None:
        """Should create a new version snapshot."""
        version_history, repo, storage, project_id = version_setup

        # Save some content
        storage.save_outline(project_id, "# Test Outline")
        storage.save_chapter(project_id, 1, "intro", "Introduction content")

        # Create version
        version = version_history.create_version(
            project_id,
            name="v1.0",
            description="Initial version",
        )

        assert version.id is not None
        assert version.project_id == project_id
        assert version.name == "v1.0"
        assert version.description == "Initial version"

    def test_list_versions(self, version_setup: tuple) -> None:
        """Should list all versions for a project."""
        import time
        version_history, repo, storage, project_id = version_setup

        # Create multiple versions with delay to ensure ordering
        storage.save_outline(project_id, "# Outline v1")
        version_history.create_version(project_id, "v1.0", "First version")
        time.sleep(0.01)  # Small delay to ensure different timestamps

        storage.save_outline(project_id, "# Outline v2")
        version_history.create_version(project_id, "v1.1", "Second version")

        versions = version_history.list_versions(project_id)

        assert len(versions) == 2
        # Versions should be ordered by creation time (most recent first)
        assert versions[0].created_at >= versions[1].created_at
        version_names = {v.name for v in versions}
        assert version_names == {"v1.0", "v1.1"}

    def test_restore_version(self, version_setup: tuple) -> None:
        """Should restore project to a specific version."""
        version_history, repo, storage, project_id = version_setup

        # Create initial version
        storage.save_outline(project_id, "# Original Outline")
        storage.save_chapter(project_id, 1, "chapter1", "Original content")
        version = version_history.create_version(project_id, "v1.0", "Original")

        # Modify content
        storage.save_outline(project_id, "# Modified Outline")
        storage.save_chapter(project_id, 1, "chapter1", "Modified content")

        # Verify modification
        assert "Modified" in storage.load_outline(project_id)

        # Restore to original version
        version_history.restore_version(project_id, version.id)

        # Verify restoration
        assert "Original" in storage.load_outline(project_id)
        chapters = storage.load_chapters(project_id)
        assert len(chapters) == 1
        assert "Original content" in chapters[0][1]

    def test_version_includes_chapters(self, version_setup: tuple) -> None:
        """Version snapshot should include all chapters."""
        version_history, repo, storage, project_id = version_setup

        # Save multiple chapters
        storage.save_chapter(project_id, 1, "intro", "Intro")
        storage.save_chapter(project_id, 2, "body", "Body content")
        storage.save_chapter(project_id, 3, "conclusion", "Conclusion")

        version = version_history.create_version(project_id, "complete", "All chapters")

        # Verify version captured all chapters
        assert version.chapter_count == 3

        # Verify by comparing restored content
        version_history.restore_version(project_id, version.id)
        restored_chapters = storage.load_chapters(project_id)
        assert len(restored_chapters) == 3

    def test_delete_version(self, version_setup: tuple) -> None:
        """Should delete a version."""
        version_history, repo, storage, project_id = version_setup

        version = version_history.create_version(project_id, "temp", "Temporary")

        # Delete the version
        result = version_history.delete_version(version.id)
        assert result is True

        # Verify deletion
        versions = version_history.list_versions(project_id)
        assert len(versions) == 0

    def test_compare_versions(self, version_setup: tuple) -> None:
        """Should compare two versions and show differences."""
        version_history, repo, storage, project_id = version_setup

        # Create first version
        storage.save_outline(project_id, "# Version 1")
        v1 = version_history.create_version(project_id, "v1.0", "First")

        # Create second version
        storage.save_outline(project_id, "# Version 2")
        v2 = version_history.create_version(project_id, "v2.0", "Second")

        # Compare versions
        diff = version_history.compare_versions(v1.id, v2.id)

        assert diff.has_changes is True
        assert "Version 1" in diff.old_outline
        assert "Version 2" in diff.new_outline

    def test_auto_version_on_generation(self, version_setup: tuple) -> None:
        """Should auto-create version before content generation."""
        version_history, repo, storage, project_id = version_setup

        # Simulate pre-generation versioning
        version_history.create_version(
            project_id,
            name="pre-generation",
            description="Auto-snapshot before content generation",
            auto=True,
        )

        versions = version_history.list_versions(project_id)
        assert len(versions) == 1
        assert versions[0].auto is True
