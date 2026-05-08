"""Inject decrypted .env values into a subprocess environment."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .crypto import decrypt_file, CryptoError
from .export import _parse_env_lines, ExportError


class InjectError(Exception):
    """Raised when injection fails."""


@dataclass
class InjectResult:
    command: list[str]
    returncode: int
    injected_keys: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _decrypt_to_env(encrypted: Path, identity: Path) -> dict[str, str]:
    """Decrypt an age-encrypted .env file and return its key/value pairs."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".env", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        decrypt_file(encrypted, tmp_path, identity)
        lines = tmp_path.read_text().splitlines()
        return _parse_env_lines(lines)
    except (CryptoError, ExportError) as exc:
        raise InjectError(f"Failed to decrypt {encrypted}: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


def inject_run(
    encrypted: Path,
    identity: Path,
    command: Sequence[str],
    *,
    override: bool = False,
    extra_env: dict[str, str] | None = None,
) -> InjectResult:
    """Run *command* with decrypted env vars injected into its environment.

    Args:
        encrypted: Path to the age-encrypted .env file.
        identity: Path to the age identity (private key) file.
        command: The command and arguments to execute.
        override: When True, decrypted values override existing env vars.
        extra_env: Additional variables to merge (applied after decryption).

    Returns:
        InjectResult with the process return code and injected key names.
    """
    if not encrypted.exists():
        raise InjectError(f"Encrypted file not found: {encrypted}")
    if not identity.exists():
        raise InjectError(f"Identity file not found: {identity}")
    if not command:
        raise InjectError("No command provided.")

    decrypted = _decrypt_to_env(encrypted, identity)
    if extra_env:
        decrypted.update(extra_env)

    env = dict(os.environ)
    if override:
        env.update(decrypted)
    else:
        for k, v in decrypted.items():
            env.setdefault(k, v)

    result = subprocess.run(list(command), env=env)
    return InjectResult(
        command=list(command),
        returncode=result.returncode,
        injected_keys=list(decrypted.keys()),
    )
