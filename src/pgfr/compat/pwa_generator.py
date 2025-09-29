"""Termux-compatible PWA generator."""

import http.server
import json
import os
import socketserver
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from rich.console import Console

from .termux import TermuxContentOptimizer

HTTP_OK = 200
SHORT_NAME_MAX = 12
console = Console()


class PWAGeneratorError(Exception):
    """PWA generation error."""


class TermuxPWAGenerator:
    """Termux-compatible PWA generator."""

    def __init__(self) -> None:
        """Initialize Termux PWA generator."""

    async def generate_pwa(self, url: str, output_dir: Path, port: int) -> None:  # noqa: ARG002
        """Generate PWA files for Termux."""
        await self.generate(url, output_dir)

    async def generate(self, url: str, output_dir: Path) -> None:
        """Generate PWA files for Termux."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            async with aiohttp.ClientSession() as session:
                # Get site info
                site_info = await self._get_site_info(session, url)

                # Download logo (simplified)
                logo_path = await self._download_logo_simple(
                    session, site_info["icon"], output_dir
                )

                # Generate manifest
                await self._generate_manifest(site_info, logo_path, output_dir)

                # Generate HTML (with Termux optimizer)
                await self._generate_html(site_info, url, output_dir)

                # Generate service worker
                await self._generate_service_worker(output_dir)

        except Exception as e:
            raise PWAGeneratorError(f"Failed to generate PWA: {e!s}") from e

    async def _get_site_info(
        self, session: aiohttp.ClientSession, url: str
    ) -> dict[str, Any]:
        """Extract site information."""
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=5),  # Shorter timeout for Termux
            ) as response:
                if response.status != HTTP_OK:
                    raise PWAGeneratorError(
                        f"Failed to fetch {url}: HTTP {response.status}"
                    )
                html = await response.text()
        except aiohttp.ClientError as e:
            raise PWAGeneratorError(f"Network error accessing {url}: {e!s}") from e

        soup = BeautifulSoup(html, "html.parser")

        # Get title
        title = soup.find("title")
        title_text = title.text.strip() if title else urlparse(url).netloc

        # Get description (simplified)
        desc_meta = soup.find("meta", attrs={"name": "description"})
        description = "Reading app"
        if desc_meta and hasattr(desc_meta, "get"):
            description = desc_meta.get("content", "Reading app") or "Reading app"

        # Find icon (simplified)
        icon_link = soup.find("link", rel="icon")
        icon_url = "/favicon.ico"
        if icon_link and hasattr(icon_link, "get"):
            icon_url = icon_link.get("href") or "/favicon.ico"

        if not icon_url.startswith("http"):
            icon_url = urljoin(url, icon_url)

        return {
            "name": title_text,
            "short_name": (
                title_text[:SHORT_NAME_MAX]
                if len(title_text) > SHORT_NAME_MAX
                else title_text
            ),
            "description": description[:50],  # Shorter for Termux
            "icon": icon_url,
            "url": url,
        }

    async def _download_logo_simple(
        self, session: aiohttp.ClientSession, icon_url: str, output_dir: Path
    ) -> str:
        """Simple logo download for Termux."""
        try:
            async with session.get(
                icon_url, timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status == HTTP_OK:
                    content = await response.read()

                    # Simple filename
                    logo_path = output_dir / "icon-192.png"

                    async with aiofiles.open(logo_path, "wb") as f:
                        await f.write(content)

                    return "icon-192.png"
        except Exception:  # noqa: S110
            pass

        # Fallback: create simple icon
        return await self._create_simple_icon(output_dir)

    async def _create_simple_icon(self, output_dir: Path) -> str:
        """Create a simple text-based icon for Termux."""
        # Create simple SVG without complex gradients
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">
            <rect width="192" height="192" fill="#2196F3" rx="24"/>
            <text x="96" y="120" font-family="Arial, sans-serif" font-size="64" fill="white" text-anchor="middle">R</text>
        </svg>"""

        icon_path = output_dir / "icon-192.svg"
        async with aiofiles.open(icon_path, "w") as f:
            await f.write(svg_content)

        return "icon-192.svg"

    async def _generate_manifest(
        self, site_info: dict[str, Any], logo_path: str, output_dir: Path
    ) -> None:
        """Generate PWA manifest for Termux."""
        manifest = {
            "name": site_info["name"],
            "short_name": site_info["short_name"],
            "description": site_info["description"],
            "start_url": "/",
            "display": "fullscreen",
            "orientation": "portrait",  # Better for mobile
            "theme_color": "#2196F3",
            "background_color": "#ffffff",
            "scope": "/",
            "categories": ["books", "education"],
            "icons": [
                {
                    "src": logo_path,
                    "sizes": "192x192",
                    "type": "image/svg+xml"
                    if logo_path.endswith(".svg")
                    else "image/png",
                    "purpose": "any maskable",
                }
            ],
        }

        async with aiofiles.open(output_dir / "manifest.json", "w") as f:
            await f.write(json.dumps(manifest, indent=2))

    async def _generate_html(
        self, site_info: dict[str, Any], target_url: str, output_dir: Path
    ) -> None:
        """Generate HTML with Termux optimization."""
        # Use Termux optimizer
        optimizer = TermuxContentOptimizer()
        optimization_result = await optimizer.optimize_site(target_url, output_dir)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>{site_info["name"]}</title>
    <meta name="description" content="{site_info["description"]}">

    <!-- PWA Meta Tags -->
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#2196F3">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="{site_info["short_name"]}">

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            overflow: hidden;
        }}

        #frame {{
            width: 100vw;
            height: 100vh;
            border: none;
            background: #fff;
        }}

        .loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #fff;
            text-align: center;
            z-index: 1000;
        }}

        .loading-spinner {{
            width: 30px;
            height: 30px;
            border: 3px solid #333;
            border-top: 3px solid #2196F3;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 12px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .info {{
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 11px;
            z-index: 1001;
        }}
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="loading-spinner"></div>
        <div>Loading {site_info["name"]}...</div>
    </div>

    <div class="info" id="info" style="display: none;">
        Termux Mode: {optimization_result.get("preloaded_pages", 0)} pages
    </div>

    <iframe id="frame" src="{target_url}" style="display:none"></iframe>

    <script>
        // Register service worker
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('sw.js')
                .catch(err => console.log('SW registration failed'));
        }}

        const frame = document.getElementById('frame');
        const loading = document.getElementById('loading');
        const info = document.getElementById('info');

        let loadTimeout = setTimeout(() => {{
            loading.innerHTML = '<div>Connection timeout. Tap to retry.</div>';
            loading.onclick = () => location.reload();
        }}, 10000);

        frame.onload = () => {{
            clearTimeout(loadTimeout);
            loading.style.display = 'none';
            frame.style.display = 'block';

            // Show info briefly
            info.style.display = 'block';
            setTimeout(() => {{
                info.style.opacity = '0';
                setTimeout(() => info.style.display = 'none', 300);
            }}, 2000);
        }};
    </script>
