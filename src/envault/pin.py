"""Pin a specific version of an encrypted .env file for reproducible deployments."""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PIN_FILE = ".envault-pins.json"


class PinError(Exception):
    """Raised when a pin operation fails."""


@dataclass
class PinEntry:
    label: str
    file: str
    checksum: str
    version_id: Optional[str] = None
    note: str = ""
    tags: list[str] = field(default_factory=list)


def _pin_path(directory: Path) -> Path:
    return directory / PIN_FILE


def _load_pins(directory: Path) -> dict:
    p = _pin_path(directory)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_pins(directory: Path, data: dict) -> None:
    _pin_path(directory).write_text(json.dumps(data, indent=2))


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin_file(
    encrypted_file: Path,
    label: str,
    *,
    directory: Optional[Path] = None,
    version_id: Optional[str] = None,
    note: str = "",
    tags: Optional[list[str]] = None,
) -> PinEntry:
    """Pin *encrypted_file* under *label* so its checksum is recorded."""
    if not encrypted_file.exists():
        raise PinError(f"Encrypted file not found: {encrypted_file}")
    if not label.strip():
        raise PinError("Label must not be empty.")

    directory = directory or encrypted_file.parent
    pins = _load_pins(directory)

    entry = PinEntry(
        label=label,
        file=str(encrypted_file),
        checksum=_checksum(encrypted_file),
        version_id=version_id,
        note=note,
        tags=tags or [],
    )
    pins[label] = entry.__dict__
    _save_pins(directory, pins)
    return entry


def verify_pin(label: str, encrypted_file: Path, *, directory: Optional[Path] = None) -> bool:
    """Return True if *encrypted_file* matches the pinned checksum for *label*."""
    directory = directory or encrypted_file.parent
    pins = _load_pins(directory)
    if label not in pins:
        raise PinError(f"No pin found for label: '{label}'")
    if not encrypted_file.exists():
        raise PinError(f"Encrypted file not found: {encrypted_file}")
    return _checksum(encrypted_file) == pins[label]["checksum"]


def list_pins(directory: Path) -> list[PinEntry]:
    """Return all pins recorded in *directory*."""
    return [
        PinEntry(**v) for v in _load_pins(directory).values()
    ]


def remove_pin(label: str, directory: Path) -> None:
    """Delete the pin for *label* from *directory*."""
    pins = _load_pins(directory)
    if label not in pins:
        raise PinError(f"No pin found for label: '{label}'")
    del pins[label]
    _save_pins(directory, pins)
