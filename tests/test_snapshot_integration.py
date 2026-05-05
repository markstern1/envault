"""Integration tests: snapshot save → list → restore round-trip."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_snapshot import snapshot_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_URL=postgres://localhost/db\nSECRET=hunter2\n")
    return p


@pytest.fixture()
def snap_base(tmp_path: Path) -> Path:
    return tmp_path / ".envault" / "snapshots"


def _invoke(runner, snap_base, args):
    """Patch SNAPSHOT_DIR so tests stay isolated."""
    import envault.snapshot as snap_mod
    import envault.cli_snapshot as cli_mod

    original = snap_mod.SNAPSHOT_DIR
    snap_mod.SNAPSHOT_DIR = str(snap_base)
    try:
        return runner.invoke(snapshot_group, args, catch_exceptions=False)
    finally:
        snap_mod.SNAPSHOT_DIR = original


def test_integration_save_and_list(runner, env_file, snap_base):
    result = _invoke(runner, snap_base, ["save", str(env_file), "baseline", "--note", "first"])
    assert result.exit_code == 0, result.output

    result = _invoke(runner, snap_base, ["list"])
    assert result.exit_code == 0
    assert "baseline" in result.output
    assert "first" in result.output


def test_integration_save_restore_round_trip(runner, env_file, snap_base, tmp_path):
    _invoke(runner, snap_base, ["save", str(env_file), "snap1"])

    dest = tmp_path / "restored.env"
    result = _invoke(runner, snap_base, ["restore", "snap1", str(dest)])
    assert result.exit_code == 0, result.output
    assert dest.read_text() == env_file.read_text()


def test_integration_duplicate_name_fails(runner, env_file, snap_base):
    _invoke(runner, snap_base, ["save", str(env_file), "dup"])
    result = _invoke(runner, snap_base, ["save", str(env_file), "dup"])
    assert result.exit_code != 0
    assert "already exists" in result.output
