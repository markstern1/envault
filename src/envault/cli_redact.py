"""CLI commands for redacting sensitive .env values."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from envault.redact import RedactError, redact_file


@click.group("redact")
def redact_group() -> None:
    """Redact sensitive values from .env files."""


@redact_group.command("run")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None, help="Output file (default: stdout)")
@click.option("--placeholder", default="***", show_default=True, help="Replacement text for redacted values")
@click.option("--all", "always_redact", is_flag=True, default=False, help="Redact ALL values, not just sensitive ones")
@click.option("--key", "keys", multiple=True, help="Specific key(s) to redact (repeatable)")
def redact_run(
    env_file: Path,
    output: Optional[Path],
    placeholder: str,
    always_redact: bool,
    keys: tuple,
) -> None:
    """Redact sensitive values in ENV_FILE."""
    try:
        result = redact_file(
            env_file,
            output=output,
            placeholder=placeholder,
            always_redact=always_redact,
            keys=list(keys) if keys else None,
        )
    except RedactError as exc:
        raise click.ClickException(str(exc)) from exc

    if output:
        click.echo(f"Redacted {result.redacted_count} value(s) → {output}")
    else:
        click.echo(result.text)
        if result.redacted_count:
            click.echo(
                f"\n# {result.redacted_count} value(s) redacted",
                err=True,
            )
