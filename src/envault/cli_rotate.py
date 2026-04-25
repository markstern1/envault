"""CLI commands for key rotation."""

from __future__ import annotations

from pathlib import Path

import click

from .rotate import rotate_key, list_rotation_history, RotationError


@click.group(name="rotate")
def rotate_group() -> None:
    """Key rotation commands."""


@rotate_group.command("run")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--identity",
    "-i",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the current (old) age private key.",
)
@click.option(
    "--recipient",
    "-r",
    required=True,
    help="New age public key to encrypt for.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path (defaults to overwriting the input file).",
)
@click.option("--actor", default="cli", help="Actor name recorded in the audit log.")
def rotate_run(
    file: Path,
    identity: Path,
    recipient: str,
    output: Path | None,
    actor: str,
) -> None:
    """Re-encrypt FILE with a new recipient key."""
    try:
        result = rotate_key(file, identity, recipient, output=output, actor=actor)
        click.echo(f"Rotated: {result}")
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc


@rotate_group.command("history")
@click.argument("file", type=click.Path(path_type=Path))
def rotate_history(file: Path) -> None:
    """Show rotation/version history for an encrypted FILE."""
    entries = list_rotation_history(file)
    if not entries:
        click.echo("No history found.")
        return
    for entry in entries:
        ts = entry.get("timestamp", "unknown")
        recipient = entry.get("recipient", "unknown")
        sha = entry.get("sha256", "")[:12]
        click.echo(f"{ts}  {sha}  {recipient}")
