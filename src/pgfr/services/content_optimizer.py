"""Content optimization service for seamless reading."""

import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup, Tag

HTTP_OK = 200


class ContentOptimizer:
    """Optimize content for seamless reading experience."""

    def __init__(self) -> None:
        """Initialize the content optimizer."""
        self.session: aiohttp.ClientSession | None = None
        self.base_url: str | None = None

    async def optimize_site(self, url: str, output_dir: Path) -> dict[str, Any]:
        """Optimize entire site for offline reading."""
        self.base_url = url

        async with aiohttp.ClientSession() as session:
            self.session = session

            # Get main page
            main_content = await self._fetch_and_optimize_page(url)

            # Find and preload linked pages
            linked_pages = await self._find_linked_pages(url, main_content)

            # Optimize images
            optimized_images = await self._optimize_images(main_content, output_dir)

            # Generate optimized content
            optimized_content = await self._generate_optimized_content(
                main_content, linked_pages, output_dir
            )

            return {
                "main_content": optimized_content,
                "preloaded_pages": len(linked_pages),
                "optimized_images": len(optimized_images),
            }

    async def _fetch_and_optimize_page(self, url: str) -> str:
        """Fetch and optimize a single page."""
        if not self.session:
            return ""
        try:
            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == HTTP_OK:
                    return await response.text()
        except Exception:  # noqa: S110
            pass
        return ""

    async def _find_linked_pages(self, base_url: str, content: str) -> list[str]:
        """Find linked pages for preloading."""
        soup = BeautifulSoup(content, "html.parser")
        links: list[str] = []

        # Find navigation links, next/prev buttons, etc.
        for link in soup.find_all("a", href=True):
            if isinstance(link, Tag):
                href = link.get("href")
                if href and not str(href).startswith(("#", "javascript:", "mailto:")):
                    full_url = urljoin(base_url, str(href))

                    # Only include same-domain links
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        # Prioritize reading-related links
                        link_text = link.get_text().lower()
                        if any(
                            word in link_text
                            for word in ["next", "continue", "chapter", "page"]
                        ):
                            links.insert(0, full_url)  # Priority links first
                        else:
                            links.append(full_url)

        # Limit to prevent excessive preloading
        return links[:5]

    async def _optimize_images(self, content: str, output_dir: Path) -> dict[str, str]:
        """Optimize and cache images."""
        soup = BeautifulSoup(content, "html.parser")
        optimized_images: dict[str, str] = {}

        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        tasks = []
        for img in soup.find_all("img", src=True):
            if isinstance(img, Tag):
                src = img.get("src")
                if src and not str(src).startswith("data:"):
                    full_url = urljoin(self.base_url or "", str(src))
                    tasks.append(self._optimize_single_image(full_url, images_dir))

        # Process images concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict):
                optimized_images.update(result)

        return optimized_images

    async def _optimize_single_image(
        self, img_url: str, images_dir: Path
    ) -> dict[str, str]:
        """Optimize a single image."""
        if not self.session:
            return {}
        try:
            async with self.session.get(
                img_url, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == HTTP_OK:
                    content = await response.read()

                    # Generate filename
                    filename = f"img_{hash(img_url) % 10000}.webp"
                    filepath = images_dir / filename

                    # For now, just save as-is (could add image compression here)
                    async with aiofiles.open(filepath, "wb") as f:
                        await f.write(content)

                    return {img_url: f"images/{filename}"}
        except Exception:  # noqa: S110
            pass
        return {}

    async def _generate_optimized_content(
        self, main_content: str, linked_pages: list[str], output_dir: Path
    ) -> str:
        """Generate optimized HTML with preloading and caching."""
        # Preload linked pages
        preloaded_content = {}
        for url in linked_pages[:3]:  # Limit concurrent preloads
            content = await self._fetch_and_optimize_page(url)
            if content:
                preloaded_content[url] = content

        # Save preloaded content
        if preloaded_content:
            preload_js = (
                "const preloadedPages = "
                + str(preloaded_content).replace("'", '"')
                + ";"
            )
            async with aiofiles.open(output_dir / "preloaded.js", "w") as f:
                await f.write(preload_js)

        return main_content
