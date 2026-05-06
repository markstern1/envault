"""Tests for src/envault/rename.py."""

from pathlib import Path

import pytest

from envault.rename import RenameError, RenameResult, rename_key


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "# database settings\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "SECRET_KEY=abc123\n",
        encoding="utf-8",
    )
    return p


def test_rename_key_success(env_file: Path) -> None:
    result = rename_key(env_file, "DB_HOST", "DATABASE_HOST")
    assert result.ok
    assert result.renamed == [("DB_HOST", "DATABASE_HOST")]
    assert result.skipped == []
    content = env_file.read_text()
    assert "DATABASE_HOST=localhost" in content
    assert "DB_HOST" not in content


def test_rename_key_not_found(env_file: Path) -> None:
    result = rename_key(env_file, "MISSING_KEY", "NEW_KEY")
    assert not result.ok
    assert result.skipped == ["MISSING_KEY"]
    assert result.renamed == []
    # file should be unchanged
    assert "DB_HOST=localhost" in env_file.read_text()


def test_rename_key_dry_run_does_not_write(env_file: Path) -> None:
    original = env_file.read_text()
    result = rename_key(env_file, "DB_HOST", "DATABASE_HOST", dry_run=True)
    assert result.renamed == [("DB_HOST", "DATABASE_HOST")]
    assert env_file.read_text() == original


def test_rename_key_custom_output(env_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "new.env"
    rename_key(env_file, "SECRET_KEY", "APP_SECRET", output=out)
    assert out.exists()
    assert "APP_SECRET=abc123" in out.read_text()
    # original unchanged
    assert "SECRET_KEY=abc123" in env_file.read_text()


def test_rename_key_preserves_comments(env_file: Path) -> None:
    rename_key(env_file, "DB_PORT", "DATABASE_PORT")
    content = env_file.read_text()
    assert "# database settings" in content


def test_rename_key_missing_file(tmp_path: Path) -> None:
    with pytest.raises(RenameError, match="File not found"):
        rename_key(tmp_path / "nonexistent.env", "KEY", "NEW_KEY")


def test_rename_key_empty_old_key(env_file: Path) -> None:
    with pytest.raises(RenameError, match="old_key must not be empty"):
        rename_key(env_file, "  ", "NEW_KEY")


def test_rename_key_empty_new_key(env_file: Path) -> None:
    with pytest.raises(RenameError, match="new_key must not be empty"):
        rename_key(env_file, "DB_HOST", "")


def test_rename_result_summary_shows_both(env_file: Path) -> None:
    result = RenameResult(
        renamed=[("OLD", "NEW")],
        skipped=["GHOST"],
    )
    summary = result.summary()
    assert "OLD -> NEW" in summary
    assert "GHOST" in summary


def test_rename_result_empty_summary() -> None:
    result = RenameResult()
    assert "nothing to do" in result.summary()
