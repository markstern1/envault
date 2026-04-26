"""Unit tests for src/envault/export.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.export import export_env, export_file, ExportError


SAMPLE_ENV = """
# database config
DB_HOST=localhost
DB_PORT=5432
DB_NAME="mydb"
SECRET_KEY='s3cr3t'
"""


def test_export_shell_format():
    result = export_env(SAMPLE_ENV, "shell")
    assert 'export DB_HOST="localhost"' in result
    assert 'export DB_PORT="5432"' in result
    assert 'export SECRET_KEY="s3cr3t"' in result


def test_export_dotenv_format():
    result = export_env(SAMPLE_ENV, "dotenv")
    assert 'DB_HOST="localhost"' in result
    assert not result.startswith("export")


def test_export_json_format():
    result = export_env(SAMPLE_ENV, "json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"
    assert data["SECRET_KEY"] == "s3cr3t"
    assert data["DB_NAME"] == "mydb"


def test_export_strips_quotes():
    result = export_env('KEY="value with spaces"', "json")
    data = json.loads(result)
    assert data["KEY"] == "value with spaces"


def test_export_ignores_comments_and_blanks():
    result = export_env("# comment\n\nFOO=bar", "json")
    data = json.loads(result)
    assert list(data.keys()) == ["FOO"]


def test_export_unknown_format_raises():
    with pytest.raises(ExportError, match="Unknown export format"):
        export_env("FOO=bar", "xml")  # type: ignore[arg-type]


def test_export_file_reads_path(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=production\n")
    result = export_file(env_file, "shell")
    assert 'export APP_ENV="production"' in result


def test_export_file_missing_raises(tmp_path: Path):
    with pytest.raises(ExportError, match="File not found"):
        export_file(tmp_path / "nonexistent.env")
