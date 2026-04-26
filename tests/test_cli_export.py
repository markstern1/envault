"""Tests for the export CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envault.cli_export import export_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_files(tmp_path: Path):
    encrypted = tmp_path / "secrets.env.age"
    encrypted.write_bytes(b"fake-age-data")
    identity = tmp_path / "key.txt"
    identity.write_text("AGE-SECRET-KEY-1FAKE")
    return encrypted, identity, tmp_path


def test_export_run_shell_stdout(runner, env_files, tmp_path):
    encrypted, identity, _ = env_files
    plaintext = "DB_HOST=localhost\nSECRET=abc\n"

    def fake_decrypt(src, dst, ident):
        Path(dst).write_text(plaintext)

    with patch("envault.cli_export.decrypt_file", side_effect=fake_decrypt):
        result = runner.invoke(
            export_group,
            ["run", str(encrypted), "-i", str(identity), "-f", "shell"],
        )
    assert result.exit_code == 0
    assert 'export DB_HOST="localhost"' in result.output


def test_export_run_json_format(runner, env_files):
    encrypted, identity, _ = env_files
    plaintext = "APP=myapp\nVERSION=1\n"

    def fake_decrypt(src, dst, ident):
        Path(dst).write_text(plaintext)

    with patch("envault.cli_export.decrypt_file", side_effect=fake_decrypt):
        result = runner.invoke(
            export_group,
            ["run", str(encrypted), "-i", str(identity), "-f", "json"],
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["APP"] == "myapp"


def test_export_run_writes_output_file(runner, env_files, tmp_path):
    encrypted, identity, _ = env_files
    out_file = tmp_path / "exported.sh"
    plaintext = "FOO=bar\n"

    def fake_decrypt(src, dst, ident):
        Path(dst).write_text(plaintext)

    with patch("envault.cli_export.decrypt_file", side_effect=fake_decrypt):
        result = runner.invoke(
            export_group,
            ["run", str(encrypted), "-i", str(identity), "-o", str(out_file)],
        )
    assert result.exit_code == 0
    assert out_file.exists()
    assert 'export FOO="bar"' in out_file.read_text()


def test_export_run_crypto_error(runner, env_files):
    encrypted, identity, _ = env_files
    from envault.crypto import CryptoError

    with patch("envault.cli_export.decrypt_file", side_effect=CryptoError("bad key")):
        result = runner.invoke(
            export_group,
            ["run", str(encrypted), "-i", str(identity)],
        )
    assert result.exit_code != 0
    assert "bad key" in result.output
