"""Export decrypted .env contents to shell-compatible formats."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

ExportFormat = Literal["shell", "dotenv", "json"]


class ExportError(Exception):
    """Raised when export fails."""


def _parse_env_lines(text: str) -> dict[str, str]:
    """Parse key=value lines, ignoring comments and blanks."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
        if match:
            key, value = match.group(1), match.group(2)
            # Strip surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
    return result


def export_env(plaintext: str, fmt: ExportFormat = "shell") -> str:
    """Convert plaintext .env content to the requested export format."""
    pairs = _parse_env_lines(plaintext)

    if fmt == "shell":
        lines = [f'export {k}="{v}"' for k, v in pairs.items()]
        return "\n".join(lines)

    if fmt == "dotenv":
        lines = [f'{k}="{v}"' for k, v in pairs.items()]
        return "\n".join(lines)

    if fmt == "json":
        import json
        return json.dumps(pairs, indent=2)

    raise ExportError(f"Unknown export format: {fmt}")


def export_file(path: Path, fmt: ExportFormat = "shell") -> str:
    """Read a plaintext .env file and export it in the given format."""
    if not path.exists():
        raise ExportError(f"File not found: {path}")
    return export_env(path.read_text(encoding="utf-8"), fmt)
