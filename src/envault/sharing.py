"""Team sharing support for envault — manage recipient public keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

TEAM_FILE = ".envault-team.json"


class SharingError(Exception):
    """Raised when a sharing operation fails."""


def _load_team(team_file: Path) -> Dict[str, str]:
    """Load team members from the JSON file. Returns {alias: public_key}."""
    if not team_file.exists():
        return {}
    try:
        data = json.loads(team_file.read_text())
        if not isinstance(data, dict):
            raise SharingError(f"{team_file} is malformed (expected a JSON object)")
        return data
    except json.JSONDecodeError as exc:
        raise SharingError(f"Failed to parse {team_file}: {exc}") from exc


def _save_team(team_file: Path, team: Dict[str, str]) -> None:
    """Persist team members to the JSON file."""
    team_file.write_text(json.dumps(team, indent=2) + "\n")


def add_recipient(alias: str, public_key: str, team_file: Path | None = None) -> None:
    """Add or update a recipient in the team file."""
    path = Path(team_file) if team_file else Path(TEAM_FILE)
    if not alias.strip():
        raise SharingError("Alias must not be empty.")
    if not public_key.strip().startswith("age"):
        raise SharingError("Public key does not look like a valid age public key.")
    team = _load_team(path)
    team[alias] = public_key.strip()
    _save_team(path, team)


def remove_recipient(alias: str, team_file: Path | None = None) -> None:
    """Remove a recipient from the team file."""
    path = Path(team_file) if team_file else Path(TEAM_FILE)
    team = _load_team(path)
    if alias not in team:
        raise SharingError(f"Recipient '{alias}' not found in team file.")
    del team[alias]
    _save_team(path, team)


def list_recipients(team_file: Path | None = None) -> List[Dict[str, str]]:
    """Return a list of {alias, public_key} dicts for all team members."""
    path = Path(team_file) if team_file else Path(TEAM_FILE)
    team = _load_team(path)
    return [{"alias": alias, "public_key": key} for alias, key in sorted(team.items())]


def get_public_keys(team_file: Path | None = None) -> List[str]:
    """Return only the public keys for all team members (for bulk encryption)."""
    return [r["public_key"] for r in list_recipients(team_file)]
