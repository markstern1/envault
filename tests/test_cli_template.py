"""Tests for the CLI template command group."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.cli_template import template_group, template_generate
from envault.template import TemplateError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path):
    """Create a sample encrypted .env.age file for testing."""
    enc = tmp_path / ".env.age"
    enc.write_text("fake encrypted content")
    return enc


class TestTemplateGenerate:
    def test_template_generate_success(self, runner, tmp_path):
        """Template generate should call generate_template and report success."""
        input_file = tmp_path / ".env"
        input_file.write_text("API_KEY=secret\nDB_HOST=localhost\n")
        output_file = tmp_path / ".env.template"

        with patch("envault.cli_template.generate_template") as mock_gen:
            result = runner.invoke(
                template_generate,
                [str(input_file), "--output", str(output_file)],
            )

        assert result.exit_code == 0
        mock_gen.assert_called_once_with(
            input_file=Path(str(input_file)),
            output_file=Path(str(output_file)),
            placeholder="",
        )
        assert "Template written" in result.output

    def test_template_generate_default_output(self, runner, tmp_path):
        """Without --output, should derive template path from input filename."""
        input_file = tmp_path / ".env"
        input_file.write_text("FOO=bar\n")

        with patch("envault.cli_template.generate_template") as mock_gen:
            result = runner.invoke(
                template_generate,
                [str(input_file)],
            )

        assert result.exit_code == 0
        called_output = mock_gen.call_args[1]["output_file"]
        assert str(called_output).endswith(".template")

    def test_template_generate_custom_placeholder(self, runner, tmp_path):
        """--placeholder flag should be forwarded to generate_template."""
        input_file = tmp_path / ".env"
        input_file.write_text("SECRET=value\n")
        output_file = tmp_path / ".env.template"

        with patch("envault.cli_template.generate_template") as mock_gen:
            result = runner.invoke(
                template_generate,
                [
                    str(input_file),
                    "--output", str(output_file),
                    "--placeholder", "CHANGE_ME",
                ],
            )

        assert result.exit_code == 0
        mock_gen.assert_called_once_with(
            input_file=Path(str(input_file)),
            output_file=Path(str(output_file)),
            placeholder="CHANGE_ME",
        )

    def test_template_generate_missing_input(self, runner, tmp_path):
        """Should exit non-zero when the input file does not exist."""
        missing = tmp_path / "nonexistent.env"

        result = runner.invoke(
            template_generate,
            [str(missing)],
        )

        assert result.exit_code != 0

    def test_template_generate_template_error(self, runner, tmp_path):
        """TemplateError raised by generate_template should surface as a CLI error."""
        input_file = tmp_path / ".env"
        input_file.write_text("KEY=value\n")
        output_file = tmp_path / ".env.template"

        with patch(
            "envault.cli_template.generate_template",
            side_effect=TemplateError("something went wrong"),
        ):
            result = runner.invoke(
                template_generate,
                [str(input_file), "--output", str(output_file)],
            )

        assert result.exit_code != 0
        assert "something went wrong" in result.output

    def test_template_group_help(self, runner):
        """The template group should expose a help message."""
        result = runner.invoke(template_group, ["--help"])
        assert result.exit_code == 0
        assert "template" in result.output.lower()
