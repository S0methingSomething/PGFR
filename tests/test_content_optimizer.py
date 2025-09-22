"""Tests for content optimizer."""

import pytest

from pgfr.services.content_optimizer import ContentOptimizer


@pytest.fixture
def content_optimizer():
    """Create content optimizer instance."""
    return ContentOptimizer()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "test_content"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def mock_html():
    """Mock HTML content with links and images."""
    return """
    <html>
        <body>
            <a href="/next-page">Next Chapter</a>
            <a href="/prev-page">Previous</a>
            <a href="https://external.com">External</a>
            <img src="/image1.jpg" alt="Image 1">
            <img src="/image2.png" alt="Image 2">
        </body>
    </html>
    """


class TestContentOptimizer:
    """Test content optimizer functionality."""

    def test_content_optimizer_init(self, content_optimizer):
        """Test content optimizer initialization."""
        assert content_optimizer.session is None
        assert content_optimizer.base_url is None

    @pytest.mark.asyncio
    async def test_find_linked_pages(self, content_optimizer, mock_html):
        """Test finding linked pages."""
        result = await content_optimizer._find_linked_pages(
            "https://example.com", mock_html
        )

        max_links = 5
        # Should find internal links, prioritize reading-related ones
        assert len(result) <= max_links  # Limited to 5
        assert any("next-page" in link for link in result)
        assert any("prev-page" in link for link in result)
        # External links should be filtered out
        assert not any("external.com" in link for link in result)

    @pytest.mark.asyncio
    async def test_fetch_and_optimize_page_no_session(self, content_optimizer):
        """Test page fetching without session."""
        result = await content_optimizer._fetch_and_optimize_page("https://example.com")
        assert result == ""

    @pytest.mark.asyncio
    async def test_optimize_single_image_no_session(
        self, content_optimizer, temp_output_dir
    ):
        """Test single image optimization without session."""
        result = await content_optimizer._optimize_single_image(
            "https://example.com/image.jpg", temp_output_dir
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_optimized_content_basic(
        self, content_optimizer, temp_output_dir
    ):
        """Test basic optimized content generation."""
        result = await content_optimizer._generate_optimized_content(
            "main content", [], temp_output_dir
        )
        assert result == "main content"
