"""Project CRUD operations via SQLite."""

from __future__ import annotations

import json
from datetime import datetime

from doc_gen.models.project import ProjectConfig, ProjectStatus
from doc_gen.storage.database import Database


class ProjectRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, config: ProjectConfig) -> None:
        self.db.conn.execute(
            "INSERT INTO projects (id, name, created_at, updated_at, status, config_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                config.id,
                config.name,
                config.created_at.isoformat(),
                config.updated_at.isoformat(),
                config.status.value,
                config.model_dump_json(),
            ),
        )
        self.db.conn.commit()

    def get(self, project_id: str) -> ProjectConfig | None:
        row = self.db.conn.execute(
            "SELECT config_json FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            return None
        return ProjectConfig.model_validate_json(row["config_json"])

    def get_by_name(self, name: str) -> ProjectConfig | None:
        row = self.db.conn.execute(
            "SELECT config_json FROM projects WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return ProjectConfig.model_validate_json(row["config_json"])

    def list_all(self) -> list[ProjectConfig]:
        rows = self.db.conn.execute(
            "SELECT config_json FROM projects ORDER BY created_at DESC"
        ).fetchall()
        return [ProjectConfig.model_validate_json(row["config_json"]) for row in rows]

    def update(self, config: ProjectConfig) -> None:
        config.updated_at = datetime.now()
        self.db.conn.execute(
            "UPDATE projects SET name=?, status=?, updated_at=?, config_json=? WHERE id=?",
            (
                config.name,
                config.status.value,
                config.updated_at.isoformat(),
                config.model_dump_json(),
                config.id,
            ),
        )
        self.db.conn.commit()

    def delete(self, project_id: str) -> bool:
        cursor = self.db.conn.execute(
            "DELETE FROM projects WHERE id = ?", (project_id,)
        )
        self.db.conn.commit()
        return cursor.rowcount > 0

    def log_generation(
        self,
        project_id: str,
        chapter_index: int,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: int,
    ) -> None:
        self.db.conn.execute(
            "INSERT INTO generation_logs "
            "(project_id, chapter_index, prompt_tokens, completion_tokens, duration_ms) "
            "VALUES (?, ?, ?, ?, ?)",
            (project_id, chapter_index, prompt_tokens, completion_tokens, duration_ms),
        )
        self.db.conn.commit()
