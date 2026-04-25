"""Audit log support for envault operations."""

from __future__ import annotations

import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

AUDIT_FILE = ".envault_audit.json"


def _load_audit(audit_path: Path) -> List[Dict[str, Any]]:
    """Load existing audit log entries."""
    if not audit_path.exists():
        return []
    try:
        return json.loads(audit_path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_audit(audit_path: Path, entries: List[Dict[str, Any]]) -> None:
    """Persist audit log entries to disk."""
    audit_path.write_text(json.dumps(entries, indent=2))


def record_event(
    action: str,
    target: str,
    actor: str | None = None,
    metadata: Dict[str, Any] | None = None,
    audit_dir: Path | None = None,
) -> Dict[str, Any]:
    """Append an audit event and return the recorded entry.

    Args:
        action:    Short action label, e.g. "encrypt", "decrypt", "team_add".
        target:    The file or resource the action was performed on.
        actor:     Optional identifier for who performed the action.
        metadata:  Optional extra key/value data to store with the event.
        audit_dir: Directory to store the audit log (defaults to cwd).

    Returns:
        The newly created audit entry dict.
    """
    audit_path = (audit_dir or Path.cwd()) / AUDIT_FILE
    entries = _load_audit(audit_path)

    entry: Dict[str, Any] = {
        "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "action": action,
        "target": target,
    }
    if actor:
        entry["actor"] = actor
    if metadata:
        entry["metadata"] = metadata

    entries.append(entry)
    _save_audit(audit_path, entries)
    return entry


def get_events(
    target: str | None = None,
    action: str | None = None,
    audit_dir: Path | None = None,
) -> List[Dict[str, Any]]:
    """Return audit events, optionally filtered by target and/or action."""
    audit_path = (audit_dir or Path.cwd()) / AUDIT_FILE
    entries = _load_audit(audit_path)

    if target is not None:
        entries = [e for e in entries if e.get("target") == target]
    if action is not None:
        entries = [e for e in entries if e.get("action") == action]

    return entries
