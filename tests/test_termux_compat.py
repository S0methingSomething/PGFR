"""Tests for Termux compatibility layer."""

import json
from unittest.mock import patch

import pytest

from pgfr.compat.pwa_generator import TermuxPWAGenerator
from pgfr.compat.termux import TermuxContentOptimizer, is_termux


@pytest.fixture
def termux_optimizer():
    """Create Termux content optimizer instance."""
    return TermuxContentOptimizer()


@pytest.fixture
def termux_generator():
    """Create Termux PWA generator instance."""
    return TermuxPWAGenerator()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "test_termux"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


class TestTermuxDetection:
    """Test Termux environment detection."""

    def test_is_termux_false_by_default(self):
        """Test that is_termux returns False in normal environment."""
        assert is_termux() is False

    @patch.dict("os.environ", {"PREFIX": "/data/data/com.termux/files/usr"})
    def test_is_termux_true_with_prefix(self):
        """Test that is_termux returns True with Termux PREFIX."""
        assert is_termux() is True

    @patch("pgfr.compat.termux.Path")
    def test_is_termux_true_with_path(self, mock_path_class):
        """Test that is_termux returns True when Termux path exists."""
        mock_path_class.return_value.exists.return_value = True
        assert is_termux() is True


class TestTermuxContentOptimizer:
    """Test Termux content optimizer."""

    def test_termux_optimizer_init(self, termux_optimizer):
        """Test Termux optimizer initialization."""
        assert termux_optimizer.session is None
        assert termux_optimizer.base_url is None

    @pytest.mark.asyncio
    async def test_find_linked_pages_limited(self, termux_optimizer):
        """Test that Termux optimizer limits linked pages."""
        html = """
        <html><body>
            <a href="/page1">Next</a>
            <a href="/page2">Continue</a>
            <a href="/page3">Chapter</a>
            <a href="/page4">Page</a>
            <a href="/page5">More</a>
        </body></html>
        """

        result = await termux_optimizer._find_linked_pages("https://example.com", html)

        max_termux_links = 3
        # Should be limited to 3 for Termux
        assert len(result) <= max_termux_links

    @pytest.mark.asyncio
    async def test_fetch_page_no_session(self, termux_optimizer):
        """Test page fetching without session."""
        result = await termux_optimizer._fetch_and_optimize_page("https://example.com")
        assert result == ""


class TestTermuxPWAGenerator:
    """Test Termux PWA generator."""

    @pytest.mark.asyncio
    async def test_create_simple_icon(self, termux_generator, temp_output_dir):
        """Test simple icon creation for Termux."""
        result = await termux_generator._create_simple_icon(temp_output_dir)

        assert result == "icon-192.svg"
        icon_file = temp_output_dir / "icon-192.svg"
        assert icon_file.exists()

        content = icon_file.read_text()
        assert "svg" in content
        assert "#2196F3" in content  # Termux blue color

    @pytest.mark.asyncio
    async def test_generate_manifest_termux(self, termux_generator, temp_output_dir):
        """Test manifest generation for Termux."""
        site_info = {
            "name": "Test App",
            "short_name": "Test",
            "description": "Test description",
        }

        await termux_generator._generate_manifest(
            site_info, "icon.svg", temp_output_dir
        )

        manifest_file = temp_output_dir / "manifest.json"
        assert manifest_file.exists()

        with manifest_file.open() as f:
            manifest = json.load(f)

        assert manifest["name"] == "Test App"
        assert manifest["orientation"] == "portrait"  # Termux specific
        assert manifest["theme_color"] == "#2196F3"  # Termux blue

    @pytest.mark.asyncio
    async def test_generate_service_worker_simple(
        self, termux_generator, temp_output_dir
    ):
        """Test simple service worker generation for Termux."""
        await termux_generator._generate_service_worker(temp_output_dir)

        sw_file = temp_output_dir / "sw.js"
        assert sw_file.exists()

        content = sw_file.read_text()
        assert "termux-reader-v1" in content
        assert "Simple install" in content  # Termux specific comment
