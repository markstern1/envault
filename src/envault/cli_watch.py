"""CLI commands for the watch feature."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.audit import record_event
from envault.crypto import encrypt_file
from envault.watch import WatchError, WatchEvent, watch_file


@click.group("watch")
def watch_group() -> None:
    """Watch a .env file and re-encrypt on change."""


@watch_group.command("run")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-r", "--recipient", required=True, help="age recipient public key.")
@click.option(
    "-o",
    "--output",
    "output",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Encrypted output path (default: <env_file>.age).",
)
@click.option("--interval", default=1.0, show_default=True, help="Poll interval in seconds.")
@click.option("--actor", default="cli", hidden=True)
def watch_run(
    env_file: Path,
    recipient: str,
    output: Path | None,
    interval: float,
    actor: str,
) -> None:
    """Watch ENV_FILE and re-encrypt whenever it changes."""
    out = output or env_file.with_suffix(env_file.suffix + ".age")

    click.echo(f"Watching {env_file} → {out}  (Ctrl-C to stop)")

    def _on_change(event: WatchEvent) -> None:
        try:
            encrypt_file(event.path, out, recipient=recipient)
            record_event(
                action="watch:encrypt",
                path=str(event.path),
                actor=actor,
                extra={"checksum": event.checksum, "output": str(out)},
            )
            click.echo(str(event))
        except Exception as exc:  # noqa: BLE001
            click.echo(f"ERROR: {exc}", err=True)

    try:
        watch_file(env_file, _on_change, interval=interval)
    except WatchError as exc:
        click.echo(f"Watch error: {exc}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")
