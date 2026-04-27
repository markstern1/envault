"""CLI commands for linting .env files."""
from pathlib import Path

import click

from .lint import lint_file, LintError


@click.group(name="lint")
def lint_group() -> None:
    """Lint .env files for common issues."""


@lint_group.command(name="run")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings as errors.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Only print issues, suppress summary.",
)
def lint_run(env_file: Path, strict: bool, quiet: bool) -> None:
    """Lint ENV_FILE and report issues."""
    try:
        result = lint_file(env_file)
    except LintError as exc:
        raise click.ClickException(str(exc)) from exc

    has_output = False
    for issue in result.issues:
        level = issue.level.upper()
        click.echo(f"[{level}] line {issue.line}: {issue.message}")
        has_output = True

    if not quiet:
        error_count = sum(1 for i in result.issues if i.level == "error")
        warn_count = sum(1 for i in result.issues if i.level == "warning")
        if has_output:
            click.echo(f"\n{error_count} error(s), {warn_count} warning(s).")
        else:
            click.echo("No issues found.")

    if result.has_errors() or (strict and result.has_warnings()):
        raise SystemExit(1)
