"""Key rotation support for envault."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .crypto import encrypt_file, decrypt_file, CryptoError
from .versioning import record_version, list_versions
from .audit import record_event


class RotationError(Exception):
    """Raised when a key rotation operation fails."""


def rotate_key(
    encrypted_file: Path,
    old_identity: Path,
    new_recipient: str,
    output: Optional[Path] = None,
    actor: str = "system",
) -> Path:
    """Decrypt with old identity and re-encrypt for new recipient.

    Args:
        encrypted_file: Path to the existing .age file.
        old_identity: Path to the old age private key file.
        new_recipient: age public key for the new recipient.
        output: Destination path for the rotated file. Defaults to overwriting.
        actor: Name/identifier of who triggered the rotation (for audit log).

    Returns:
        Path to the newly encrypted file.

    Raises:
        RotationError: If decryption or re-encryption fails.
    """
    if not encrypted_file.exists():
        raise RotationError(f"Encrypted file not found: {encrypted_file}")

    if not old_identity.exists():
        raise RotationError(f"Identity file not found: {old_identity}")

    tmp_plain = encrypted_file.with_suffix(".tmp_plain")
    destination = output or encrypted_file

    try:
        try:
            decrypt_file(encrypted_file, old_identity, tmp_plain)
        except CryptoError as exc:
            raise RotationError(f"Decryption failed during rotation: {exc}") from exc

        try:
            encrypt_file(tmp_plain, new_recipient, destination)
        except CryptoError as exc:
            raise RotationError(f"Re-encryption failed during rotation: {exc}") from exc

        record_version(destination, new_recipient)
        record_event(
            "rotate",
            str(destination),
            actor=actor,
            metadata={"new_recipient": new_recipient},
        )

        return destination
    finally:
        if tmp_plain.exists():
            tmp_plain.unlink()


def list_rotation_history(encrypted_file: Path) -> list[dict]:
    """Return version history for an encrypted file (acts as rotation log)."""
    return list_versions(encrypted_file)
