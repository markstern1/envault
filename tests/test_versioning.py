"""Tests for envault.versioning module."""

import json
from pathlib import Path

import pytest

from envault.versioning import VERSION_FILE, list_versions, record_version

RECIPIENT = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"


def test_record_version_creates_version_file(tmp_path):
    enc = tmp_path / ".env.age"
    enc.write_bytes(b"fake encrypted content")

    checksum = record_version(enc, RECIPIENT)

    version_file = tmp_path / VERSION_FILE
    assert version_file.exists()
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex digest


def test_record_version_appends_entries(tmp_path):
    enc = tmp_path / ".env.age"
    enc.write_bytes(b"v1")
    record_version(enc, RECIPIENT)

    enc.write_bytes(b"v2")
    record_version(enc, RECIPIENT)

    version_file = tmp_path / VERSION_FILE
    versions = json.loads(version_file.read_text())
    assert len(versions) == 2
    assert versions[0]["version"] == 1
    assert versions[1]["version"] == 2


def test_record_version_stores_recipient(tmp_path):
    enc = tmp_path / ".env.age"
    enc.write_bytes(b"data")
    record_version(enc, RECIPIENT)

    version_file = tmp_path / VERSION_FILE
    versions = json.loads(version_file.read_text())
    assert versions[0]["recipient"] == RECIPIENT


def test_record_version_checksum_changes_with_content(tmp_path):
    """Verify that different file contents produce different checksums."""
    enc = tmp_path / ".env.age"

    enc.write_bytes(b"content_v1")
    checksum_v1 = record_version(enc, RECIPIENT)

    enc.write_bytes(b"content_v2")
    checksum_v2 = record_version(enc, RECIPIENT)

    assert checksum_v1 != checksum_v2


def test_record_version_same_content_produces_same_checksum(tmp_path):
    """Verify that identical file contents produce the same checksum across versions."""
    enc = tmp_path / ".env.age"
    enc.write_bytes(b"identical_content")

    checksum_v1 = record_version(enc, RECIPIENT)
    checksum_v2 = record_version(enc, RECIPIENT)

    assert checksum_v1 == checksum_v2


def test_list_versions_returns_only_matching_file(tmp_path):
    enc1 = tmp_path / ".env.age"
    enc1.write_bytes(b"env1")
    enc2 = tmp_path / ".env.prod.age"
    enc2.write_bytes(b"env2")

    vf = tmp_path / VERSION_FILE
    record_version(enc1, RECIPIENT, version_file=vf)
    record_version(enc2, RECIPIENT, version_file=vf)
    record_version(enc1, RECIPIENT, version_file=vf)

    result = list_versions(enc1, version_file=vf)
    assert len(result) == 2
    assert all(v["file"] == ".env.age" for v in result)


def test_list_versions_empty_when_no_file(tmp_path):
    enc = tmp_path / ".env.age"
    enc.write_bytes(b"data")
    result = list_versions(enc)
    assert result == []
