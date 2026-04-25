"""Tests for envault.sharing — team recipient management."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.sharing import (
    SharingError,
    add_recipient,
    get_public_keys,
    list_recipients,
    remove_recipient,
)

FAKE_KEY_A = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq0ljelq"
FAKE_KEY_B = "age1zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz8f4r0"


def test_add_recipient_creates_file(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    add_recipient("alice", FAKE_KEY_A, team_file=team_file)
    assert team_file.exists()
    data = json.loads(team_file.read_text())
    assert data["alice"] == FAKE_KEY_A


def test_add_recipient_updates_existing(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    add_recipient("alice", FAKE_KEY_A, team_file=team_file)
    add_recipient("alice", FAKE_KEY_B, team_file=team_file)
    data = json.loads(team_file.read_text())
    assert data["alice"] == FAKE_KEY_B


def test_add_recipient_multiple_members(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    add_recipient("alice", FAKE_KEY_A, team_file=team_file)
    add_recipient("bob", FAKE_KEY_B, team_file=team_file)
    data = json.loads(team_file.read_text())
    assert len(data) == 2


def test_add_recipient_rejects_invalid_key(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    with pytest.raises(SharingError, match="valid age public key"):
        add_recipient("alice", "not-a-key", team_file=team_file)


def test_add_recipient_rejects_empty_alias(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    with pytest.raises(SharingError, match="Alias must not be empty"):
        add_recipient("  ", FAKE_KEY_A, team_file=team_file)


def test_remove_recipient(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    add_recipient("alice", FAKE_KEY_A, team_file=team_file)
    remove_recipient("alice", team_file=team_file)
    data = json.loads(team_file.read_text())
    assert "alice" not in data


def test_remove_recipient_raises_when_missing(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    with pytest.raises(SharingError, match="not found"):
        remove_recipient("ghost", team_file=team_file)


def test_list_recipients_sorted(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    add_recipient("zara", FAKE_KEY_B, team_file=team_file)
    add_recipient("alice", FAKE_KEY_A, team_file=team_file)
    recipients = list_recipients(team_file=team_file)
    assert recipients[0]["alias"] == "alice"
    assert recipients[1]["alias"] == "zara"


def test_list_recipients_empty_when_no_file(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    assert list_recipients(team_file=team_file) == []


def test_get_public_keys(tmp_path: Path) -> None:
    team_file = tmp_path / ".envault-team.json"
    add_recipient("alice", FAKE_KEY_A, team_file=team_file)
    add_recipient("bob", FAKE_KEY_B, team_file=team_file)
    keys = get_public_keys(team_file=team_file)
    assert FAKE_KEY_A in keys
    assert FAKE_KEY_B in keys
