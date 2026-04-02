"""Interactive CLI prompts."""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from doc_gen.models.project import DesignBrief, DocumentType, Granularity, Language


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


LANGUAGE_OPTIONS = [
    ("zh", "简体中文"),
    ("en", "English"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("es", "Español"),
]


def prompt_language() -> Language:
    click.echo("\nDocument language:")
    for i, (_, label) in enumerate(LANGUAGE_OPTIONS, 1):
        click.echo(f"  {i}. {label}")
    idx = click.prompt(
        "Select language",
        type=click.IntRange(1, len(LANGUAGE_OPTIONS)),
        default=1,
    )
    key, _ = LANGUAGE_OPTIONS[idx - 1]
    return Language(key)


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


GOAL_TYPE_OPTIONS = [
    ("intro_guide", "快速入门"),
    ("systematic_guide", "系统学习"),
    ("interview_prep", "面试准备"),
    ("reference_manual", "参考手册"),
]

AUDIENCE_LEVEL_OPTIONS = [
    ("beginner", "初学者"),
    ("intermediate", "进阶读者"),
    ("advanced", "高级读者"),
]

LEARNING_MODE_OPTIONS = [
    ("compact", "紧凑"),
    ("standard", "标准"),
    ("in_depth", "深入"),
]

FOCUS_MODE_OPTIONS = [
    ("concept_heavy", "偏概念理解"),
    ("balanced", "概念与实践平衡"),
    ("practice_heavy", "偏实战应用"),
]

OPTIONAL_MODULES = [
    ("roadmap", "学习路线图"),
    ("interview_highlights", "面试重点"),
    ("glossary", "术语表"),
    ("recap", "章节总结"),
]


def _prompt_option(title: str, options: list[tuple[str, str]], default: int = 1) -> str:
    click.echo(f"\n{title}:")
    for i, (_, label) in enumerate(options, 1):
        click.echo(f"  {i}. {label}")
    idx = click.prompt("Select", type=click.IntRange(1, len(options)), default=default)
    key, _ = options[idx - 1]
    return key


def prompt_design_brief(project_domain: str, current_audience: str) -> DesignBrief:
    click.echo("\nClarify the outline direction before generation.")

    goal_type = _prompt_option("Primary document goal", GOAL_TYPE_OPTIONS, default=2)
    audience_level = _prompt_option("Reader level", AUDIENCE_LEVEL_OPTIONS, default=2)
    learning_mode = _prompt_option("Preferred depth", LEARNING_MODE_OPTIONS, default=2)
    focus_mode = _prompt_option("Concept vs practice", FOCUS_MODE_OPTIONS, default=2)

    selected_modules: list[str] = []
    click.echo("\nOptional modules:")
    for key, label in OPTIONAL_MODULES:
        if click.confirm(f"Include {label}?", default=False):
            selected_modules.append(key)

    scope_guidance = click.prompt(
        "What should this document emphasize most?",
        default=f"Focus on {project_domain} for {current_audience}",
        show_default=True,
    )
    notes = click.prompt("Additional notes (optional)", default="", show_default=False)

    return DesignBrief(
        goal_type=goal_type,
        audience_level=audience_level,
        learning_mode=learning_mode,
        focus_mode=focus_mode,
        selected_modules=selected_modules,
        scope_guidance=scope_guidance,
        notes=notes,
    )


def render_design_brief(brief: DesignBrief) -> str:
    modules = ", ".join(brief.selected_modules) if brief.selected_modules else "none"
    lines = [
        "Design Brief",
        "-" * 40,
        f"Goal Type: {brief.goal_type}",
        f"Audience Level: {brief.audience_level}",
        f"Learning Mode: {brief.learning_mode}",
        f"Focus Mode: {brief.focus_mode}",
        f"Selected Modules: {modules}",
        f"Scope Guidance: {brief.scope_guidance or 'not specified'}",
    ]
    if brief.notes:
        lines.append(f"Notes: {brief.notes}")
    return "\n".join(lines)


def prompt_design_brief_action(has_existing: bool = False) -> str:
    click.echo("\nOptions:")
    if has_existing:
        click.echo("  1. Reuse existing design brief")
        click.echo("  2. Regenerate design brief")
        click.echo("  3. Cancel")
        choice = click.prompt("Choose", type=click.IntRange(1, 3), default=1)
        return {1: "reuse", 2: "regenerate", 3: "cancel"}[choice]

    click.echo("  1. Confirm design brief")
    click.echo("  2. Regenerate design brief")
    click.echo("  3. Cancel")
    choice = click.prompt("Choose", type=click.IntRange(1, 3), default=1)
    return {1: "confirm", 2: "regenerate", 3: "cancel"}[choice]
