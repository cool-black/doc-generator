"""Project file system management."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from doc_gen.models.project import DesignBrief, ProjectConfig


class ProjectStorage:
    """Manages the file system layout for a project."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def project_dir(self, project_id: str) -> Path:
        return self.base_dir / "projects" / project_id

    def create_project_dirs(self, project_id: str) -> Path:
        project_path = self.project_dir(project_id)
        (project_path / "sources" / "uploaded").mkdir(parents=True, exist_ok=True)
        (project_path / "cache").mkdir(parents=True, exist_ok=True)
        (project_path / "chapters").mkdir(parents=True, exist_ok=True)
        (project_path / "output").mkdir(parents=True, exist_ok=True)
        return project_path

    def save_meta(self, config: ProjectConfig) -> None:
        project_path = self.project_dir(config.id)
        meta_file = project_path / "meta.json"
        meta_file.write_text(config.model_dump_json(indent=2), encoding="utf-8")

    def load_meta(self, project_id: str) -> ProjectConfig | None:
        meta_file = self.project_dir(project_id) / "meta.json"
        if not meta_file.exists():
            return None
        return ProjectConfig.model_validate_json(meta_file.read_text(encoding="utf-8"))

    def save_outline(self, project_id: str, content: str) -> Path:
        path = self.project_dir(project_id) / "outline.md"
        path.write_text(content, encoding="utf-8")
        return path

    def load_outline(self, project_id: str) -> str | None:
        path = self.project_dir(project_id) / "outline.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def save_design_brief(self, project_id: str, brief: DesignBrief) -> Path:
        path = self.project_dir(project_id) / "design_brief.json"
        path.write_text(brief.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_design_brief(self, project_id: str) -> DesignBrief | None:
        path = self.project_dir(project_id) / "design_brief.json"
        if not path.exists():
            return None
        return DesignBrief.model_validate_json(path.read_text(encoding="utf-8"))

    def has_design_brief(self, project_id: str) -> bool:
        return (self.project_dir(project_id) / "design_brief.json").exists()

    def save_chapter(self, project_id: str, index: int, slug: str, content: str) -> Path:
        filename = f"{index:02d}_{slug}.md"
        path = self.project_dir(project_id) / "chapters" / filename
        path.write_text(content, encoding="utf-8")
        return path

    def load_chapters(self, project_id: str) -> list[tuple[str, str]]:
        """Return list of (filename, content) sorted by name."""
        chapters_dir = self.project_dir(project_id) / "chapters"
        if not chapters_dir.exists():
            return []
        files = sorted(chapters_dir.glob("*.md"))
        return [(f.name, f.read_text(encoding="utf-8")) for f in files]

    def get_generated_chapter_indices(self, project_id: str) -> set[int]:
        """Return the set of generated chapter numbers (1-based)."""
        chapters_dir = self.project_dir(project_id) / "chapters"
        if not chapters_dir.exists():
            return set()

        indices: set[int] = set()
        for file_path in chapters_dir.glob("*.md"):
            name = file_path.stem
            parts = name.split("_", 1)
            if parts and parts[0].isdigit():
                indices.add(int(parts[0]))
        return indices

    def get_last_generated_chapter(self, project_id: str) -> int:
        """Get the highest chapter index from existing chapter files.

        Returns -1 if no chapters exist.
        Chapter files are named like '01_intro.md', '02_content.md' etc.
        """
        chapters_dir = self.project_dir(project_id) / "chapters"
        if not chapters_dir.exists():
            return -1

        max_index = -1
        for file_path in chapters_dir.glob("*.md"):
            # Extract index from filename like '01_intro.md' -> 1
            name = file_path.stem  # '01_intro'
            parts = name.split("_", 1)  # ['01', 'intro']
            if parts and parts[0].isdigit():
                index = int(parts[0])
                max_index = max(max_index, index)

        return max_index

    def save_output(self, project_id: str, filename: str, content: str) -> Path:
        path = self.project_dir(project_id) / "output" / filename
        path.write_text(content, encoding="utf-8")
        return path

    def delete_project(self, project_id: str) -> None:
        project_path = self.project_dir(project_id)
        if project_path.exists():
            shutil.rmtree(project_path)

    def get_uploaded_files(self, project_id: str) -> list[Path]:
        upload_dir = self.project_dir(project_id) / "sources" / "uploaded"
        if not upload_dir.exists():
            return []
        return list(upload_dir.iterdir())

    def save_review(
        self,
        project_id: str,
        chapter_index: int,
        review_data: dict,
    ) -> Path:
        """Save chapter review results.

        Args:
            project_id: Project ID
            chapter_index: Chapter index (0-based)
            review_data: Review result dictionary

        Returns:
            Path to saved review file
        """
        reviews_dir = self.project_dir(project_id) / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{chapter_index + 1:02d}_review.json"
        path = reviews_dir / filename
        path.write_text(
            json.dumps(review_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def load_reviews(self, project_id: str) -> list[dict]:
        """Load all review results for a project.

        Returns:
            List of review data dictionaries
        """
        reviews_dir = self.project_dir(project_id) / "reviews"
        if not reviews_dir.exists():
            return []

        reviews = []
        for file_path in sorted(reviews_dir.glob("*_review.json")):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                reviews.append(data)
            except (json.JSONDecodeError, IOError):
                continue
        return reviews
