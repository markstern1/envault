"""Tests for src/envault/clone.py."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.clone import CloneError, CloneResult, clone_for_recipient


RECIPIENT = "age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs0000"


@pytest.fixture()
def env_files(tmp_path: Path):
    enc = tmp_path / "secrets.env.age"
    enc.write_bytes(b"fake-age-ciphertext")
    identity = tmp_path / "key.txt"
    identity.write_text("AGE-SECRET-KEY-1FAKE")
    return enc, identity


def _patch_crypto():
    return (
        patch("envault.clone.decrypt_file"),
        patch("envault.clone.encrypt_file"),
        patch("envault.clone.record_event"),
    )


def test_clone_returns_result(tmp_path, env_files):
    enc, identity = env_files
    with (
        patch("envault.clone.decrypt_file") as mock_dec,
        patch("envault.clone.encrypt_file") as mock_enc,
        patch("envault.clone.record_event"),
    ):
        result = clone_for_recipient(enc, identity, RECIPIENT, tmp_dir=tmp_path)

    assert isinstance(result, CloneResult)
    assert result.source == enc
    assert result.recipient == RECIPIENT
    mock_dec.assert_called_once()
    mock_enc.assert_called_once()


def test_clone_default_output_name(tmp_path, env_files):
    enc, identity = env_files
    with (
        patch("envault.clone.decrypt_file"),
        patch("envault.clone.encrypt_file"),
        patch("envault.clone.record_event"),
    ):
        result = clone_for_recipient(enc, identity, RECIPIENT, tmp_dir=tmp_path)

    assert result.destination.name.startswith("secrets.env.")
    assert result.destination.suffix == ".age"


def test_clone_custom_output(tmp_path, env_files):
    enc, identity = env_files
    out = tmp_path / "custom.age"
    with (
        patch("envault.clone.decrypt_file"),
        patch("envault.clone.encrypt_file"),
        patch("envault.clone.record_event"),
    ):
        result = clone_for_recipient(enc, identity, RECIPIENT, output_path=out, tmp_dir=tmp_path)

    assert result.destination == out


def test_clone_raises_on_missing_encrypted(tmp_path, env_files):
    _, identity = env_files
    with pytest.raises(CloneError, match="Source file not found"):
        clone_for_recipient(tmp_path / "missing.age", identity, RECIPIENT)


def test_clone_raises_on_missing_identity(tmp_path, env_files):
    enc, _ = env_files
    with pytest.raises(CloneError, match="Identity file not found"):
        clone_for_recipient(enc, tmp_path / "missing.txt", RECIPIENT)


def test_clone_raises_on_invalid_recipient(tmp_path, env_files):
    enc, identity = env_files
    with pytest.raises(CloneError, match="Invalid recipient key"):
        clone_for_recipient(enc, identity, "not-an-age-key")


def test_clone_records_audit_event(tmp_path, env_files):
    enc, identity = env_files
    with (
        patch("envault.clone.decrypt_file"),
        patch("envault.clone.encrypt_file"),
        patch("envault.clone.record_event") as mock_audit,
    ):
        clone_for_recipient(enc, identity, RECIPIENT, tmp_dir=tmp_path, actor="alice")

    mock_audit.assert_called_once()
    _, kwargs = mock_audit.call_args
    assert kwargs.get("actor") == "alice" or mock_audit.call_args[0][2] == "alice"


def test_clone_wraps_crypto_error(tmp_path, env_files):
    from envault.crypto import CryptoError

    enc, identity = env_files
    with (
        patch("envault.clone.decrypt_file", side_effect=CryptoError("age failed")),
        patch("envault.clone.record_event"),
    ):
        with pytest.raises(CloneError, match="age failed"):
            clone_for_recipient(enc, identity, RECIPIENT, tmp_dir=tmp_path)
