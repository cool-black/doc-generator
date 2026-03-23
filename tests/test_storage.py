"""Tests for storage layer."""

import tempfile
from pathlib import Path

from doc_gen.models.project import DocumentType, Granularity, ProjectConfig, ProjectStatus
from doc_gen.storage.database import Database
from doc_gen.storage.project import ProjectStorage
from doc_gen.storage.repository import ProjectRepository


def _make_project(name: str = "test-project") -> ProjectConfig:
    return ProjectConfig(
        name=name,
        domain="Python programming",
        doc_type=DocumentType.TUTORIAL,
        audience="beginners",
        granularity=Granularity.STANDARD,
    )


class TestProjectRepository:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db = Database(Path(self.tmpdir) / "test.db")
        self.repo = ProjectRepository(self.db)

    def teardown_method(self):
        self.db.close()

    def test_create_and_get(self):
        project = _make_project()
        self.repo.create(project)
        loaded = self.repo.get(project.id)
        assert loaded is not None
        assert loaded.name == "test-project"
        assert loaded.domain == "Python programming"

    def test_get_by_name(self):
        project = _make_project("my-doc")
        self.repo.create(project)
        loaded = self.repo.get_by_name("my-doc")
        assert loaded is not None
        assert loaded.id == project.id

    def test_get_nonexistent(self):
        assert self.repo.get("nonexistent") is None
        assert self.repo.get_by_name("nonexistent") is None

    def test_list_all(self):
        self.repo.create(_make_project("a"))
        self.repo.create(_make_project("b"))
        projects = self.repo.list_all()
        assert len(projects) == 2

    def test_update(self):
        project = _make_project()
        self.repo.create(project)
        project.status = ProjectStatus.OUTLINE_DRAFT
        self.repo.update(project)
        loaded = self.repo.get(project.id)
        assert loaded is not None
        assert loaded.status == ProjectStatus.OUTLINE_DRAFT

    def test_delete(self):
        project = _make_project()
        self.repo.create(project)
        assert self.repo.delete(project.id)
        assert self.repo.get(project.id) is None
        assert not self.repo.delete("nonexistent")

    def test_log_generation(self):
        project = _make_project()
        self.repo.create(project)
        # Should not raise
        self.repo.log_generation(project.id, 0, 100, 200, 1500)


class TestProjectStorage:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = ProjectStorage(Path(self.tmpdir))

    def test_create_dirs(self):
        path = self.storage.create_project_dirs("proj1")
        assert (path / "sources" / "uploaded").is_dir()
        assert (path / "chapters").is_dir()
        assert (path / "output").is_dir()

    def test_save_and_load_outline(self):
        self.storage.create_project_dirs("proj1")
        self.storage.save_outline("proj1", "# My Outline\n## Chapter 1")
        content = self.storage.load_outline("proj1")
        assert content is not None
        assert "Chapter 1" in content

    def test_load_outline_missing(self):
        self.storage.create_project_dirs("proj1")
        assert self.storage.load_outline("proj1") is None

    def test_save_and_load_chapters(self):
        self.storage.create_project_dirs("proj1")
        self.storage.save_chapter("proj1", 1, "intro", "Introduction content")
        self.storage.save_chapter("proj1", 2, "basics", "Basics content")
        chapters = self.storage.load_chapters("proj1")
        assert len(chapters) == 2
        assert chapters[0][0] == "01_intro.md"
        assert "Introduction" in chapters[0][1]

    def test_save_output(self):
        self.storage.create_project_dirs("proj1")
        path = self.storage.save_output("proj1", "final.md", "# Final doc")
        assert path.exists()
        assert path.read_text() == "# Final doc"

    def test_delete_project(self):
        path = self.storage.create_project_dirs("proj1")
        assert path.exists()
        self.storage.delete_project("proj1")
        assert not path.exists()
