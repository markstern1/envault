"""CLI commands for template generation."""
from __future__ import annotations

from pathlib import Path

import click

from .template import TemplateError, generate_template


@click.group("template")
def template_group() -> None:
    """Generate .env template files."""


@template_group.command("generate")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path (default: <source>.template).",
)
@click.option(
    "--placeholder",
    "-p",
    default="",
    show_default=True,
    help="Value to use for each variable in the template.",
)
def template_generate(
    source: Path,
    output: Path | None,
    placeholder: str,
) -> None:
    """Generate a .env.template from SOURCE, blanking all values."""
    try:
        dest = generate_template(source, output=output, placeholder=placeholder)
        click.echo(f"Template written to {dest}")
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc
