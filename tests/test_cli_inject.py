"""Tests for the inject CLI commands."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envault.cli_inject import inject_group
from envault.inject import InjectError, InjectResult


@pytest.fixture()
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def env_files(tmp_path: Path):
    enc = tmp_path / "secrets.env.age"
    enc.write_bytes(b"age-data")
    identity = tmp_path / "key.txt"
    identity.write_text("AGE-SECRET-KEY-1FAKE")
    return enc, identity


def test_inject_run_success(runner, env_files):
    enc, identity = env_files
    fake_result = InjectResult(command=["echo", "hi"], returncode=0, injected_keys=["A", "B"])
    with patch("envault.cli_inject.inject_run", return_value=fake_result) as mock_fn:
        result = runner.invoke(
            inject_group,
            ["run", str(enc), "--identity", str(identity), "echo", "hi"],
        )
    mock_fn.assert_called_once()
    assert "injected 2 variable(s)" in result.output + (result.stderr or "")
    assert result.exit_code == 0


def test_inject_run_failure_propagates_exit_code(runner, env_files):
    enc, identity = env_files
    fake_result = InjectResult(command=["false"], returncode=42, injected_keys=["X"])
    with patch("envault.cli_inject.inject_run", return_value=fake_result):
        result = runner.invoke(
            inject_group,
            ["run", str(enc), "--identity", str(identity), "false"],
        )
    assert result.exit_code == 42


def test_inject_run_inject_error(runner, env_files):
    enc, identity = env_files
    with patch("envault.cli_inject.inject_run", side_effect=InjectError("boom")):
        result = runner.invoke(
            inject_group,
            ["run", str(enc), "--identity", str(identity), "echo"],
        )
    assert result.exit_code != 0
    assert "boom" in result.output


def test_inject_run_quiet_suppresses_info(runner, env_files):
    enc, identity = env_files
    fake_result = InjectResult(command=["echo"], returncode=0, injected_keys=["A"])
    with patch("envault.cli_inject.inject_run", return_value=fake_result):
        result = runner.invoke(
            inject_group,
            ["run", str(enc), "--identity", str(identity), "--quiet", "echo"],
        )
    assert "injected" not in (result.output + (result.stderr or ""))
    assert result.exit_code == 0


def test_inject_run_bad_set_option(runner, env_files):
    enc, identity = env_files
    result = runner.invoke(
        inject_group,
        ["run", str(enc), "--identity", str(identity), "--set", "NOEQUALS", "echo"],
    )
    assert result.exit_code != 0
    assert "KEY=VALUE" in result.output
