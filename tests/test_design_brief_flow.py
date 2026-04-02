"""Tests for design brief workflow integration."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from doc_gen.cli.commands import _ensure_design_brief
from doc_gen.core.outline import generate_outline
from doc_gen.llm.client import LLMResponse
from doc_gen.models.project import DesignBrief, ProjectConfig
from doc_gen.storage.project import ProjectStorage


def test_outline_prompt_includes_design_brief():
    project = ProjectConfig(
        id="proj1",
        name="Test Project",
        domain="Python",
        audience="developers",
    )
    brief = DesignBrief(
        goal_type="systematic_guide",
        audience_level="beginner",
        learning_mode="standard",
        focus_mode="practice_heavy",
        selected_modules=["roadmap", "recap"],
        scope_guidance="Prioritize hands-on exercises",
    )
    llm = MagicMock()
    llm.generate = AsyncMock(return_value=LLMResponse("# Outline"))

    asyncio.run(generate_outline(project, llm, design_brief=brief))

    prompt = llm.generate.await_args.kwargs["prompt"]
    assert "Design Brief:" in prompt
    assert "Goal Type: systematic_guide" in prompt
    assert "Selected Modules: roadmap, recap" in prompt
    assert "Prioritize hands-on exercises" in prompt


def test_ensure_design_brief_saves_confirmed_brief():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ProjectStorage(Path(tmpdir))
        project = ProjectConfig(id="proj1", name="Test Project", domain="Python", audience="developers")
        storage.create_project_dirs(project.id)
        brief = DesignBrief(scope_guidance="Focus on core concepts")

        with patch("doc_gen.cli.commands.prompt_design_brief", return_value=brief), patch(
            "doc_gen.cli.commands.prompt_design_brief_action",
            side_effect=["confirm"],
        ), patch("click.echo"):
            _ensure_design_brief(storage, project)

        saved = storage.load_design_brief(project.id)
        assert saved is not None
        assert saved.scope_guidance == "Focus on core concepts"


def test_ensure_design_brief_reuses_existing_brief_without_regeneration():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ProjectStorage(Path(tmpdir))
        project = ProjectConfig(id="proj1", name="Test Project", domain="Python", audience="developers")
        storage.create_project_dirs(project.id)
        storage.save_design_brief(project.id, DesignBrief(scope_guidance="Existing brief"))

        with patch("doc_gen.cli.commands.prompt_design_brief") as prompt_brief, patch(
            "doc_gen.cli.commands.prompt_design_brief_action",
            side_effect=["reuse"],
        ), patch("click.echo"):
            _ensure_design_brief(storage, project)

        prompt_brief.assert_not_called()
