"""Version tracking for encrypted .env files."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

VERSION_FILE = ".envault_versions.json"


def _load_versions(version_file: Path) -> List[Dict]:
    if version_file.exists():
        return json.loads(version_file.read_text())
    return []


def _save_versions(version_file: Path, versions: List[Dict]) -> None:
    version_file.write_text(json.dumps(versions, indent=2))


def record_version(encrypted_file: Path, recipient: str, version_file: Optional[Path] = None) -> str:
    """Record a new version entry for an encrypted file.

    Args:
        encrypted_file: Path to the newly created encrypted file.
        recipient: The age public key used for encryption.
        version_file: Path to the version log JSON. Defaults to .envault_versions.json.

    Returns:
        The SHA-256 checksum of the encrypted file.
    """
    if version_file is None:
        version_file = encrypted_file.parent / VERSION_FILE

    checksum = _sha256(encrypted_file)
    versions = _load_versions(version_file)

    entry = {
        "file": encrypted_file.name,
        "checksum": checksum,
        "recipient": recipient,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": len(versions) + 1,
    }
    versions.append(entry)
    _save_versions(version_file, versions)
    return checksum


def list_versions(target_file: Path, version_file: Optional[Path] = None) -> List[Dict]:
    """Return all recorded versions for a given encrypted file.

    Args:
        target_file: The encrypted file to look up.
        version_file: Path to the version log JSON.

    Returns:
        List of version dicts, oldest first.
    """
    if version_file is None:
        version_file = target_file.parent / VERSION_FILE

    all_versions = _load_versions(version_file)
    return [v for v in all_versions if v["file"] == target_file.name]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()
