"""CLI tests for snapshot commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_snapshot import snapshot_group
from envault.snapshot import SnapshotEntry


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("A=1\n")
    return p


def test_snapshot_save_success(runner, env_file):
    entry = SnapshotEntry(name="v1", source=str(env_file), timestamp="2024-01-01T00:00:00+00:00")
    with patch("envault.cli_snapshot.save_snapshot", return_value=entry) as mock_save:
        result = runner.invoke(snapshot_group, ["save", str(env_file), "v1", "--note", "init"])
    assert result.exit_code == 0
    assert "v1" in result.output
    mock_save.assert_called_once()


def test_snapshot_save_failure(runner, env_file):
    from envault.snapshot import SnapshotError
    with patch("envault.cli_snapshot.save_snapshot", side_effect=SnapshotError("already exists")):
        result = runner.invoke(snapshot_group, ["save", str(env_file), "v1"])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_snapshot_restore_success(runner, tmp_path):
    dest = tmp_path / "out.env"
    with patch("envault.cli_snapshot.restore_snapshot", return_value=dest) as mock_restore:
        result = runner.invoke(snapshot_group, ["restore", "v1", str(dest)])
    assert result.exit_code == 0
    assert "restored" in result.output
    mock_restore.assert_called_once_with("v1", dest)


def test_snapshot_restore_missing(runner, tmp_path):
    from envault.snapshot import SnapshotError
    dest = tmp_path / "out.env"
    with patch("envault.cli_snapshot.restore_snapshot", side_effect=SnapshotError("not found")):
        result = runner.invoke(snapshot_group, ["restore", "ghost", str(dest)])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_snapshot_list_empty(runner):
    with patch("envault.cli_snapshot.list_snapshots", return_value=[]):
        result = runner.invoke(snapshot_group, ["list"])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_snapshot_list_shows_entries(runner):
    entries = [
        SnapshotEntry(name="v1", source=".env", timestamp="2024-01-01T00:00:00+00:00", note="init"),
        SnapshotEntry(name="v2", source=".env", timestamp="2024-06-01T00:00:00+00:00", tags=["prod"]),
    ]
    with patch("envault.cli_snapshot.list_snapshots", return_value=entries):
        result = runner.invoke(snapshot_group, ["list"])
    assert result.exit_code == 0
    assert "v1" in result.output
    assert "v2" in result.output
    assert "prod" in result.output
