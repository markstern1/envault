"""CLI commands for diffing .env versions."""
from __future__ import annotations

import tempfile
from pathlib import Path

import click

from .diff import diff_files, diff_encrypted, DiffError


@click.group(name="diff")
def diff_group() -> None:
    """Compare .env file versions."""


@diff_group.command(name="plain")
@click.argument("old_file", type=click.Path(exists=True, path_type=Path))
@click.argument("new_file", type=click.Path(exists=True, path_type=Path))
@click.option("--no-color", is_flag=True, default=False, help="Disable colour output.")
def diff_plain(old_file: Path, new_file: Path, no_color: bool) -> None:
    """Diff two plain-text .env files."""
    try:
        result = diff_files(old_file, new_file)
    except DiffError as exc:
        raise click.ClickException(str(exc)) from exc

    if not result.has_changes:
        click.echo("No differences found.")
        return

    for line in result.lines:
        if no_color:
            click.echo(line, nl=False)
        elif line.startswith('+') and not line.startswith('+++'):
            click.echo(click.style(line, fg='green'), nl=False)
        elif line.startswith('-') and not line.startswith('---'):
            click.echo(click.style(line, fg='red'), nl=False)
        else:
            click.echo(line, nl=False)


@diff_group.command(name="encrypted")
@click.argument("old_file", type=click.Path(exists=True, path_type=Path))
@click.argument("new_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--identity", "-i",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Age identity file for decryption.",
)
@click.option("--no-color", is_flag=True, default=False, help="Disable colour output.")
def diff_enc(old_file: Path, new_file: Path, identity: Path, no_color: bool) -> None:
    """Decrypt and diff two encrypted .env.age files."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            result = diff_encrypted(old_file, new_file, identity, Path(tmp))
        except DiffError as exc:
            raise click.ClickException(str(exc)) from exc

    if not result.has_changes:
        click.echo("No differences found.")
        return

    for line in result.lines:
        if no_color:
            click.echo(line, nl=False)
        elif line.startswith('+') and not line.startswith('+++'):
            click.echo(click.style(line, fg='green'), nl=False)
        elif line.startswith('-') and not line.startswith('---'):
            click.echo(click.style(line, fg='red'), nl=False)
        else:
            click.echo(line, nl=False)
