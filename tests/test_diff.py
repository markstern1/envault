"""Unit tests for envault.diff."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.diff import diff_files, diff_encrypted, DiffError, DiffResult


@pytest.fixture()
def env_pair(tmp_path: Path):
    old = tmp_path / "old.env"
    new = tmp_path / "new.env"
    old.write_text("FOO=bar\nBAZ=qux\n")
    new.write_text("FOO=bar\nBAZ=changed\nNEW=value\n")
    return old, new


def test_diff_files_detects_changes(env_pair):
    old, new = env_pair
    result = diff_files(old, new)
    assert result.has_changes
    assert isinstance(result.lines, list)


def test_diff_files_no_changes(tmp_path: Path):
    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f1.write_text("FOO=bar\n")
    f2.write_text("FOO=bar\n")
    result = diff_files(f1, f2)
    assert not result.has_changes


def test_diff_files_missing_old(tmp_path: Path):
    with pytest.raises(DiffError, match="Cannot read"):
        diff_files(tmp_path / "ghost.env", tmp_path / "ghost2.env")


def test_diff_files_missing_new(tmp_path: Path):
    old = tmp_path / "old.env"
    old.write_text("X=1\n")
    with pytest.raises(DiffError, match="Cannot read"):
        diff_files(old, tmp_path / "missing.env")


def test_diff_result_as_text(env_pair):
    old, new = env_pair
    result = diff_files(old, new)
    text = result.as_text()
    assert "BAZ" in text


def test_diff_encrypted_calls_decrypt(tmp_path: Path):
    old_enc = tmp_path / "old.env.age"
    new_enc = tmp_path / "new.env.age"
    old_enc.write_text("dummy")
    new_enc.write_text("dummy")
    identity = tmp_path / "key.txt"
    identity.write_text("AGE-SECRET-KEY-1")

    def fake_decrypt(src, dst, ident):
        dst.write_text("FOO=1\n" if "old" in dst.name else "FOO=2\n")

    with patch("envault.diff.decrypt_file", side_effect=fake_decrypt):
        result = diff_encrypted(old_enc, new_enc, identity, tmp_path)

    assert result.has_changes


def test_diff_encrypted_raises_on_decrypt_error(tmp_path: Path):
    from envault.crypto import CryptoError

    old_enc = tmp_path / "old.env.age"
    new_enc = tmp_path / "new.env.age"
    old_enc.write_text("x")
    new_enc.write_text("x")
    identity = tmp_path / "key.txt"
    identity.write_text("k")

    with patch("envault.diff.decrypt_file", side_effect=CryptoError("bad")):
        with pytest.raises(DiffError, match="Failed to decrypt"):
            diff_encrypted(old_enc, new_enc, identity, tmp_path)
