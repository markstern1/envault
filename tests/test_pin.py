"""Tests for src/envault/pin.py"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.pin import (
    PinError,
    PinEntry,
    pin_file,
    verify_pin,
    list_pins,
    remove_pin,
    PIN_FILE,
)


@pytest.fixture()
def enc_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.env.age"
    p.write_bytes(b"fake-encrypted-content")
    return p


def test_pin_file_creates_pin_file(tmp_path, enc_file):
    entry = pin_file(enc_file, label="prod", directory=tmp_path)
    assert (tmp_path / PIN_FILE).exists()
    assert entry.label == "prod"
    assert entry.checksum  # non-empty sha256


def test_pin_file_stores_correct_checksum(tmp_path, enc_file):
    import hashlib
    expected = hashlib.sha256(enc_file.read_bytes()).hexdigest()
    entry = pin_file(enc_file, label="staging", directory=tmp_path)
    assert entry.checksum == expected


def test_pin_file_stores_optional_fields(tmp_path, enc_file):
    entry = pin_file(
        enc_file,
        label="ci",
        directory=tmp_path,
        version_id="v3",
        note="CI deployment",
        tags=["ci", "automated"],
    )
    assert entry.version_id == "v3"
    assert entry.note == "CI deployment"
    assert "ci" in entry.tags


def test_pin_file_raises_on_missing_file(tmp_path):
    with pytest.raises(PinError, match="not found"):
        pin_file(tmp_path / "nonexistent.age", label="x", directory=tmp_path)


def test_pin_file_raises_on_empty_label(tmp_path, enc_file):
    with pytest.raises(PinError, match="Label"):
        pin_file(enc_file, label="  ", directory=tmp_path)


def test_verify_pin_returns_true_for_unchanged_file(tmp_path, enc_file):
    pin_file(enc_file, label="prod", directory=tmp_path)
    assert verify_pin("prod", enc_file, directory=tmp_path) is True


def test_verify_pin_returns_false_after_modification(tmp_path, enc_file):
    pin_file(enc_file, label="prod", directory=tmp_path)
    enc_file.write_bytes(b"tampered-content")
    assert verify_pin("prod", enc_file, directory=tmp_path) is False


def test_verify_pin_raises_on_unknown_label(tmp_path, enc_file):
    with pytest.raises(PinError, match="No pin found"):
        verify_pin("ghost", enc_file, directory=tmp_path)


def test_list_pins_returns_all_entries(tmp_path, enc_file):
    pin_file(enc_file, label="a", directory=tmp_path)
    pin_file(enc_file, label="b", directory=tmp_path)
    pins = list_pins(tmp_path)
    labels = {p.label for p in pins}
    assert labels == {"a", "b"}


def test_list_pins_empty_directory(tmp_path):
    assert list_pins(tmp_path) == []


def test_remove_pin_deletes_entry(tmp_path, enc_file):
    pin_file(enc_file, label="old", directory=tmp_path)
    remove_pin("old", tmp_path)
    assert "old" not in json.loads((tmp_path / PIN_FILE).read_text())


def test_remove_pin_raises_on_unknown_label(tmp_path):
    with pytest.raises(PinError, match="No pin found"):
        remove_pin("missing", tmp_path)
