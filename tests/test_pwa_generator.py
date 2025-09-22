"""Tests for PWA generator."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from pgfr.services.pwa_generator import PWAGenerator, PWAGeneratorError


@pytest.fixture
def pwa_generator():
    """Create PWA generator instance."""
    return PWAGenerator()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "test_pwa"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


class TestPWAGenerator:
    """Test PWA generator functionality."""

    @pytest.mark.asyncio
    async def test_generate_manifest(self, pwa_generator, temp_output_dir):
        """Test manifest generation."""
        site_info = {
            "name": "Test App",
            "short_name": "Test",
            "description": "Test description",
        }

        await pwa_generator._generate_manifest(site_info, "icon.png", temp_output_dir)

        manifest_file = temp_output_dir / "manifest.json"
        assert manifest_file.exists()

        with manifest_file.open() as f:
            manifest = json.load(f)

        assert manifest["name"] == "Test App"
        assert manifest["short_name"] == "Test"
        assert manifest["display"] == "fullscreen"
        expected_icons = 2
        assert len(manifest["icons"]) == expected_icons

    @pytest.mark.asyncio
    async def test_generate_service_worker(self, pwa_generator, temp_output_dir):
        """Test service worker generation."""
        await pwa_generator._generate_service_worker(temp_output_dir)

        sw_file = temp_output_dir / "sw.js"
        assert sw_file.exists()

        content = sw_file.read_text()
        assert "pwa-reader-v2" in content
        assert "addEventListener" in content
        assert "caches" in content

    @pytest.mark.asyncio
    async def test_create_fallback_icon(self, pwa_generator, temp_output_dir):
        """Test fallback icon creation."""
        result = await pwa_generator._create_fallback_icon(temp_output_dir)

        assert result == "icon-192.svg"
        icon_file = temp_output_dir / "icon-192.svg"
        assert icon_file.exists()

        content = icon_file.read_text()
        assert "svg" in content
        assert "📖" in content

    def test_pwa_generator_error_creation(self):
        """Test PWA generator error creation."""
        error = PWAGeneratorError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    @pytest.mark.asyncio
    async def test_generate_html_with_mock_optimizer(
        self, pwa_generator, temp_output_dir
    ):
        """Test HTML generation with mocked optimizer."""
        site_info = {
            "name": "Test App",
            "short_name": "Test",
            "description": "Test description",
        }

        with patch(
            "pgfr.services.pwa_generator.ContentOptimizer"
        ) as mock_optimizer_class:
            mock_optimizer = AsyncMock()
            mock_optimizer.optimize_site.return_value = {
                "preloaded_pages": 2,
                "optimized_images": 5,
            }
            mock_optimizer_class.return_value = mock_optimizer

            await pwa_generator._generate_html(
                site_info, "https://example.com", temp_output_dir
            )

        html_file = temp_output_dir / "index.html"
        assert html_file.exists()

        content = html_file.read_text()
        assert "Test App" in content
        assert "https://example.com" in content
