"""Entry-point CLI for envault."""
from __future__ import annotations

import click
from rich.console import Console

from envault import __version__

console = Console()


@click.group()
@click.version_option(__version__, prog_name="envault")
def main() -> None:
    """envault — encrypt and version .env files using age encryption."""


@main.command()
@click.argument("env_file", default=".env", metavar="ENV_FILE")
@click.option(
    "--recipients",
    "-r",
    multiple=True,
    metavar="PUBKEY",
    help="age public key(s) of recipients. May be repeated.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    metavar="OUTPUT",
    help="Output path for the encrypted file (default: <ENV_FILE>.age).",
)
def encrypt(
    env_file: str,
    recipients: tuple[str, ...],
    output: str | None,
) -> None:
    """Encrypt ENV_FILE for one or more age recipients."""
    from envault.crypto import encrypt_file

    if not recipients:
        raise click.UsageError(
            "At least one recipient public key is required (-r / --recipients)."
        )

    out_path = output or f"{env_file}.age"
    encrypt_file(env_file, list(recipients), out_path)
    console.print(f"[green]✓[/green] Encrypted [bold]{env_file}[/bold] → [bold]{out_path}[/bold]")


@main.command()
@click.argument("encrypted_file", metavar="ENCRYPTED_FILE")
@click.option(
    "--identity",
    "-i",
    required=True,
    metavar="IDENTITY_FILE",
    help="Path to the age identity (private key) file.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    metavar="OUTPUT",
    help="Output path for the decrypted file (default: strips .age suffix).",
)
def decrypt(
    encrypted_file: str,
    identity: str,
    output: str | None,
) -> None:
    """Decrypt ENCRYPTED_FILE using an age identity file."""
    from envault.crypto import decrypt_file

    out_path = output or (
        encrypted_file[: -len(".age")] if encrypted_file.endswith(".age") else f"{encrypted_file}.dec"
    )
    decrypt_file(encrypted_file, identity, out_path)
    console.print(f"[green]✓[/green] Decrypted [bold]{encrypted_file}[/bold] → [bold]{out_path}[/bold]")


if __name__ == "__main__":  # pragma: no cover
    main()
