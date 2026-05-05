"""CLI commands for snapshot management."""

from __future__ import annotations

from pathlib import Path

import click

from envault.snapshot import SnapshotError, list_snapshots, restore_snapshot, save_snapshot


@click.group("snapshot")
def snapshot_group() -> None:
    """Save and restore named .env snapshots."""


@snapshot_group.command("save")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("name")
@click.option("--note", default="", help="Optional description for this snapshot.")
@click.option("--tag", "tags", multiple=True, help="Tag(s) to attach (repeatable).")
def snapshot_save(source: Path, name: str, note: str, tags: tuple) -> None:
    """Save SOURCE as a named snapshot."""
    try:
        entry = save_snapshot(source, name, note=note, tags=list(tags))
        click.echo(f"Snapshot '{entry.name}' saved at {entry.timestamp}.")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_group.command("restore")
@click.argument("name")
@click.argument("dest", type=click.Path(dir_okay=False, path_type=Path))
def snapshot_restore(name: str, dest: Path) -> None:
    """Restore snapshot NAME to DEST."""
    try:
        out = restore_snapshot(name, dest)
        click.echo(f"Snapshot '{name}' restored to {out}.")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_group.command("list")
def snapshot_list() -> None:
    """List all saved snapshots."""
    snapshots = list_snapshots()
    if not snapshots:
        click.echo("No snapshots found.")
        return
    for s in snapshots:
        tags_str = f"  tags=[{', '.join(s.tags)}]" if s.tags else ""
        note_str = f"  note={s.note!r}" if s.note else ""
        click.echo(f"{s.name}  {s.timestamp}{tags_str}{note_str}")
