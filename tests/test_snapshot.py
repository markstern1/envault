"""Unit tests for src/envault/snapshot.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.snapshot import (
    SnapshotError,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\nSECRET=abc\n")
    return p


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snapshots"


def test_save_snapshot_creates_index(env_file, snap_dir):
    entry = save_snapshot(env_file, "v1", base_dir=snap_dir)
    assert entry.name == "v1"
    index_file = snap_dir / "index.json"
    assert index_file.exists()
    data = json.loads(index_file.read_text())
    assert len(data) == 1
    assert data[0]["name"] == "v1"


def test_save_snapshot_copies_file(env_file, snap_dir):
    save_snapshot(env_file, "v1", base_dir=snap_dir)
    snap_copy = snap_dir / "v1.env"
    assert snap_copy.exists()
    assert snap_copy.read_text() == env_file.read_text()


def test_save_snapshot_stores_note_and_tags(env_file, snap_dir):
    entry = save_snapshot(env_file, "v1", note="pre-deploy", tags=["prod"], base_dir=snap_dir)
    assert entry.note == "pre-deploy"
    assert entry.tags == ["prod"]


def test_save_snapshot_rejects_duplicate_name(env_file, snap_dir):
    save_snapshot(env_file, "v1", base_dir=snap_dir)
    with pytest.raises(SnapshotError, match="already exists"):
        save_snapshot(env_file, "v1", base_dir=snap_dir)


def test_save_snapshot_rejects_missing_source(tmp_path, snap_dir):
    with pytest.raises(SnapshotError, match="not found"):
        save_snapshot(tmp_path / "missing.env", "v1", base_dir=snap_dir)


def test_save_snapshot_rejects_empty_name(env_file, snap_dir):
    with pytest.raises(SnapshotError, match="must not be empty"):
        save_snapshot(env_file, "   ", base_dir=snap_dir)


def test_restore_snapshot_writes_dest(env_file, snap_dir, tmp_path):
    save_snapshot(env_file, "v1", base_dir=snap_dir)
    dest = tmp_path / "restored.env"
    restore_snapshot("v1", dest, base_dir=snap_dir)
    assert dest.read_text() == env_file.read_text()


def test_restore_snapshot_missing_name(snap_dir, tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot("ghost", tmp_path / "out.env", base_dir=snap_dir)


def test_list_snapshots_returns_all(env_file, snap_dir):
    save_snapshot(env_file, "v1", base_dir=snap_dir)
    save_snapshot(env_file, "v2", note="second", base_dir=snap_dir)
    entries = list_snapshots(base_dir=snap_dir)
    assert len(entries) == 2
    assert {e.name for e in entries} == {"v1", "v2"}


def test_list_snapshots_empty(snap_dir):
    entries = list_snapshots(base_dir=snap_dir)
    assert entries == []
