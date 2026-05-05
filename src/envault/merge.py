"""Merge two .env files, with optional conflict resolution strategies."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple


class MergeError(Exception):
    """Raised when a merge operation fails."""


class ConflictStrategy(str, Enum):
    OURS = "ours"       # keep value from base file
    THEIRS = "theirs"   # keep value from other file
    ERROR = "error"     # raise on any conflict


class MergeConflict(NamedTuple):
    key: str
    ours: str
    theirs: str

    def __str__(self) -> str:
        return f"CONFLICT {self.key}: ours={self.ours!r} theirs={self.theirs!r}"


class MergeResult(NamedTuple):
    merged: Dict[str, str]
    conflicts: List[MergeConflict]
    added: List[str]      # keys only in other
    removed: List[str]    # keys only in base

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def _parse_env(path: Path) -> Dict[str, str]:
    """Parse a .env file into an ordered dict of key->value pairs."""
    result: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def merge_env_files(
    base: Path,
    other: Path,
    strategy: ConflictStrategy = ConflictStrategy.ERROR,
    output: Optional[Path] = None,
) -> MergeResult:
    """Merge *other* into *base*, returning a MergeResult.

    Args:
        base: The primary .env file ("ours").
        other: The secondary .env file ("theirs").
        strategy: How to resolve key conflicts.
        output: If given, write the merged result to this path.

    Raises:
        MergeError: If *base* or *other* do not exist, or strategy is ERROR
                    and conflicts are detected.
    """
    if not base.exists():
        raise MergeError(f"Base file not found: {base}")
    if not other.exists():
        raise MergeError(f"Other file not found: {other}")

    base_env = _parse_env(base)
    other_env = _parse_env(other)

    conflicts: List[MergeConflict] = []
    added = [k for k in other_env if k not in base_env]
    removed = [k for k in base_env if k not in other_env]

    merged: Dict[str, str] = dict(base_env)

    for key, other_val in other_env.items():
        if key not in base_env:
            merged[key] = other_val
        elif base_env[key] != other_val:
            conflict = MergeConflict(key=key, ours=base_env[key], theirs=other_val)
            conflicts.append(conflict)
            if strategy == ConflictStrategy.ERROR:
                raise MergeError(f"Conflict on key '{key}': {conflict}")
            elif strategy == ConflictStrategy.THEIRS:
                merged[key] = other_val
            # OURS: keep base value (already in merged)

    result = MergeResult(merged=merged, conflicts=conflicts, added=added, removed=removed)

    if output is not None:
        lines = [f"{k}={v}" for k, v in merged.items()]
        output.write_text("\n".join(lines) + "\n")

    return result
