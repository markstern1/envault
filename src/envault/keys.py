"""Key management utilities for envault."""

import subprocess
from pathlib import Path
from typing import Tuple

from envault.crypto import CryptoError

DEFAULT_KEY_DIR = Path.home() / ".age"
DEFAULT_KEY_FILE = DEFAULT_KEY_DIR / "key.txt"


def generate_keypair(output_path: Path = DEFAULT_KEY_FILE) -> Tuple[str, str]:
    """Generate a new age keypair and save the private key to disk.

    Args:
        output_path: Where to write the private key file.

    Returns:
        A tuple of (public_key, private_key_path_str).

    Raises:
        CryptoError: If age-keygen is not available or key generation fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["age-keygen", "--output", str(output_path)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise CryptoError(
            "'age-keygen' not found. Install age from https://github.com/FiloSottile/age"
        )

    if result.returncode != 0:
        raise CryptoError(f"Key generation failed: {result.stderr.strip()}")

    public_key = _extract_public_key(output_path)
    return public_key, str(output_path)


def _extract_public_key(key_file: Path) -> str:
    """Parse the public key from an age private key file.

    Args:
        key_file: Path to the age private key file.

    Returns:
        The public key string (age1...).

    Raises:
        CryptoError: If the public key cannot be found in the file.
    """
    for line in key_file.read_text().splitlines():
        if line.startswith("# public key:"):
            return line.split(":", 1)[1].strip()
    raise CryptoError(f"Could not extract public key from {key_file}")


def read_public_key(key_file: Path = DEFAULT_KEY_FILE) -> str:
    """Read the public key associated with an existing private key file.

    Args:
        key_file: Path to the age private key file.

    Returns:
        The public key string.

    Raises:
        CryptoError: If the key file does not exist.
    """
    if not key_file.exists():
        raise CryptoError(
            f"Key file not found: {key_file}. Run 'envault keygen' to create one."
        )
    return _extract_public_key(key_file)
