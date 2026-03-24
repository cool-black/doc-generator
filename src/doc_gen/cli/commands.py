"""CLI command implementations."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from doc_gen.cli.prompts import (
    prompt_audience,
    prompt_doc_type,
    prompt_domain,
    prompt_files,
    prompt_granularity,
    prompt_language,
    prompt_outline_action,
)
from doc_gen.config.loader import CONFIG_FILE, ensure_data_dir, load_config, save_config
from doc_gen.config.models import AppConfig, LLMProvider
from doc_gen.core.generator import DocumentGenerator
from doc_gen.models.project import ProjectConfig, ProjectStatus
from doc_gen.storage.database import Database
from doc_gen.storage.project import ProjectStorage
from doc_gen.storage.repository import ProjectRepository

# Persistent event loop to avoid "Event loop is closed" on Windows
_loop: asyncio.AbstractEventLoop | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
    return _loop


def run_async(coro):  # type: ignore
    return _get_loop().run_until_complete(coro)


def _get_services(app_config: AppConfig | None = None) -> tuple[AppConfig, ProjectRepository, ProjectStorage]:
    """Initialize shared services."""
    config = app_config or load_config()
    data_dir = ensure_data_dir(config)
    db = Database(data_dir / "db.sqlite")
    repo = ProjectRepository(db)
    storage = ProjectStorage(data_dir)
    return config, repo, storage


def cmd_init() -> None:
    """Initialize configuration interactively."""
    config = load_config()

    click.echo("DocGen Configuration")
    click.echo("=" * 40)

    # Provider selection
    providers = [p.value for p in LLMProvider]
    click.echo("\nLLM Providers:")
    for i, p in enumerate(providers, 1):
        click.echo(f"  {i}. {p}")
    idx = click.prompt(
        "Select provider",
        type=click.IntRange(1, len(providers)),
        default=providers.index(config.llm.provider.value) + 1,
    )
    config.llm.provider = LLMProvider(providers[idx - 1])

    # API key
    current_key = config.llm.api_key
    masked = f"...{current_key[-4:]}" if len(current_key) > 4 else "(not set)"
    click.echo(f"\nCurrent API key: {masked}")
    new_key = click.prompt("API key", default=current_key, show_default=False)
    config.llm.api_key = new_key

    # Model
    default_model = config.llm.get_model()
    config.llm.model = click.prompt("Model", default=default_model)

    # Base URL (optional)
    config.llm.base_url = click.prompt("Custom base URL (optional)", default=config.llm.base_url)

    save_config(config)
    click.echo(f"\nConfiguration saved to {CONFIG_FILE}")


def cmd_new(name: str) -> None:
    """Create a new project interactively."""
    config, repo, storage = _get_services()

    # Check for duplicate name
    existing = repo.get_by_name(name)
    if existing:
        click.echo(f"Error: Project '{name}' already exists.")
        raise SystemExit(1)

    click.echo(f"\nCreating project: {name}")
    click.echo("-" * 40)

    domain = prompt_domain()
    doc_type = prompt_doc_type()
    audience = prompt_audience()
    granularity = prompt_granularity()
    language = prompt_language()

    project = ProjectConfig(
        name=name,
        domain=domain,
        doc_type=doc_type,
        audience=audience,
        granularity=granularity,
        language=language,
    )

    # Create directory structure
    project_path = storage.create_project_dirs(project.id)

    # Upload files
    upload_dir = project_path / "sources" / "uploaded"
    user_files = prompt_files(upload_dir)
    project.user_files = user_files

    # Save
    repo.create(project)
    storage.save_meta(project)

    click.echo(f"\nProject '{name}' created (ID: {project.id})")
    click.echo(f"Next: doc-gen generate {name} --stage outline")


def cmd_list() -> None:
    """List all projects."""
    _, repo, _ = _get_services()
    projects = repo.list_all()

    if not projects:
        click.echo("No projects found. Create one with: doc-gen new <name>")
        return

    click.echo(f"\n{'Name':<20} {'Status':<20} {'Domain':<30} {'Created'}")
    click.echo("-" * 80)
    for p in projects:
        created = p.created_at.strftime("%Y-%m-%d %H:%M")
        click.echo(f"{p.name:<20} {p.status.value:<20} {p.domain[:30]:<30} {created}")


def cmd_status(name: str) -> None:
    """Show project status."""
    _, repo, storage = _get_services()
    project = repo.get_by_name(name)
    if not project:
        click.echo(f"Error: Project '{name}' not found.")
        raise SystemExit(1)

    click.echo(f"\nProject: {project.name}")
    click.echo(f"ID: {project.id}")
    click.echo(f"Status: {project.status.value}")
    click.echo(f"Domain: {project.domain}")
    click.echo(f"Type: {project.doc_type.value}")
    click.echo(f"Audience: {project.audience}")
    click.echo(f"Granularity: {project.granularity.value}")
    click.echo(f"Language: {project.language.value}")
    click.echo(f"Created: {project.created_at}")
    click.echo(f"Updated: {project.updated_at}")
    click.echo(f"Files: {len(project.user_files)}")

    chapters = storage.load_chapters(project.id)
    click.echo(f"Chapters: {len(chapters)}")


def cmd_generate(name: str, stage: str) -> None:
    """Generate outline or content."""
    app_config, repo, storage = _get_services()
    project = repo.get_by_name(name)
    if not project:
        click.echo(f"Error: Project '{name}' not found.")
        raise SystemExit(1)

    # Validate API key
    if not app_config.llm.api_key:
        click.echo("Error: No API key configured. Run: doc-gen init")
        raise SystemExit(1)

    generator = DocumentGenerator(app_config, repo, storage)

    if stage in ("outline", "all"):
        _generate_outline(generator, project)
        # Reload project after status update
        project = repo.get_by_name(name)
        if not project:
            return

    if stage in ("content", "all"):
        if project.status not in (ProjectStatus.OUTLINE_CONFIRMED, ProjectStatus.COMPLETED):
            if stage == "content":
                click.echo("Error: Outline not confirmed. Run: doc-gen generate <name> --stage outline")
                raise SystemExit(1)
        _generate_content(generator, project)

    run_async(generator.close())


def _generate_outline(generator: DocumentGenerator, project: ProjectConfig) -> None:
    """Handle outline generation with user interaction loop."""
    while True:
        click.echo("\nGenerating outline...")
        outline_md = run_async(generator.generate_outline(project))

        click.echo("\n" + "=" * 60)
        click.echo(outline_md)
        click.echo("=" * 60)

        action = prompt_outline_action()
        if action == "confirm":
            project.status = ProjectStatus.OUTLINE_CONFIRMED
            generator.repo.update(project)
            click.echo("Outline confirmed.")
            # Reload project to ensure status is persisted
            project = generator.repo.get_by_name(project.name)
            break
        elif action == "regenerate":
            click.echo("Regenerating...")
            continue
        else:
            click.echo("Cancelled.")
            raise SystemExit(0)


def _generate_content(generator: DocumentGenerator, project: ProjectConfig) -> None:
    """Handle content generation."""
    click.echo("\nGenerating chapters...")
    chapter_files = run_async(generator.generate_content(project))
    click.echo(f"\n{len(chapter_files)} chapters generated.")
    click.echo(f"Next: doc-gen export {project.name}")


def cmd_export(name: str, output_format: str) -> None:
    """Export document."""
    app_config, repo, storage = _get_services()
    project = repo.get_by_name(name)
    if not project:
        click.echo(f"Error: Project '{name}' not found.")
        raise SystemExit(1)

    generator = DocumentGenerator(app_config, repo, storage)
    output_path = generator.export_document(project, output_format)
    click.echo(f"Document exported to: {output_path}")


def cmd_delete(name: str) -> None:
    """Delete a project."""
    _, repo, storage = _get_services()
    project = repo.get_by_name(name)
    if not project:
        click.echo(f"Error: Project '{name}' not found.")
        raise SystemExit(1)

    if not click.confirm(f"Delete project '{name}'?"):
        return

    storage.delete_project(project.id)
    repo.delete(project.id)
    click.echo(f"Project '{name}' deleted.")
