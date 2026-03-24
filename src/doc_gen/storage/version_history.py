"""Project version history management for snapshots and rollbacks."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from doc_gen.storage.database import Database
from doc_gen.storage.project import ProjectStorage


@dataclass
class VersionInfo:
    """Information about a saved version."""

    id: str
    project_id: str
    name: str
    description: str
    created_at: datetime
    auto: bool = False
    chapter_count: int = 0


@dataclass
class VersionDiff:
    """Difference between two versions."""

    old_outline: str
    new_outline: str
    old_chapters: dict[str, str] = field(default_factory=dict)
    new_chapters: dict[str, str] = field(default_factory=dict)
    has_changes: bool = False


class VersionHistory:
    """Manages version snapshots for projects."""

    def __init__(self, db: Database, storage: ProjectStorage) -> None:
        self.db = db
        self.storage = storage
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema for version history."""
        self.db.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_versions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                auto BOOLEAN DEFAULT FALSE,
                chapter_count INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """
        )
        self.db.conn.commit()

    def create_version(
        self,
        project_id: str,
        name: str,
        description: str = "",
        auto: bool = False,
    ) -> VersionInfo:
        """Create a new version snapshot.

        Args:
            project_id: Project ID
            name: Version name (e.g., "v1.0")
            description: Version description
            auto: Whether this is an auto-generated version

        Returns:
            VersionInfo for the created version
        """
        version_id = uuid4().hex[:12]

        # Get chapter count
        chapters = self.storage.load_chapters(project_id)
        chapter_count = len(chapters)

        # Create version snapshot directory
        version_dir = self._version_dir(project_id, version_id)
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy current outline
        outline = self.storage.load_outline(project_id)
        if outline:
            (version_dir / "outline.md").write_text(outline, encoding="utf-8")

        # Copy all chapters
        for filename, content in chapters:
            (version_dir / filename).write_text(content, encoding="utf-8")

        # Save metadata
        meta = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
        }
        (version_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

        # Save to database
        self.db.conn.execute(
            "INSERT INTO project_versions (id, project_id, name, description, auto, chapter_count) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (version_id, project_id, name, description, auto, chapter_count),
        )
        self.db.conn.commit()

        return VersionInfo(
            id=version_id,
            project_id=project_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            auto=auto,
            chapter_count=chapter_count,
        )

    def list_versions(self, project_id: str) -> list[VersionInfo]:
        """List all versions for a project.

        Args:
            project_id: Project ID

        Returns:
            List of VersionInfo, most recent first
        """
        rows = self.db.conn.execute(
            "SELECT id, name, description, created_at, auto, chapter_count "
            "FROM project_versions WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()

        return [
            VersionInfo(
                id=row["id"],
                project_id=project_id,
                name=row["name"],
                description=row["description"] or "",
                created_at=datetime.fromisoformat(row["created_at"]),
                auto=bool(row["auto"]),
                chapter_count=row["chapter_count"],
            )
            for row in rows
        ]

    def get_version(self, version_id: str) -> VersionInfo | None:
        """Get version info by ID.

        Args:
            version_id: Version ID

        Returns:
            VersionInfo or None if not found
        """
        row = self.db.conn.execute(
            "SELECT id, project_id, name, description, created_at, auto, chapter_count "
            "FROM project_versions WHERE id = ?",
            (version_id,),
        ).fetchone()

        if not row:
            return None

        return VersionInfo(
            id=row["id"],
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            auto=bool(row["auto"]),
            chapter_count=row["chapter_count"],
        )

    def restore_version(self, project_id: str, version_id: str) -> bool:
        """Restore project to a specific version.

        Args:
            project_id: Project ID
            version_id: Version ID to restore

        Returns:
            True if restored successfully
        """
        version_dir = self._version_dir(project_id, version_id)
        if not version_dir.exists():
            return False

        # Clear current chapters
        chapters_dir = self.storage.project_dir(project_id) / "chapters"
        if chapters_dir.exists():
            for f in chapters_dir.glob("*.md"):
                f.unlink()

        # Restore outline
        outline_path = version_dir / "outline.md"
        if outline_path.exists():
            outline = outline_path.read_text(encoding="utf-8")
            self.storage.save_outline(project_id, outline)

        # Restore chapters
        for chapter_file in version_dir.glob("*.md"):
            if chapter_file.name == "outline.md":
                continue
            content = chapter_file.read_text(encoding="utf-8")
            # Parse index from filename like "01_intro.md"
            parts = chapter_file.stem.split("_", 1)
            if parts[0].isdigit():
                index = int(parts[0])
                slug = parts[1] if len(parts) > 1 else "chapter"
                self.storage.save_chapter(project_id, index, slug, content)

        return True

    def delete_version(self, version_id: str) -> bool:
        """Delete a version.

        Args:
            version_id: Version ID

        Returns:
            True if deleted successfully
        """
        version = self.get_version(version_id)
        if not version:
            return False

        # Delete from database
        cursor = self.db.conn.execute(
            "DELETE FROM project_versions WHERE id = ?", (version_id,)
        )
        self.db.conn.commit()

        # Delete snapshot directory
        version_dir = self._version_dir(version.project_id, version_id)
        if version_dir.exists():
            shutil.rmtree(version_dir)

        return cursor.rowcount > 0

    def compare_versions(self, old_version_id: str, new_version_id: str) -> VersionDiff:
        """Compare two versions.

        Args:
            old_version_id: Older version ID
            new_version_id: Newer version ID

        Returns:
            VersionDiff with changes
        """
        old_version = self.get_version(old_version_id)
        new_version = self.get_version(new_version_id)

        if not old_version or not new_version:
            raise ValueError("Version not found")

        old_dir = self._version_dir(old_version.project_id, old_version_id)
        new_dir = self._version_dir(new_version.project_id, new_version_id)

        # Load outlines
        old_outline = ""
        new_outline = ""
        if (old_dir / "outline.md").exists():
            old_outline = (old_dir / "outline.md").read_text(encoding="utf-8")
        if (new_dir / "outline.md").exists():
            new_outline = (new_dir / "outline.md").read_text(encoding="utf-8")

        # Load chapters
        old_chapters = self._load_chapters_from_dir(old_dir)
        new_chapters = self._load_chapters_from_dir(new_dir)

        has_changes = (
            old_outline != new_outline or old_chapters != new_chapters
        )

        return VersionDiff(
            old_outline=old_outline,
            new_outline=new_outline,
            old_chapters=old_chapters,
            new_chapters=new_chapters,
            has_changes=has_changes,
        )

    def _version_dir(self, project_id: str, version_id: str) -> Path:
        """Get version snapshot directory path."""
        return (
            self.storage.project_dir(project_id) / "versions" / version_id
        )

    def _load_chapters_from_dir(self, dir_path: Path) -> dict[str, str]:
        """Load chapters from a version directory."""
        chapters = {}
        for f in sorted(dir_path.glob("*.md")):
            if f.name == "outline.md":
                continue
            chapters[f.name] = f.read_text(encoding="utf-8")
        return chapters
