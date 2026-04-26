"""CLI commands for exporting decrypted .env content."""

from __future__ import annotations

from pathlib import Path

import click

from .crypto import decrypt_file, CryptoError
from .export import export_env, ExportError


@click.group("export")
def export_group() -> None:
    """Export decrypted .env values in various formats."""


@export_group.command("run")
@click.argument("encrypted_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--identity",
    "-i",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="age identity (private key) file.",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["shell", "dotenv", "json"]),
    default="shell",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write output to file instead of stdout.",
)
def export_run(
    encrypted_file: Path,
    identity: Path,
    fmt: str,
    output: Path | None,
) -> None:
    """Decrypt ENCRYPTED_FILE and print its contents in FORMAT."""
    tmp = encrypted_file.with_suffix(".env.tmp")
    try:
        decrypt_file(str(encrypted_file), str(tmp), str(identity))
        plaintext = tmp.read_text(encoding="utf-8")
        result = export_env(plaintext, fmt)  # type: ignore[arg-type]
        if output:
            output.write_text(result + "\n", encoding="utf-8")
            click.echo(f"Exported to {output}")
        else:
            click.echo(result)
    except (CryptoError, ExportError) as exc:
        raise click.ClickException(str(exc)) from exc
    finally:
        if tmp.exists():
            tmp.unlink()
