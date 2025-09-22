"""Tests for CLI functionality."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from pgfr.cli.main import app


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


class TestCLI:
    """Test CLI functionality."""

    def test_info_command(self, cli_runner):
        """Test info command."""
        result = cli_runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "PGFR - PWA Generator for Reading" in result.stdout
        assert "Features:" in result.stdout

    @patch("pgfr.cli.main._generate_wrapper")
    def test_generate_command_non_interactive(self, mock_generate, cli_runner):
        """Test generate command in non-interactive mode."""
        mock_generate.return_value = None

        result = cli_runner.invoke(
            app,
            [
                "generate",
                "https://example.com",
                "--no-interactive",
                "--output-dir",
                "./test-pwa",
                "--port",
                "8080",
            ],
        )

        assert result.exit_code == 0

    def test_generate_command_no_url_non_interactive(self, cli_runner):
        """Test generate command without URL in non-interactive mode."""
        result = cli_runner.invoke(app, ["generate", "--no-interactive"])

        assert result.exit_code == 1
        assert "Error: URL is required in non-interactive mode" in result.stdout

    @patch("pgfr.cli.main._generate_wrapper")
    def test_generate_command_interactive(self, mock_interactive, cli_runner):
        """Test generate command in interactive mode."""
        mock_interactive.return_value = None

        result = cli_runner.invoke(app, ["generate", "--interactive"])

        assert result.exit_code == 0
