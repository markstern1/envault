"""Integration-style tests for rotate module wiring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import call, patch, MagicMock

import pytest

from envault.rotate import rotate_key, RotationError


PUBLIC_KEY = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"


@pytest.fixture()
def setup_files(tmp_path: Path):
    enc = tmp_path / "prod.env.age"
    enc.write_bytes(b"ciphertext")
    ident = tmp_path / "old_key.txt"
    ident.write_text("AGE-SECRET-KEY-1OLD")
    return enc, ident, tmp_path


def test_rotate_records_audit_event(setup_files):
    enc, ident, tmp_path = setup_files
    output = tmp_path / "prod_rotated.env.age"

    with (
        patch("envault.rotate.decrypt_file"),
        patch("envault.rotate.encrypt_file"),
        patch("envault.rotate.record_version"),
        patch("envault.rotate.record_event") as mock_audit,
    ):
        rotate_key(enc, ident, PUBLIC_KEY, output=output, actor="alice")

    mock_audit.assert_called_once_with(
        "rotate",
        str(output),
        actor="alice",
        metadata={"new_recipient": PUBLIC_KEY},
    )


def test_rotate_records_version(setup_files):
    enc, ident, tmp_path = setup_files
    output = tmp_path / "prod_rotated.env.age"

    with (
        patch("envault.rotate.decrypt_file"),
        patch("envault.rotate.encrypt_file"),
        patch("envault.rotate.record_version") as mock_ver,
        patch("envault.rotate.record_event"),
    ):
        rotate_key(enc, ident, PUBLIC_KEY, output=output)

    mock_ver.assert_called_once_with(output, PUBLIC_KEY)


def test_rotate_default_output_overwrites_input(setup_files):
    enc, ident, _ = setup_files

    with (
        patch("envault.rotate.decrypt_file"),
        patch("envault.rotate.encrypt_file") as mock_enc,
        patch("envault.rotate.record_version"),
        patch("envault.rotate.record_event"),
    ):
        result = rotate_key(enc, ident, PUBLIC_KEY)

    assert result == enc
    _, _, dest = mock_enc.call_args[0]
    assert dest == enc
