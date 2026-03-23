"""Interactive CLI prompts."""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from doc_gen.models.project import DocumentType, Granularity


def prompt_domain() -> str:
    return click.prompt("Domain/topic of the document", type=str)


def prompt_doc_type() -> DocumentType:
    choices = [dt.value for dt in DocumentType]
    click.echo("\nDocument types:")
    for i, dt in enumerate(DocumentType, 1):
        click.echo(f"  {i}. {dt.value.replace('_', ' ').title()}")
    idx = click.prompt("Select document type", type=click.IntRange(1, len(choices)), default=1)
    return DocumentType(choices[idx - 1])


AUDIENCE_OPTIONS = [
    ("beginner", "无基础入门者"),
    ("intermediate", "有一定基础的开发者"),
    ("advanced", "有经验的专业人员"),
    ("expert", "领域专家/研究人员"),
]


def prompt_audience() -> str:
    click.echo("\nTarget audience:")
    for i, (_, label) in enumerate(AUDIENCE_OPTIONS, 1):
        click.echo(f"  {i}. {label}")
    idx = click.prompt(
        "Select target audience",
        type=click.IntRange(1, len(AUDIENCE_OPTIONS)),
        default=2,
    )
    key, label = AUDIENCE_OPTIONS[idx - 1]
    return label


def prompt_granularity() -> Granularity:
    choices = [g.value for g in Granularity]
    click.echo("\nGranularity levels:")
    for i, g in enumerate(Granularity, 1):
        click.echo(f"  {i}. {g.value.replace('_', ' ').title()}")
    idx = click.prompt("Select granularity", type=click.IntRange(1, len(choices)), default=2)
    return Granularity(choices[idx - 1])


def prompt_files(project_upload_dir: Path) -> list[str]:
    """Ask user to provide file paths for upload."""
    files: list[str] = []
    if not click.confirm("Upload reference files?", default=False):
        return files

    click.echo("Enter file paths (empty line to finish):")
    while True:
        path_str = click.prompt("File path", default="", show_default=False)
        if not path_str:
            break
        src = Path(path_str).expanduser()
        if not src.exists():
            click.echo(f"  File not found: {src}")
            continue
        dst = project_upload_dir / src.name
        shutil.copy2(src, dst)
        files.append(str(dst))
        click.echo(f"  Uploaded: {src.name}")

    return files


def prompt_outline_action() -> str:
    """Ask user what to do with generated outline."""
    click.echo("\nOptions:")
    click.echo("  1. Confirm and proceed")
    click.echo("  2. Regenerate outline")
    click.echo("  3. Cancel")
    choice = click.prompt("Choose", type=click.IntRange(1, 3), default=1)
    return {1: "confirm", 2: "regenerate", 3: "cancel"}[choice]
