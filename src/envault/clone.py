"""Clone an encrypted .env file for a different recipient."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .crypto import CryptoError, decrypt_file, encrypt_file
from .audit import record_event


class CloneError(Exception):  # noqa: N818
    """Raised when cloning fails."""


@dataclass
class CloneResult:
    source: Path
    destination: Path
    recipient: str

    @property
    def summary(self) -> str:
        return (
            f"Cloned {self.source} -> {self.destination} "
            f"for recipient {self.recipient}"
        )


def clone_for_recipient(
    encrypted_path: Path,
    identity_path: Path,
    recipient: str,
    output_path: Path | None = None,
    *,
    actor: str = "envault",
    tmp_dir: Path | None = None,
) -> CloneResult:
    """Decrypt *encrypted_path* with *identity_path*, then re-encrypt for *recipient*.

    Parameters
    ----------
    encrypted_path:
        Path to the source ``.age`` file.
    identity_path:
        Age identity (private key) file used to decrypt the source.
    recipient:
        Age public key of the target recipient.
    output_path:
        Where to write the cloned file.  Defaults to
        ``<stem>.<recipient[:8]>.age`` next to the source.
    actor:
        Username recorded in the audit log.
    tmp_dir:
        Directory for the temporary plaintext file.  Defaults to the
        parent of *encrypted_path*.
    """
    if not encrypted_path.exists():
        raise CloneError(f"Source file not found: {encrypted_path}")
    if not identity_path.exists():
        raise CloneError(f"Identity file not found: {identity_path}")
    if not recipient.startswith("age1"):
        raise CloneError(f"Invalid recipient key (must start with 'age1'): {recipient}")

    base_dir = tmp_dir or encrypted_path.parent
    tmp_plain = base_dir / f".envault_clone_tmp_{encrypted_path.stem}.env"

    if output_path is None:
        short = recipient[:8]
        output_path = encrypted_path.parent / f"{encrypted_path.stem}.{short}.age"

    try:
        decrypt_file(encrypted_path, identity_path, tmp_plain)
        encrypt_file(tmp_plain, recipient, output_path)
    except CryptoError as exc:
        raise CloneError(str(exc)) from exc
    finally:
        if tmp_plain.exists():
            tmp_plain.unlink()

    record_event(
        action="clone",
        path=str(output_path),
        actor=actor,
        meta={"source": str(encrypted_path), "recipient": recipient},
    )

    return CloneResult(source=encrypted_path, destination=output_path, recipient=recipient)
