"""Tests for envault.crypto module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.crypto import CryptoError, decrypt_file, encrypt_file


RECIPIENT = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"


@patch("envault.crypto.subprocess.run")
def test_encrypt_file_calls_age(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    src = tmp_path / ".env"
    src.write_text("SECRET=abc")
    dst = tmp_path / ".env.age"

    encrypt_file(src, dst, RECIPIENT)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "age" in args
    assert "--recipient" in args
    assert RECIPIENT in args


@patch("envault.crypto.subprocess.run")
def test_encrypt_file_raises_on_failure(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stderr="bad recipient")
    src = tmp_path / ".env"
    src.write_text("X=1")
    dst = tmp_path / ".env.age"

    with pytest.raises(CryptoError, match="Encryption failed"):
        encrypt_file(src, dst, RECIPIENT)


@patch("envault.crypto.subprocess.run")
def test_encrypt_raises_when_age_missing(mock_run, tmp_path):
    mock_run.side_effect = FileNotFoundError
    src = tmp_path / ".env"
    src.write_text("X=1")
    dst = tmp_path / ".env.age"

    with pytest.raises(CryptoError, match="'age' binary not found"):
        encrypt_file(src, dst, RECIPIENT)


@patch("envault.crypto.subprocess.run")
def test_decrypt_file_calls_age(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    identity = tmp_path / "key.txt"
    identity.write_text("# public key: age1xxx\nAGE-SECRET-KEY-1xxx")
    src = tmp_path / ".env.age"
    src.write_bytes(b"encrypted")
    dst = tmp_path / ".env"

    decrypt_file(src, dst, identity_path=identity)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "--decrypt" in args
    assert "--identity" in args


@patch("envault.crypto.subprocess.run")
def test_decrypt_raises_on_missing_identity(mock_run, tmp_path):
    src = tmp_path / ".env.age"
    src.write_bytes(b"encrypted")
    dst = tmp_path / ".env"
    missing_key = tmp_path / "no_key.txt"

    with pytest.raises(CryptoError, match="Identity file not found"):
        decrypt_file(src, dst, identity_path=missing_key)


@patch("envault.crypto.subprocess.run")
def test_decrypt_raises_on_failure(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stderr="wrong key")
    identity = tmp_path / "key.txt"
    identity.write_text("# public key: age1xxx\nAGE-SECRET-KEY-1xxx")
    src = tmp_path / ".env.age"
    src.write_bytes(b"encrypted")
    dst = tmp_path / ".env"

    with pytest.raises(CryptoError, match="Decryption failed"):
        decrypt_file(src, dst, identity_path=identity)
