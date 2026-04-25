"""Tests for the envault CLI entry-point."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli import main


@pytest.fixture()
runner() -> CliRunner:
    return CliRunner()


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_encrypt_requires_recipient(runner: CliRunner, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hello\n")
    result = runner.invoke(main, ["encrypt", str(env_file)])
    assert result.exit_code != 0
    assert "recipient" in result.output.lower()


def test_encrypt_calls_crypto(runner: CliRunner, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hello\n")
    out_file = tmp_path / ".env.age"

    with patch("envault.crypto.encrypt_file") as mock_enc:
        result = runner.invoke(
            main,
            [
                "encrypt",
                str(env_file),
                "-r", "age1qqq",
                "-o", str(out_file),
            ],
        )
    assert result.exit_code == 0, result.output
    mock_enc.assert_called_once_with(str(env_file), ["age1qqq"], str(out_file))


def test_decrypt_calls_crypto(runner: CliRunner, tmp_path: Path) -> None:
    enc_file = tmp_path / ".env.age"
    enc_file.write_bytes(b"encrypted")
    identity = tmp_path / "key.txt"
    identity.write_text("AGE-SECRET-KEY-1...\n")
    out_file = tmp_path / ".env"

    with patch("envault.crypto.decrypt_file") as mock_dec:
        result = runner.invoke(
            main,
            [
                "decrypt",
                str(enc_file),
                "-i", str(identity),
                "-o", str(out_file),
            ],
        )
    assert result.exit_code == 0, result.output
    mock_dec.assert_called_once_with(str(enc_file), str(identity), str(out_file))


def test_decrypt_default_output_strips_age(runner: CliRunner, tmp_path: Path) -> None:
    enc_file = tmp_path / "prod.env.age"
    enc_file.write_bytes(b"encrypted")
    identity = tmp_path / "key.txt"
    identity.write_text("AGE-SECRET-KEY-1...\n")

    with patch("envault.crypto.decrypt_file") as mock_dec:
        result = runner.invoke(
            main,
            ["decrypt", str(enc_file), "-i", str(identity)],
        )
    assert result.exit_code == 0, result.output
    expected_out = str(enc_file)[: -len(".age")]
    mock_dec.assert_called_once_with(str(enc_file), str(identity), expected_out)
