"""CLI commands for injecting decrypted env vars into a subprocess."""
from __future__ import annotations

from pathlib import Path

import click

from .inject import inject_run, InjectError


@click.group("inject")
def inject_group() -> None:
    """Inject decrypted .env values into a subprocess."""


@inject_group.command("run")
@click.argument("encrypted", type=click.Path(exists=True, path_type=Path))
@click.argument("command", nargs=-1, required=True)
@click.option(
    "--identity",
    "-i",
    default="key.txt",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Path to age identity file.",
)
@click.option(
    "--override",
    is_flag=True,
    default=False,
    help="Override existing environment variables with decrypted values.",
)
@click.option(
    "--set",
    "extra",
    multiple=True,
    metavar="KEY=VALUE",
    help="Additional KEY=VALUE pairs to inject (can be repeated).",
)
@click.option("--quiet", "-q", is_flag=True, default=False)
def inject_cmd(
    encrypted: Path,
    command: tuple[str, ...],
    identity: Path,
    override: bool,
    extra: tuple[str, ...],
    quiet: bool,
) -> None:
    """Decrypt ENCRYPTED and run COMMAND with the env vars injected."""
    extra_env: dict[str, str] = {}
    for item in extra:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item!r}", param_hint="--set")
        k, _, v = item.partition("=")
        extra_env[k.strip()] = v

    try:
        result = inject_run(
            encrypted,
            identity,
            command,
            override=override,
            extra_env=extra_env or None,
        )
    except InjectError as exc:
        raise click.ClickException(str(exc)) from exc

    if not quiet:
        click.echo(
            f"[envault] injected {len(result.injected_keys)} variable(s) "
            f"into: {' '.join(command)}",
            err=True,
        )

    raise SystemExit(result.returncode)
