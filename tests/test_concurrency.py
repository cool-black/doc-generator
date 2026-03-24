"""Tests for SQLite concurrency control."""

from __future__ import annotations

import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from doc_gen.config.models import AppConfig, LLMConfig
from doc_gen.models.project import ProjectConfig, ProjectStatus
from doc_gen.storage.database import Database
from doc_gen.storage.project import ProjectStorage
from doc_gen.storage.repository import ProjectRepository


class TestSQLiteConcurrency:
    """Test SQLite concurrency handling."""

    def test_wal_mode_enabled(self, tmp_path: Path) -> None:
        """Should enable WAL mode for better concurrency."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # Access connection to initialize
        conn = db.conn

        # Check journal mode
        cursor = conn.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]

        assert journal_mode.upper() == "WAL"

    def test_busy_timeout_set(self, tmp_path: Path) -> None:
        """Should set busy timeout to handle lock contention."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        conn = db.conn

        # Check busy timeout
        cursor = conn.execute("PRAGMA busy_timeout")
        timeout = cursor.fetchone()[0]

        assert timeout > 0, "Busy timeout should be set"
        assert timeout >= 5000, "Busy timeout should be at least 5 seconds"

    def test_concurrent_reads(self, tmp_path: Path) -> None:
        """Should handle concurrent read operations."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        repo = ProjectRepository(db)

        # Create some projects
        for i in range(5):
            project = ProjectConfig(
                id=f"test-{i}",
                name=f"Test Project {i}",
            )
            repo.create(project)

        results = []

        def read_projects():
            try:
                projects = repo.list_all()
                results.append(len(projects))
            except Exception as e:
                results.append(str(e))

        # Run concurrent reads
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(read_projects) for _ in range(10)]
            for f in futures:
                f.result()

        # All reads should succeed
        assert all(isinstance(r, int) and r == 5 for r in results), f"Some reads failed: {results}"


class TestDatabaseConnectionManagement:
    """Test database connection lifecycle management."""

    def test_connection_pooling(self, tmp_path: Path) -> None:
        """Should reuse the same connection within the same thread."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # First access creates connection
        conn1 = db.conn
        conn2 = db.conn

        # Should be the same connection object
        assert conn1 is conn2

    def test_close_releases_connection(self, tmp_path: Path) -> None:
        """Should release connection when closed."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # Access connection
        _ = db.conn
        assert db._conn is not None

        # Close should release it
        db.close()
        assert db._conn is None

    def test_reconnect_after_close(self, tmp_path: Path) -> None:
        """Should be able to reconnect after closing."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # Create a project
        repo = ProjectRepository(db)
        project = ProjectConfig(id="test", name="Test")
        repo.create(project)

        # Close connection
        db.close()

        # Reconnect and verify
        project2 = repo.get("test")
        assert project2 is not None
        assert project2.name == "Test"
