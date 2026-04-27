"""Tests for src/envault/template.py and src/envault/cli_template.py."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.template import TemplateError, generate_template
from envault.cli_template import template_group


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "# Database\nDB_HOST=localhost\nDB_PORT=5432\n\n# App\nSECRET_KEY=supersecret\n"
    )
    return p


def test_generate_template_creates_file(env_file: Path) -> None:
    dest = generate_template(env_file)
    assert dest.exists()
    assert dest.name == ".env.template"


def test_generate_template_blanks_values(env_file: Path) -> None:
    dest = generate_template(env_file)
    content = dest.read_text()
    assert "DB_HOST=" in content
    assert "localhost" not in content
    assert "supersecret" not in content


def test_generate_template_preserves_comments(env_file: Path) -> None:
    dest = generate_template(env_file)
    content = dest.read_text()
    assert "# Database" in content
    assert "# App" in content


def test_generate_template_custom_placeholder(env_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.template"
    generate_template(env_file, output=out, placeholder="CHANGE_ME")
    content = out.read_text()
    assert "DB_HOST=CHANGE_ME" in content
    assert "SECRET_KEY=CHANGE_ME" in content


def test_generate_template_custom_output(env_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "custom.template"
    result = generate_template(env_file, output=out)
    assert result == out
    assert out.exists()


def test_generate_template_missing_source(tmp_path: Path) -> None:
    with pytest.raises(TemplateError, match="not found"):
        generate_template(tmp_path / "missing.env")


def test_generate_template_no_assignments(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("# just a comment\n\n")
    with pytest.raises(TemplateError, match="No valid"):
        generate_template(p)


# --- CLI tests ---


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_template_generate_success(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(template_group, ["generate", str(env_file)])
    assert result.exit_code == 0
    assert "Template written to" in result.output
    assert env_file.with_suffix(".template").exists()


def test_cli_template_generate_with_placeholder(runner: CliRunner, env_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "t.template"
    result = runner.invoke(
        template_group,
        ["generate", str(env_file), "--output", str(out), "--placeholder", "TODO"],
    )
    assert result.exit_code == 0
    assert "TODO" in out.read_text()


def test_cli_template_generate_missing_file(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(template_group, ["generate", str(tmp_path / "ghost.env")])
    assert result.exit_code != 0
