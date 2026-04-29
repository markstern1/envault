"""CLI commands for searching .env files."""
from __future__ import annotations

from pathlib import Path
from typing import List

import click

from .search import SearchError, search_files


@click.group("search")
def search_group() -> None:
    """Search keys/values inside .env files."""


@search_group.command("run")
@click.argument("pattern")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--keys-only",
    is_flag=True,
    default=False,
    help="Match against key names only (skip values).",
)
@click.option(
    "--ignore-case", "-i",
    is_flag=True,
    default=False,
    help="Case-insensitive matching.",
)
@click.option(
    "--count",
    is_flag=True,
    default=False,
    help="Print only the total match count.",
)
def search_run(
    pattern: str,
    files: tuple,
    keys_only: bool,
    ignore_case: bool,
    count: bool,
) -> None:
    """Search for PATTERN in one or more .env FILES.

    Values are partially masked in output for safety.
    """
    paths: List[Path] = [Path(f) for f in files]
    try:
        result = search_files(
            paths,
            pattern,
            keys_only=keys_only,
            ignore_case=ignore_case,
        )
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    if count:
        click.echo(str(len(result.matches)))
        return

    if not result.found:
        click.echo("No matches found.")
        raise SystemExit(1)

    for match in result.matches:
        click.echo(str(match))
