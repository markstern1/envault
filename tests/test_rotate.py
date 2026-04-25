"""Tests for key rotation functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.rotate import rotate_key, list_rotation_history, RotationError


PUBLIC_KEY = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"


@pytest.fixture()
def fake_encrypted(tmp_path: Path) -> Path:
    f = tmp_path / "secrets.env.age"
    f.write_bytes(b"encrypted-data")
    return f


@pytest.fixture()
def fake_identity(tmp_path: Path) -> Path:
    ident = tmp_path / "key.txt"
    ident.write_text("AGE-SECRET-KEY-1FAKE")
    return ident


def test_rotate_key_success(fake_encrypted: Path, fake_identity: Path, tmp_path: Path):
    output = tmp_path / "rotated.env.age"
    with (
        patch("envault.rotate.decrypt_file") as mock_dec,
        patch("envault.rotate.encrypt_file") as mock_enc,
        patch("envault.rotate.record_version") as mock_ver,
        patch("envault.rotate.record_event") as mock_audit,
    ):
        result = rotate_key(fake_encrypted, fake_identity, PUBLIC_KEY, output=output)

    assert result == output
    mock_dec.assert_called_once()
    mock_enc.assert_called_once()
    mock_ver.assert_called_once_with(output, PUBLIC_KEY)
    mock_audit.assert_called_once()


def test_rotate_key_missing_encrypted(fake_identity: Path, tmp_path: Path):
    missing = tmp_path / "ghost.env.age"
    with pytest.raises(RotationError, match="Encrypted file not found"):
        rotate_key(missing, fake_identity, PUBLIC_KEY)


def test_rotate_key_missing_identity(fake_encrypted: Path, tmp_path: Path):
    missing_ident = tmp_path / "no_key.txt"
    with pytest.raises(RotationError, match="Identity file not found"):
        rotate_key(fake_encrypted, missing_ident, PUBLIC_KEY)


def test_rotate_key_decrypt_failure(fake_encrypted: Path, fake_identity: Path):
    from envault.crypto import CryptoError

    with patch("envault.rotate.decrypt_file", side_effect=CryptoError("bad key")):
        with pytest.raises(RotationError, match="Decryption failed"):
            rotate_key(fake_encrypted, fake_identity, PUBLIC_KEY)


def test_rotate_key_encrypt_failure(fake_encrypted: Path, fake_identity: Path):
    from envault.crypto import CryptoError

    with (
        patch("envault.rotate.decrypt_file"),
        patch("envault.rotate.encrypt_file", side_effect=CryptoError("bad recipient")),
    ):
        with pytest.raises(RotationError, match="Re-encryption failed"):
            rotate_key(fake_encrypted, fake_identity, PUBLIC_KEY)


def test_rotate_cleans_up_temp_file_on_failure(fake_encrypted: Path, fake_identity: Path):
    from envault.crypto import CryptoError

    with (
        patch("envault.rotate.decrypt_file"),
        patch("envault.rotate.encrypt_file", side_effect=CryptoError("fail")),
    ):
        with pytest.raises(RotationError):
            rotate_key(fake_encrypted, fake_identity, PUBLIC_KEY)

    tmp_plain = fake_encrypted.with_suffix(".tmp_plain")
    assert not tmp_plain.exists()


def test_list_rotation_history(tmp_path: Path):
    env_file = tmp_path / "secrets.env.age"
    with patch("envault.rotate.list_versions", return_value=[{"recipient": PUBLIC_KEY}]) as mock_lv:
        history = list_rotation_history(env_file)
    mock_lv.assert_called_once_with(env_file)
    assert history == [{"recipient": PUBLIC_KEY}]
