"""Tests for src/envault/compare.py"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.compare import compare_encrypted, CompareError, CompareResult
from envault.diff import DiffResult


@pytest.fixture()
def fake_paths(tmp_path: Path):
    old_enc = tmp_path / "old.env.age"
    new_enc = tmp_path / "new.env.age"
    identity = tmp_path / "key.txt"
    old_enc.write_bytes(b"encrypted-old")
    new_enc.write_bytes(b"encrypted-new")
    identity.write_text("AGE-SECRET-KEY-FAKE")
    return old_enc, new_enc, identity


def _make_diff(changed: bool) -> DiffResult:
    return DiffResult(
        added={"NEW_KEY": "val"} if changed else {},
        removed={},
        modified={},
        unchanged={"EXISTING": "x"},
    )


def test_compare_returns_result(fake_paths):
    old_enc, new_enc, identity = fake_paths
    diff = _make_diff(True)

    with patch("envault.compare.decrypt_file"), \
         patch("envault.compare.diff_files", return_value=diff):
        result = compare_encrypted(old_enc, new_enc, identity)

    assert isinstance(result, CompareResult)
    assert result.has_changes is True
    assert result.old_file == str(old_enc)
    assert result.new_file == str(new_enc)


def test_compare_no_changes(fake_paths):
    old_enc, new_enc, identity = fake_paths
    diff = _make_diff(False)

    with patch("envault.compare.decrypt_file"), \
         patch("envault.compare.diff_files", return_value=diff):
        result = compare_encrypted(old_enc, new_enc, identity)

    assert result.has_changes is False
    assert result.summary() == "No differences found."


def test_compare_summary_shows_counts(fake_paths):
    old_enc, new_enc, identity = fake_paths
    diff = DiffResult(
        added={"A": "1"},
        removed={"B": "2"},
        modified={"C": ("old", "new")},
        unchanged={},
    )

    with patch("envault.compare.decrypt_file"), \
         patch("envault.compare.diff_files", return_value=diff):
        result = compare_encrypted(old_enc, new_enc, identity)

    summary = result.summary()
    assert "+1 added" in summary
    assert "-1 removed" in summary
    assert "~1 modified" in summary


def test_compare_raises_on_missing_old(tmp_path):
    new_enc = tmp_path / "new.env.age"
    new_enc.write_bytes(b"x")
    identity = tmp_path / "key.txt"
    identity.write_text("key")

    with pytest.raises(CompareError, match="File not found"):
        compare_encrypted(tmp_path / "missing.age", new_enc, identity)


def test_compare_raises_on_missing_new(tmp_path):
    old_enc = tmp_path / "old.env.age"
    old_enc.write_bytes(b"x")
    identity = tmp_path / "key.txt"
    identity.write_text("key")

    with pytest.raises(CompareError, match="File not found"):
        compare_encrypted(old_enc, tmp_path / "missing.age", identity)


def test_compare_raises_on_missing_identity(tmp_path):
    old_enc = tmp_path / "old.env.age"
    new_enc = tmp_path / "new.env.age"
    old_enc.write_bytes(b"x")
    new_enc.write_bytes(b"x")

    with pytest.raises(CompareError, match="Identity file not found"):
        compare_encrypted(old_enc, new_enc, tmp_path / "no-key.txt")


def test_compare_wraps_crypto_error(fake_paths):
    from envault.crypto import CryptoError
    old_enc, new_enc, identity = fake_paths

    with patch("envault.compare.decrypt_file", side_effect=CryptoError("bad")):
        with pytest.raises(CompareError, match="Decryption failed"):
            compare_encrypted(old_enc, new_enc, identity)
