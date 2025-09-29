"""Test interactive CLI."""

from unittest.mock import AsyncMock, patch

import pytest

from pgfr.cli.main import _generate_pwa

DEFAULT_PORT = 8080


class TestInteractiveCLI:
    """Test interactive CLI functionality."""

    @pytest.mark.asyncio
    @patch("pgfr.cli.main.PWAGenerator")
    async def test_generate_pwa(self, mock_generator_class):
        """Test PWA generation function."""
        mock_generator = AsyncMock()
        mock_generator_class.return_value = mock_generator

        await _generate_pwa("https://example.com", "./test-pwa", DEFAULT_PORT)

        mock_generator.generate_pwa.assert_called_once()
        args = mock_generator.generate_pwa.call_args[0]
        assert args[0] == "https://example.com"
        assert str(args[1]) == "test-pwa"
        assert args[2] == DEFAULT_PORT

    @pytest.mark.asyncio
    @patch("pgfr.cli.main.PWAGenerator")
    async def test_generate_pwa_adds_https(self, mock_generator_class):
        """Test URL gets https prefix."""
        mock_generator = AsyncMock()
        mock_generator_class.return_value = mock_generator

        await _generate_pwa("example.com", "./test-pwa", DEFAULT_PORT)

        args = mock_generator.generate_pwa.call_args[0]
        assert args[0] == "https://example.com"
