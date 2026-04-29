"""Search for keys across .env files or encrypted archives."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchMatch:
    file: str
    line_number: int
    key: str
    value_preview: str  # first 6 chars, rest masked

    def __str__(self) -> str:
        return f"{self.file}:{self.line_number}  {self.key}={self.value_preview}"


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0


def _mask_value(value: str) -> str:
    """Show first 6 chars and mask the rest with asterisks."""
    if len(value) <= 6:
        return "*" * len(value)
    return value[:6] + "*" * (len(value) - 6)


def _parse_env_lines(lines: List[str]) -> List[tuple[int, str, str]]:
    """Return (line_number, key, value) tuples from env lines."""
    results = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            results.append((i, key, value))
    return results


def search_file(
    path: Path,
    pattern: str,
    *,
    keys_only: bool = False,
    ignore_case: bool = False,
) -> SearchResult:
    """Search a plaintext .env file for keys (or values) matching *pattern*."""
    if not path.exists():
        raise SearchError(f"File not found: {path}")

    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        raise SearchError(f"Invalid pattern '{pattern}': {exc}") from exc

    lines = path.read_text(encoding="utf-8").splitlines()
    result = SearchResult()
    for lineno, key, value in _parse_env_lines(lines):
        key_match = regex.search(key)
        value_match = (not keys_only) and regex.search(value)
        if key_match or value_match:
            result.matches.append(
                SearchMatch(
                    file=str(path),
                    line_number=lineno,
                    key=key,
                    value_preview=_mask_value(value),
                )
            )
    return result


def search_files(
    paths: List[Path],
    pattern: str,
    *,
    keys_only: bool = False,
    ignore_case: bool = False,
) -> SearchResult:
    """Search multiple files and aggregate results."""
    combined = SearchResult()
    for p in paths:
        r = search_file(p, pattern, keys_only=keys_only, ignore_case=ignore_case)
        combined.matches.extend(r.matches)
    return combined
