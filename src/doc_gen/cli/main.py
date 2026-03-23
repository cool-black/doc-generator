"""CLI entry point using Click."""

from __future__ import annotations

import click

from doc_gen import __version__
from doc_gen.utils.logger import setup_logging


@click.group()
@click.version_option(__version__, prog_name="doc-gen")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """DocGen - Generate comprehensive knowledge documents."""
    setup_logging("DEBUG" if verbose else "INFO")


@cli.command()
def init() -> None:
    """Initialize configuration (API keys, provider settings)."""
    from doc_gen.cli.commands import cmd_init
    cmd_init()


@cli.command("new")
@click.argument("name")
def new_project(name: str) -> None:
    """Create a new documentation project."""
    from doc_gen.cli.commands import cmd_new
    cmd_new(name)


@cli.command("list")
def list_projects() -> None:
    """List all projects."""
    from doc_gen.cli.commands import cmd_list
    cmd_list()


@cli.command()
@click.argument("name")
def status(name: str) -> None:
    """Show project status."""
    from doc_gen.cli.commands import cmd_status
    cmd_status(name)


@cli.command()
@click.argument("name")
@click.option(
    "--stage",
    type=click.Choice(["outline", "content", "all"]),
    default="all",
    help="Generation stage",
)
def generate(name: str, stage: str) -> None:
    """Generate document outline and/or content."""
    from doc_gen.cli.commands import cmd_generate
    cmd_generate(name, stage)


@cli.command()
@click.argument("name")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md"]),
    default="md",
    help="Output format",
)
def export(name: str, output_format: str) -> None:
    """Export generated document."""
    from doc_gen.cli.commands import cmd_export
    cmd_export(name, output_format)


@cli.command()
@click.argument("name")
def delete(name: str) -> None:
    """Delete a project."""
    from doc_gen.cli.commands import cmd_delete
    cmd_delete(name)
