"""Diagnostics module for envault — checks that required tools and config are present."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    message: str

    def __str__(self) -> str:
        status = "✓" if self.ok else "✗"
        return f"[{status}] {self.name}: {self.message}"


@dataclass
class DoctorResult:
    checks: List[DoctorCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def failed(self) -> List[DoctorCheck]:
        return [c for c in self.checks if not c.ok]


def _check_age_binary() -> DoctorCheck:
    path = shutil.which("age")
    if path:
        return DoctorCheck("age binary", True, f"found at {path}")
    return DoctorCheck("age binary", False, "'age' not found in PATH — install from https://github.com/FiloSottile/age")


def _check_age_keygen_binary() -> DoctorCheck:
    path = shutil.which("age-keygen")
    if path:
        return DoctorCheck("age-keygen binary", True, f"found at {path}")
    return DoctorCheck("age-keygen binary", False, "'age-keygen' not found in PATH")


def _check_identity_file(identity: Path) -> DoctorCheck:
    if identity.exists():
        return DoctorCheck("identity file", True, f"found at {identity}")
    return DoctorCheck("identity file", False, f"{identity} does not exist — run 'envault keys generate'")


def _check_team_file(team_file: Path) -> DoctorCheck:
    if team_file.exists():
        return DoctorCheck("team file", True, f"found at {team_file}")
    return DoctorCheck("team file", False, f"{team_file} not found — run 'envault team add' to configure recipients")


def run_doctor(
    identity: Path = Path(".envault/identity.age"),
    team_file: Path = Path(".envault/team.json"),
) -> DoctorResult:
    """Run all diagnostic checks and return a DoctorResult."""
    result = DoctorResult()
    result.checks.append(_check_age_binary())
    result.checks.append(_check_age_keygen_binary())
    result.checks.append(_check_identity_file(identity))
    result.checks.append(_check_team_file(team_file))
    return result
