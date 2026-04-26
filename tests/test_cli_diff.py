"""Tests for the diff CLI commands."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_diff import diff_group
from envault.diff import DiffResult, DiffError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_files(tmp_path: Path):
    old = tmp_path / "old.env"
    new = tmp_path / "new.env"
    old.write_text("FOO=1\n")
    new.write_text("FOO=2\n")
    return old, new


def test_diff_plain_shows_changes(runner, env_files):
    old, new = env_files
    result = runner.invoke(diff_group, ["plain", str(old), str(new), "--no-color"])
    assert result.exit_code == 0
    assert "-FOO=1" in result.output or "FOO" in result.output


def test_diff_plain_no_changes(runner, tmp_path):
    f = tmp_path / "same.env"
    f.write_text("FOO=bar\n")
    g = tmp_path / "same2.env"
    g.write_text("FOO=bar\n")
    result = runner.invoke(diff_group, ["plain", str(f), str(g)])
    assert result.exit_code == 0
    assert "No differences" in result.output


def test_diff_plain_error(runner, tmp_path):
    missing = tmp_path / "nope.env"
    other = tmp_path / "other.env"
    other.write_text("X=1\n")
    result = runner.invoke(diff_group, ["plain", str(missing), str(other)])
    assert result.exit_code != 0


def test_diff_encrypted_success(runner, tmp_path):
    old_enc = tmp_path / "old.env.age"
    new_enc = tmp_path / "new.env.age"
    identity = tmp_path / "key.txt"
    old_enc.write_text("x")
    new_enc.write_text("x")
    identity.write_text("k")

    fake_result = DiffResult(
        old_path=str(old_enc),
        new_path=str(new_enc),
        lines=["-FOO=1\n", "+FOO=2\n"],
    )
    with patch("envault.cli_diff.diff_encrypted", return_value=fake_result):
        result = runner.invoke(
            diff_group,
            ["encrypted", str(old_enc), str(new_enc), "-i", str(identity), "--no-color"],
        )
    assert result.exit_code == 0
    assert "FOO" in result.output


def test_diff_encrypted_error(runner, tmp_path):
    old_enc = tmp_path / "old.env.age"
    new_enc = tmp_path / "new.env.age"
    identity = tmp_path / "key.txt"
    old_enc.write_text("x")
    new_enc.write_text("x")
    identity.write_text("k")

    with patch("envault.cli_diff.diff_encrypted", side_effect=DiffError("oops")):
        result = runner.invoke(
            diff_group,
            ["encrypted", str(old_enc), str(new_enc), "-i", str(identity)],
        )
    assert result.exit_code != 0
    assert "oops" in result.output
