"""CLI integration tests for the `envault team` sub-commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from envault.cli import main

FAKE_KEY = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq0ljelq"


def _runner(tmp_path: Path) -> CliRunner:
    """Return a CliRunner that changes to tmp_path so team file is isolated."""
    return CliRunner(mix_stderr=False)


def test_team_add_success(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["team", "add", "alice", FAKE_KEY])
    assert result.exit_code == 0
    assert "Added recipient 'alice'" in result.output


def test_team_add_invalid_key(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["team", "add", "alice", "bad-key"])
    assert result.exit_code != 0
    assert "valid age public key" in result.output


def test_team_remove_success(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ["team", "add", "alice", FAKE_KEY])
        result = runner.invoke(main, ["team", "remove", "alice"])
    assert result.exit_code == 0
    assert "Removed recipient 'alice'" in result.output


def test_team_remove_missing(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["team", "remove", "ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_team_list_empty(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["team", "list"])
    assert result.exit_code == 0
    assert "No team recipients" in result.output


def test_team_list_shows_members(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(main, ["team", "add", "alice", FAKE_KEY])
        result = runner.invoke(main, ["team", "list"])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert FAKE_KEY in result.output
