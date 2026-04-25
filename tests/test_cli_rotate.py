"""Tests for rotate CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_rotate import rotate_group
from envault.rotate import RotationError


PUBLIC_KEY = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_files(tmp_path: Path):
    enc = tmp_path / "secrets.env.age"
    enc.write_bytes(b"data")
    ident = tmp_path / "key.txt"
    ident.write_text("AGE-SECRET-KEY-1FAKE")
    return enc, ident


def test_rotate_run_success(runner: CliRunner, env_files):
    enc, ident = env_files
    with patch("envault.cli_rotate.rotate_key", return_value=enc) as mock_rot:
        result = runner.invoke(
            rotate_group,
            ["run", str(enc), "--identity", str(ident), "--recipient", PUBLIC_KEY],
        )
    assert result.exit_code == 0
    assert "Rotated" in result.output
    mock_rot.assert_called_once()


def test_rotate_run_failure(runner: CliRunner, env_files):
    enc, ident = env_files
    with patch("envault.cli_rotate.rotate_key", side_effect=RotationError("bad")):
        result = runner.invoke(
            rotate_group,
            ["run", str(enc), "--identity", str(ident), "--recipient", PUBLIC_KEY],
        )
    assert result.exit_code != 0
    assert "bad" in result.output


def test_rotate_history_empty(runner: CliRunner, tmp_path: Path):
    env_file = tmp_path / "secrets.env.age"
    with patch("envault.cli_rotate.list_rotation_history", return_value=[]):
        result = runner.invoke(rotate_group, ["history", str(env_file)])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_rotate_history_with_entries(runner: CliRunner, tmp_path: Path):
    env_file = tmp_path / "secrets.env.age"
    entries = [
        {"timestamp": "2024-01-01T00:00:00", "recipient": PUBLIC_KEY, "sha256": "abc123def456"},
    ]
    with patch("envault.cli_rotate.list_rotation_history", return_value=entries):
        result = runner.invoke(rotate_group, ["history", str(env_file)])
    assert result.exit_code == 0
    assert PUBLIC_KEY in result.output
    assert "abc123def4" in result.output
