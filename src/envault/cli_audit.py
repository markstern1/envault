"""CLI commands for viewing and querying the audit log."""

import click
from pathlib import Path
from datetime import datetime

from .audit import get_events


@click.group(name="audit")
def audit_group() -> None:
    """View and query the audit log for envault operations."""


@audit_group.command(name="log")
@click.option(
    "--dir",
    "vault_dir",
    default=".",
    show_default=True,
    help="Directory containing the .envault/ folder.",
)
@click.option(
    "--limit",
    default=20,
    show_default=True,
    help="Maximum number of entries to display.",
)
@click.option(
    "--actor",
    default=None,
    help="Filter entries by actor name or key fingerprint.",
)
@click.option(
    "--action",
    default=None,
    help="Filter entries by action type (e.g. encrypt, decrypt, rotate).",
)
@click.option(
    "--json", "as_json",
    is_flag=True,
    default=False,
    help="Output entries as JSON lines.",
)
def audit_log(
    vault_dir: str,
    limit: int,
    actor: str | None,
    action: str | None,
    as_json: bool,
) -> None:
    """Display recent audit log entries."""
    import json as _json

    vault_path = Path(vault_dir)
    events = get_events(vault_path)

    if not events:
        click.echo("No audit events recorded yet.")
        return

    # Apply optional filters
    if actor:
        events = [e for e in events if actor.lower() in (e.get("actor") or "").lower()]
    if action:
        events = [e for e in events if action.lower() in (e.get("action") or "").lower()]

    # Most recent first, then cap
    events = list(reversed(events))[:limit]

    if not events:
        click.echo("No matching audit events found.")
        return

    for entry in events:
        if as_json:
            click.echo(_json.dumps(entry))
        else:
            _print_entry(entry)


def _print_entry(entry: dict) -> None:
    """Pretty-print a single audit log entry to stdout."""
    ts_raw = entry.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(ts_raw)
        ts = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        ts = ts_raw or "unknown time"

    action = entry.get("action", "unknown")
    actor = entry.get("actor") or "<unknown>"
    detail = entry.get("detail") or ""

    line = click.style(f"[{ts}]", fg="cyan") + " " + click.style(action, fg="yellow", bold=True)
    line += f"  actor={actor}"
    if detail:
        line += f"  {detail}"
    click.echo(line)


@audit_group.command(name="clear")
@click.option(
    "--dir",
    "vault_dir",
    default=".",
    show_default=True,
    help="Directory containing the .envault/ folder.",
)
@click.confirmation_option(prompt="This will permanently delete all audit log entries. Continue?")
def audit_clear(vault_dir: str) -> None:
    """Permanently clear all audit log entries."""
    vault_path = Path(vault_dir) / ".envault"
    audit_file = vault_path / "audit.json"

    if not audit_file.exists():
        click.echo("No audit log found — nothing to clear.")
        return

    audit_file.write_text("[]")
    click.echo(click.style("Audit log cleared.", fg="green"))
