"""CLI group for the `envault clone` command."""
from __future__ import annotations

from pathlib import Path

import click

from .clone import CloneError, clone_for_recipient


@click.group("clone")
def clone_group() -> None:
    """Clone an encrypted .env file for a different recipient."""


@clone_group.command("run")
@click.argument("encrypted", type=click.Path(exists=True, path_type=Path))
@click.argument("identity", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--recipient",
    "-r",
    required=True,
    help="Age public key of the target recipient.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for the cloned file (default: auto-generated).",
)
@click.option(
    "--actor",
    default="envault",
    show_default=True,
    help="Actor name recorded in the audit log.",
)
def clone_run(
    encrypted: Path,
    identity: Path,
    recipient: str,
    output: Path | None,
    actor: str,
) -> None:
    """Decrypt ENCRYPTED with IDENTITY and re-encrypt for RECIPIENT."""
    try:
        result = clone_for_recipient(
            encrypted_path=encrypted,
            identity_path=identity,
            recipient=recipient,
            output_path=output,
            actor=actor,
        )
    except CloneError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary)
