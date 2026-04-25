"""CLI entry-points for envault."""

from __future__ import annotations

from pathlib import Path

import click

from envault import __version__
from envault.crypto import CryptoError, decrypt_file, encrypt_file
from envault.sharing import (
    SharingError,
    add_recipient,
    get_public_keys,
    list_recipients,
    remove_recipient,
)


@click.group()
@click.version_option(__version__, prog_name="envault")
def main() -> None:
    """envault — encrypt and version .env files with age."""


@main.command()
@click.argument("env_file", type=click.Path(exists=True))
@click.option("-r", "--recipient", multiple=True, help="age public key of a recipient.")
@click.option("--team", "use_team", is_flag=True, default=False, help="Include all team recipients.")
@click.option("-o", "--output", default=None, help="Output path (default: <env_file>.age).")
def encrypt(
    env_file: str,
    recipient: tuple[str, ...],
    use_team: bool,
    output: str | None,
) -> None:
    """Encrypt ENV_FILE with age."""
    recipients = list(recipient)
    if use_team:
        recipients.extend(get_public_keys())
    if not recipients:
        raise click.UsageError("Provide at least one --recipient or use --team.")
    out = output or f"{env_file}.age"
    try:
        encrypt_file(Path(env_file), Path(out), recipients)
    except CryptoError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Encrypted → {out}")


@main.command()
@click.argument("age_file", type=click.Path(exists=True))
@click.option("-i", "--identity", required=True, help="Path to age identity (private key) file.")
@click.option("-o", "--output", default=None, help="Output path (default: strip .age suffix).")
def decrypt(
    age_file: str,
    identity: str,
    output: str | None,
) -> None:
    """Decrypt AGE_FILE with age."""
    out = output or (age_file[:-4] if age_file.endswith(".age") else f"{age_file}.dec")
    try:
        decrypt_file(Path(age_file), Path(out), Path(identity))
    except CryptoError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Decrypted → {out}")


@main.group("team")
def team_group() -> None:
    """Manage team recipients."""


@team_group.command("add")
@click.argument("alias")
@click.argument("public_key")
def team_add(alias: str, public_key: str) -> None:
    """Add ALIAS with PUBLIC_KEY to the team file."""
    try:
        add_recipient(alias, public_key)
    except SharingError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Added recipient '{alias}'.")


@team_group.command("remove")
@click.argument("alias")
def team_remove(alias: str) -> None:
    """Remove ALIAS from the team file."""
    try:
        remove_recipient(alias)
    except SharingError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Removed recipient '{alias}'.")


@team_group.command("list")
def team_list() -> None:
    """List all team recipients."""
    members = list_recipients()
    if not members:
        click.echo("No team recipients configured.")
        return
    for member in members:
        click.echo(f"{member['alias']}: {member['public_key']}")
