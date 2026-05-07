"""Tests for envault.doctor diagnostics module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envault.doctor import (
    DoctorCheck,
    DoctorResult,
    _check_age_binary,
    _check_age_keygen_binary,
    _check_identity_file,
    _check_team_file,
    run_doctor,
)


def test_doctor_check_str_ok():
    check = DoctorCheck("age binary", True, "found at /usr/bin/age")
    assert str(check) == "[✓] age binary: found at /usr/bin/age"


def test_doctor_check_str_fail():
    check = DoctorCheck("age binary", False, "not found")
    assert str(check) == "[✗] age binary: not found"


def test_doctor_result_passed_when_all_ok():
    result = DoctorResult(checks=[
        DoctorCheck("a", True, "ok"),
        DoctorCheck("b", True, "ok"),
    ])
    assert result.passed is True
    assert result.failed == []


def test_doctor_result_failed_lists_bad_checks():
    bad = DoctorCheck("age binary", False, "missing")
    result = DoctorResult(checks=[
        DoctorCheck("a", True, "ok"),
        bad,
    ])
    assert result.passed is False
    assert result.failed == [bad]


def test_check_age_binary_found():
    with patch("envault.doctor.shutil.which", return_value="/usr/bin/age"):
        check = _check_age_binary()
    assert check.ok is True
    assert "/usr/bin/age" in check.message


def test_check_age_binary_missing():
    with patch("envault.doctor.shutil.which", return_value=None):
        check = _check_age_binary()
    assert check.ok is False
    assert "not found" in check.message


def test_check_age_keygen_found():
    with patch("envault.doctor.shutil.which", return_value="/usr/bin/age-keygen"):
        check = _check_age_keygen_binary()
    assert check.ok is True


def test_check_identity_file_exists(tmp_path):
    identity = tmp_path / "identity.age"
    identity.write_text("AGE-SECRET-KEY-...")
    check = _check_identity_file(identity)
    assert check.ok is True


def test_check_identity_file_missing(tmp_path):
    identity = tmp_path / "identity.age"
    check = _check_identity_file(identity)
    assert check.ok is False
    assert "keys generate" in check.message


def test_check_team_file_exists(tmp_path):
    team = tmp_path / "team.json"
    team.write_text("{}")
    check = _check_team_file(team)
    assert check.ok is True


def test_check_team_file_missing(tmp_path):
    team = tmp_path / "team.json"
    check = _check_team_file(team)
    assert check.ok is False
    assert "team add" in check.message


def test_run_doctor_all_pass(tmp_path):
    identity = tmp_path / "identity.age"
    identity.write_text("key")
    team = tmp_path / "team.json"
    team.write_text("{}")
    with patch("envault.doctor.shutil.which", return_value="/usr/bin/age"):
        result = run_doctor(identity=identity, team_file=team)
    assert result.passed is True
    assert len(result.checks) == 4


def test_run_doctor_partial_failure(tmp_path):
    identity = tmp_path / "identity.age"  # does not exist
    team = tmp_path / "team.json"          # does not exist
    with patch("envault.doctor.shutil.which", return_value="/usr/bin/age"):
        result = run_doctor(identity=identity, team_file=team)
    assert result.passed is False
    assert len(result.failed) == 2
