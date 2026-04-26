"""Integration tests: diff of real decrypted files via mocked age."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_diff import diff_group


@pytest.fixture()
def setup_env_pair(tmp_path: Path):
    old_plain = tmp_path / "old.env"
    new_plain = tmp_path / "new.env"
    old_plain.write_text("DB_URL=postgres://old\nSECRET=abc\n")
    new_plain.write_text("DB_URL=postgres://new\nSECRET=abc\nEXTRA=1\n")
    return old_plain, new_plain


def test_diff_integration_plain_changed_lines(setup_env_pair):
    old, new = setup_env_pair
    runner = CliRunner()
    result = runner.invoke(diff_group, ["plain", str(old), str(new), "--no-color"])
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "EXTRA" in result.output


def test_diff_integration_plain_unchanged_secret(setup_env_pair):
    """SECRET line should appear in context but not as a change."""
    old, new = setup_env_pair
    runner = CliRunner()
    result = runner.invoke(diff_group, ["plain", str(old), str(new), "--no-color"])
    # SECRET unchanged — should not appear with leading +/- in a change line
    change_lines = [l for l in result.output.splitlines() if l.startswith(('+SECRET', '-SECRET'))]
    assert change_lines == []


def test_diff_encrypted_integration(tmp_path: Path):
    """Encrypted diff decrypts to temp files and diffs them."""
    old_enc = tmp_path / "old.env.age"
    new_enc = tmp_path / "new.env.age"
    identity = tmp_path / "id.txt"
    old_enc.write_text("enc_old")
    new_enc.write_text("enc_new")
    identity.write_text("AGE-SECRET-KEY-1")

    def fake_decrypt(src, dst, ident):
        if "old" in dst.name:
            dst.write_text("KEY=old_value\n")
        else:
            dst.write_text("KEY=new_value\n")

    runner = CliRunner()
    with patch("envault.diff.decrypt_file", side_effect=fake_decrypt):
        result = runner.invoke(
            diff_group,
            ["encrypted", str(old_enc), str(new_enc), "-i", str(identity), "--no-color"],
        )

    assert result.exit_code == 0
    assert "KEY" in result.output
