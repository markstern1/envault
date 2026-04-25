"""Cryptographic operations for envault using age encryption."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class CryptoError(Exception):
    """Raised when an encryption or decryption operation fails."""
    pass


def encrypt_file(input_path: Path, output_path: Path, recipient: str) -> None:
    """Encrypt a file using age encryption for a given recipient.

    Args:
        input_path: Path to the plaintext file to encrypt.
        output_path: Path where the encrypted file will be written.
        recipient: age public key of the recipient.

    Raises:
        CryptoError: If the age binary is not found or encryption fails.
    """
    try:
        result = subprocess.run(
            ["age", "--recipient", recipient, "--output", str(output_path), str(input_path)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise CryptoError(
            "'age' binary not found. Install it from https://github.com/FiloSottile/age"
        )

    if result.returncode != 0:
        raise CryptoError(f"Encryption failed: {result.stderr.strip()}")


def decrypt_file(input_path: Path, output_path: Path, identity_path: Optional[Path] = None) -> None:
    """Decrypt an age-encrypted file.

    Args:
        input_path: Path to the encrypted .age file.
        output_path: Path where the decrypted file will be written.
        identity_path: Path to the age identity (private key) file.
                       Defaults to ~/.age/key.txt if not provided.

    Raises:
        CryptoError: If the age binary is not found or decryption fails.
    """
    if identity_path is None:
        identity_path = Path.home() / ".age" / "key.txt"

    if not identity_path.exists():
        raise CryptoError(f"Identity file not found: {identity_path}")

    try:
        result = subprocess.run(
            [
                "age",
                "--decrypt",
                "--identity",
                str(identity_path),
                "--output",
                str(output_path),
                str(input_path),
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise CryptoError(
            "'age' binary not found. Install it from https://github.com/FiloSottile/age"
        )

    if result.returncode != 0:
        raise CryptoError(f"Decryption failed: {result.stderr.strip()}")
