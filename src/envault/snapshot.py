"""Snapshot management: capture and restore named .env snapshots."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

SNAPSHOT_DIR = ".envault/snapshots"
_INDEX_FILE = "index.json"


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class SnapshotEntry:
    name: str
    source: str
    timestamp: str
    note: str = ""
    tags: List[str] = field(default_factory=list)


def _index_path(base: Path) -> Path:
    return base / _INDEX_FILE


def _load_index(base: Path) -> List[dict]:
    p = _index_path(base)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_index(base: Path, entries: List[dict]) -> None:
    base.mkdir(parents=True, exist_ok=True)
    _index_path(base).write_text(json.dumps(entries, indent=2))


def save_snapshot(
    source: Path,
    name: str,
    note: str = "",
    tags: Optional[List[str]] = None,
    base_dir: Optional[Path] = None,
) -> SnapshotEntry:
    """Copy *source* into the snapshot store under *name*."""
    if not source.exists():
        raise SnapshotError(f"Source file not found: {source}")
    if not name.strip():
        raise SnapshotError("Snapshot name must not be empty.")

    base = Path(base_dir or SNAPSHOT_DIR)
    entries = _load_index(base)

    if any(e["name"] == name for e in entries):
        raise SnapshotError(f"Snapshot '{name}' already exists.")

    dest = base / f"{name}{source.suffix}"
    base.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)

    entry = SnapshotEntry(
        name=name,
        source=str(source),
        timestamp=datetime.now(timezone.utc).isoformat(),
        note=note,
        tags=tags or [],
    )
    entries.append(entry.__dict__)
    _save_index(base, entries)
    return entry


def restore_snapshot(
    name: str,
    dest: Path,
    base_dir: Optional[Path] = None,
) -> Path:
    """Restore snapshot *name* to *dest*."""
    base = Path(base_dir or SNAPSHOT_DIR)
    entries = _load_index(base)
    match = next((e for e in entries if e["name"] == name), None)
    if match is None:
        raise SnapshotError(f"Snapshot '{name}' not found.")

    src = base / f"{name}{Path(match['source']).suffix}"
    if not src.exists():
        raise SnapshotError(f"Snapshot file missing on disk: {src}")

    shutil.copy2(src, dest)
    return dest


def list_snapshots(base_dir: Optional[Path] = None) -> List[SnapshotEntry]:
    """Return all recorded snapshots."""
    base = Path(base_dir or SNAPSHOT_DIR)
    return [SnapshotEntry(**e) for e in _load_index(base)]
