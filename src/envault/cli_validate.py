"""CLI commands for env schema validation."""
from __future__ import annotations

from pathlib import Path

import click

from envault.validate import ValidateError, validate_env


@click.group("validate")
def validate_group() -> None:
    """Validate .env files against a JSON schema."""


@validate_group.command("run")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.argument("schema_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Treat warnings as errors.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output results as JSON.",
)
def validate_run(
    env_file: Path,
    schema_file: Path,
    strict: bool,
    as_json: bool,
) -> None:
    """Validate ENV_FILE against SCHEMA_FILE."""
    import json as _json

    try:
        result = validate_env(env_file, schema_file)
    except ValidateError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        payload = [
            {"key": i.key, "message": i.message, "severity": i.severity}
            for i in result.issues
        ]
        click.echo(_json.dumps(payload, indent=2))
    else:
        if not result.issues:
            click.echo(click.style("✓ All checks passed.", fg="green"))
        for issue in result.issues:
            colour = "red" if issue.severity == "error" else "yellow"
            click.echo(click.style(str(issue), fg=colour))

    if not result.ok or (strict and result.warnings()):
        raise SystemExit(1)