</body>
</html>"""

        async with aiofiles.open(output_dir / "index.html", "w") as f:
            await f.write(html)

    async def _generate_service_worker(self, output_dir: Path) -> None:
        """Generate lightweight service worker for Termux."""
        sw_content = """const CACHE_NAME = 'termux-reader-v1';
const staticAssets = [
    '/',
    '/index.html',
    '/manifest.json'
];

// Simple install
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(staticAssets))
            .then(() => self.skipWaiting())
    );
});

// Simple fetch
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
            .catch(() => new Response('Offline'))
    );
});

// Clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});"""

        async with aiofiles.open(output_dir / "sw.js", "w") as f:
            await f.write(sw_content)

    async def serve(self, output_dir: Path, port: int) -> None:
        """Serve PWA locally (Termux compatible)."""
        os.chdir(output_dir)

        class Handler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self) -> None:
                self.send_header("Cache-Control", "no-cache")
                super().end_headers()

            def log_message(self, fmt: str, *args: Any) -> None:
                # Suppress logging for Termux
                pass

        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                console.print(
                    f"[green]✅ Termux server running at http://localhost:{port}[/green]"
                )
                console.print("[dim]• Use Termux:API to open in browser[/dim]")
                console.print("[dim]• Press Ctrl+C to stop[/dim]")
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e):
                console.print(
                    f"[red]Port {port} is already in use. Try a different port.[/red]"
                )
            else:
                console.print(f"[red]Server error: {e}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")
