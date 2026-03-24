"""Tests for project status management.

This module tests the state machine transitions for project status,
ensuring that status changes are correctly persisted to the database.
"""

import tempfile
from pathlib import Path

import pytest

from doc_gen.models.project import DocumentType, Granularity, ProjectConfig, ProjectStatus
from doc_gen.storage.database import Database
from doc_gen.storage.repository import ProjectRepository


class TestStatusManagement:
    """Test project status state machine transitions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.db = Database(Path(self.tmpdir) / "test.db")
        self.repo = ProjectRepository(self.db)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.db.close()

    def test_status_outline_confirmed_persisted(self):
        """Test that OUTLINE_CONFIRMED status is correctly saved and reloaded."""
        # Create project
        project = ProjectConfig(
            name="test-project",
            domain="test domain",
            doc_type=DocumentType.TUTORIAL,
            audience="beginners",
            granularity=Granularity.STANDARD,
        )
        self.repo.create(project)

        # Initial status should be CREATED
        assert project.status == ProjectStatus.CREATED

        # Update to OUTLINE_CONFIRMED
        project.status = ProjectStatus.OUTLINE_CONFIRMED
        self.repo.update(project)

        # Reload from database
        reloaded = self.repo.get_by_name("test-project")

        # Status should be persisted correctly
        assert reloaded is not None
        assert reloaded.status == ProjectStatus.OUTLINE_CONFIRMED
        assert reloaded.status.value == "outline_confirmed"

    def test_status_generating_after_content_start(self):
        """Test status transition to GENERATING when content generation starts."""
        # Create project with OUTLINE_CONFIRMED status
        project = ProjectConfig(
            name="test-project",
            domain="test domain",
            doc_type=DocumentType.TUTORIAL,
            audience="beginners",
            granularity=Granularity.STANDARD,
        )
        project.status = ProjectStatus.OUTLINE_CONFIRMED
        self.repo.create(project)

        # Verify initial state
        assert project.status == ProjectStatus.OUTLINE_CONFIRMED

        # Simulate starting content generation
        project.status = ProjectStatus.GENERATING
        self.repo.update(project)

        # Reload and verify
        reloaded = self.repo.get_by_name("test-project")
        assert reloaded.status == ProjectStatus.GENERATING

    def test_status_flow_outline_draft_to_confirmed(self):
        """Test the complete flow: OUTLINE_DRAFT -> OUTLINE_CONFIRMED."""
        project = ProjectConfig(
            name="test-flow",
            domain="test",
            doc_type=DocumentType.LEARNING_GUIDE,
            audience="developers",
            granularity=Granularity.OVERVIEW,
        )
        self.repo.create(project)

        # Simulate outline generation
        project.status = ProjectStatus.OUTLINE_DRAFT
        self.repo.update(project)

        # Verify DRAFT state
        reloaded = self.repo.get_by_name("test-flow")
        assert reloaded.status == ProjectStatus.OUTLINE_DRAFT

        # User confirms outline
        reloaded.status = ProjectStatus.OUTLINE_CONFIRMED
        self.repo.update(reloaded)

        # Verify CONFIRMED state persists after reload
        final = self.repo.get_by_name("test-flow")
        assert final.status == ProjectStatus.OUTLINE_CONFIRMED

    def test_cannot_generate_content_without_outline_confirmed(self):
        """Test that content generation requires OUTLINE_CONFIRMED status."""
        # Create project with CREATED status (not confirmed outline)
        project = ProjectConfig(
            name="unconfirmed",
            domain="test",
            doc_type=DocumentType.LEARNING_GUIDE,
            audience="developers",
            granularity=Granularity.OVERVIEW,
        )
        self.repo.create(project)

        # Verify check logic - simulate step_generate_content check
        assert project.status not in (
            ProjectStatus.OUTLINE_CONFIRMED,
            ProjectStatus.COMPLETED,
        )

        # Simulate the check from step_generate_content
        can_generate = project.status in (
            ProjectStatus.OUTLINE_CONFIRMED,
            ProjectStatus.COMPLETED,
        )
        assert not can_generate

        # Now set to confirmed
        project.status = ProjectStatus.OUTLINE_CONFIRMED
        self.repo.update(project)

        # Reload and verify generation is allowed
        reloaded = self.repo.get_by_name("unconfirmed")
        can_generate = reloaded.status in (
            ProjectStatus.OUTLINE_CONFIRMED,
            ProjectStatus.COMPLETED,
        )
        assert can_generate

    def test_status_not_accidentally_overwritten(self):
        """Test that confirmed status is not accidentally overwritten.

        This regression test verifies the bug fix where outline confirmation
        would not properly persist the OUTLINE_CONFIRMED status.
        """
        project = ProjectConfig(
            name="regression-test",
            domain="test",
            doc_type=DocumentType.LEARNING_GUIDE,
            audience="developers",
            granularity=Granularity.OVERVIEW,
        )
        self.repo.create(project)

        # Simulate: outline generated
        project.status = ProjectStatus.OUTLINE_DRAFT
        self.repo.update(project)

        # Simulate: user confirms outline (with reload pattern from fix)
        reloaded = self.repo.get_by_name("regression-test")
        reloaded.status = ProjectStatus.OUTLINE_CONFIRMED
        self.repo.update(reloaded)

        # Simulate: reload after confirmation (as done in run.py fix)
        after_confirm = self.repo.get_by_name("regression-test")

        # Status should be OUTLINE_CONFIRMED, not OUTLINE_DRAFT or GENERATING
        assert after_confirm.status == ProjectStatus.OUTLINE_CONFIRMED
        assert after_confirm.status != ProjectStatus.OUTLINE_DRAFT
        assert after_confirm.status != ProjectStatus.GENERATING
