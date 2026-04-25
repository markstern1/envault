"""Tests for envault.audit module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import record_event, get_events, AUDIT_FILE


@pytest.fixture()
def audit_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_record_event_creates_audit_file(audit_dir: Path) -> None:
    record_event("encrypt", ".env", audit_dir=audit_dir)
    assert (audit_dir / AUDIT_FILE).exists()


def test_record_event_returns_entry(audit_dir: Path) -> None:
    entry = record_event("encrypt", ".env", audit_dir=audit_dir)
    assert entry["action"] == "encrypt"
    assert entry["target"] == ".env"
    assert entry["timestamp"].endswith("Z")


def test_record_event_appends_multiple(audit_dir: Path) -> None:
    record_event("encrypt", ".env", audit_dir=audit_dir)
    record_event("decrypt", ".env.age", audit_dir=audit_dir)
    entries = json.loads((audit_dir / AUDIT_FILE).read_text())
    assert len(entries) == 2
    assert entries[0]["action"] == "encrypt"
    assert entries[1]["action"] == "decrypt"


def test_record_event_stores_actor(audit_dir: Path) -> None:
    entry = record_event("team_add", "team.json", actor="alice", audit_dir=audit_dir)
    assert entry["actor"] == "alice"


def test_record_event_stores_metadata(audit_dir: Path) -> None:
    entry = record_event(
        "encrypt",
        ".env",
        metadata={"recipient": "age1abc"},
        audit_dir=audit_dir,
    )
    assert entry["metadata"] == {"recipient": "age1abc"}


def test_record_event_omits_optional_fields_when_absent(audit_dir: Path) -> None:
    entry = record_event("decrypt", ".env.age", audit_dir=audit_dir)
    assert "actor" not in entry
    assert "metadata" not in entry


def test_get_events_returns_all(audit_dir: Path) -> None:
    record_event("encrypt", ".env", audit_dir=audit_dir)
    record_event("decrypt", ".env.age", audit_dir=audit_dir)
    events = get_events(audit_dir=audit_dir)
    assert len(events) == 2


def test_get_events_filters_by_target(audit_dir: Path) -> None:
    record_event("encrypt", ".env", audit_dir=audit_dir)
    record_event("encrypt", ".env.prod", audit_dir=audit_dir)
    events = get_events(target=".env", audit_dir=audit_dir)
    assert len(events) == 1
    assert events[0]["target"] == ".env"


def test_get_events_filters_by_action(audit_dir: Path) -> None:
    record_event("encrypt", ".env", audit_dir=audit_dir)
    record_event("decrypt", ".env.age", audit_dir=audit_dir)
    events = get_events(action="decrypt", audit_dir=audit_dir)
    assert len(events) == 1
    assert events[0]["action"] == "decrypt"


def test_get_events_empty_when_no_file(audit_dir: Path) -> None:
    events = get_events(audit_dir=audit_dir)
    assert events == []
