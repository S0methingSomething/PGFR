"""PWA generator service with enhanced user experience."""

import http.server
import json
import os
import socketserver
import webbrowser
from pathlib import Path
from threading import Timer
from typing import Any
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from rich.console import Console

from .content_optimizer import ContentOptimizer

# Import compatibility layer
try:
    from ..compat.pwa_generator import TermuxPWAGenerator
    from ..compat.termux import is_termux

    TERMUX_AVAILABLE = True
except ImportError:
    TERMUX_AVAILABLE = False

    def is_termux() -> bool:
        """Fallback function when Termux compatibility unavailable."""
        return False


HTTP_OK = 200
SHORT_NAME_MAX = 12
console = Console()


class PWAGeneratorError(Exception):
    """PWA generation error."""


class PWAGenerator:
    """Generate PWA from website with environment compatibility."""

    def __new__(cls, *_args: Any, **_kwargs: Any) -> Any:
        """Create appropriate generator based on environment."""
        if TERMUX_AVAILABLE and is_termux():
            console.print(
                "[yellow]🤖 Detected Termux environment - "
                "using compatibility mode[/yellow]"
            )
            return TermuxPWAGenerator()
        return super().__new__(cls)

    async def generate(self, url: str, output_dir: Path) -> None:
        """Generate PWA files."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            async with aiohttp.ClientSession() as session:
                # Get site info
                site_info = await self._get_site_info(session, url)

                # Download logo
                logo_path = await self._download_logo(
                    session, site_info["icon"], output_dir
                )

                # Generate manifest
                await self._generate_manifest(site_info, logo_path, output_dir)

                # Generate HTML
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
                url, timeout=aiohttp.ClientTimeout(total=10)
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

        # Get description
        desc_meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if desc_meta and hasattr(desc_meta, "get"):
            description = desc_meta.get("content", "Reading app") or "Reading app"
        else:
            description = "Reading app"

        # Find icon
        icon_link = (
            soup.find("link", rel="apple-touch-icon")
            or soup.find("link", rel="icon")
            or soup.find("link", rel="shortcut icon")
        )

        if icon_link and hasattr(icon_link, "get"):
            icon_url = icon_link.get("href") or "/favicon.ico"
        else:
            icon_url = "/favicon.ico"
        if not icon_url.startswith("http"):
            icon_url = urljoin(url, icon_url)

        return {
            "name": title_text,
            "short_name": (
                title_text[:SHORT_NAME_MAX]
                if len(title_text) > SHORT_NAME_MAX
                else title_text
            ),
            "description": description[:100],
            "icon": icon_url,
            "url": url,
        }

    async def _download_logo(
        self,
        session: aiohttp.ClientSession,
        icon_url: str,
        output_dir: Path,
    ) -> str:
        """Download and save logo."""
        try:
            async with session.get(
                icon_url, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == HTTP_OK:
                    content = await response.read()

                    # Determine file extension
                    content_type = response.headers.get("content-type", "")
                    if "svg" in content_type:
                        ext = "svg"
                    elif "png" in content_type:
                        ext = "png"
                    elif "jpg" in content_type or "jpeg" in content_type:
                        ext = "jpg"
                    else:
                        ext = "png"  # default

                    logo_path = output_dir / f"icon-192.{ext}"

                    async with aiofiles.open(logo_path, "wb") as f:
                        await f.write(content)

                    return f"icon-192.{ext}"
        except Exception:  # noqa: S110
            pass

        # Fallback: create simple icon
        return await self._create_fallback_icon(output_dir)

    async def _create_fallback_icon(self, output_dir: Path) -> str:
        """Create a simple fallback icon."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 192 192">
            <defs>
                <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#4285f4;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#34a853;stop-opacity:1" />
                </linearGradient>
            </defs>
            <rect width="192" height="192" fill="url(#grad)" rx="24"/>
            <text x="96" y="120" font-family="Arial, sans-serif" font-size="64" fill="white" text-anchor="middle">📖</text>
        </svg>"""

        icon_path = output_dir / "icon-192.svg"
        async with aiofiles.open(icon_path, "w") as f:
            await f.write(svg_content)

        return "icon-192.svg"

    async def _generate_manifest(
        self, site_info: dict[str, Any], logo_path: str, output_dir: Path
    ) -> None:
        """Generate PWA manifest."""
        manifest = {
            "name": site_info["name"],
            "short_name": site_info["short_name"],
            "description": site_info["description"],
            "start_url": "/",
            "display": "fullscreen",
            "orientation": "any",
            "theme_color": "#000000",
            "background_color": "#ffffff",
            "scope": "/",
            "categories": ["books", "education", "entertainment"],
            "icons": [
                {
                    "src": logo_path,
                    "sizes": "192x192",
                    "type": "image/svg+xml"
                    if logo_path.endswith(".svg")
                    else "image/png",
                    "purpose": "any maskable",
                },
                {
                    "src": logo_path,
                    "sizes": "512x512",
                    "type": "image/svg+xml"
                    if logo_path.endswith(".svg")
                    else "image/png",
                    "purpose": "any maskable",
                },
            ],
        }

        async with aiofiles.open(output_dir / "manifest.json", "w") as f:
            await f.write(json.dumps(manifest, indent=2))

    async def _generate_html(
        self, site_info: dict[str, Any], target_url: str, output_dir: Path
    ) -> None:
        """Generate main HTML file with optimization."""
        # Optimize content
        optimizer = ContentOptimizer()
        optimization_result = await optimizer.optimize_site(target_url, output_dir)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>{site_info["name"]}</title>
    <meta name="description" content="{site_info["description"]}">

    <!-- PWA Meta Tags -->
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#000000">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="{site_info["short_name"]}">

    <!-- Preload critical resources -->
    <link rel="preload" href="preloaded.js" as="script">
    <link rel="prefetch" href="{target_url}">

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
            transition: opacity 0.3s ease;
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
            width: 40px;
            height: 40px;
            border: 4px solid #333;
            border-top: 4px solid #4285f4;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .error {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #ff4444;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            max-width: 300px;
            display: none;
        }}

        .optimization-info {{
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1001;
        }}
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="loading-spinner"></div>
        <div>Loading {site_info["name"]}...</div>
        <div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">
            Optimizing content...
        </div>
    </div>

    <div class="error" id="error">
        <h3>Failed to load</h3>
        <p>Please check your internet connection</p>
        <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background: #fff; color: #ff4444; border: none; border-radius: 4px; cursor: pointer;">Retry</button>
    </div>

    <div class="optimization-info" id="optInfo" style="display: none;">
        📄 {optimization_result.get("preloaded_pages", 0)} pages preloaded<br>
        🖼️ {optimization_result.get("optimized_images", 0)} images optimized
    </div>

    <iframe id="frame" src="{target_url}" style="display:none"></iframe>

    <script src="preloaded.js"></script>
    <script>
        // Register service worker
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('sw.js')
                .then(reg => console.log('SW registered'))
                .catch(err => console.log('SW registration failed'));
        }}

        const frame = document.getElementById('frame');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const optInfo = document.getElementById('optInfo');

        // Preload next pages in background
        function preloadPages() {{
            if (typeof preloadedPages !== 'undefined') {{
                Object.keys(preloadedPages).forEach(url => {{
                    const link = document.createElement('link');
                    link.rel = 'prefetch';
                    link.href = url;
                    document.head.appendChild(link);
                }});
            }}
        }}

        // Image lazy loading optimization
        function optimizeImages() {{
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        const img = entry.target;
                        if (img.dataset.src) {{
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            observer.unobserve(img);
                        }}
                    }}
                }});
            }});

            frame.contentDocument?.querySelectorAll('img[data-src]').forEach(img => {{
                observer.observe(img);
            }});
        }}

        let loadTimeout = setTimeout(() => {{
            loading.style.display = 'none';
            error.style.display = 'block';
        }}, 15000);

        frame.onload = () => {{
            clearTimeout(loadTimeout);
            loading.style.display = 'none';
            frame.style.display = 'block';

            // Show optimization info briefly
            optInfo.style.display = 'block';
            setTimeout(() => {{
                optInfo.style.opacity = '0';
                setTimeout(() => optInfo.style.display = 'none', 300);
            }}, 3000);

            // Start optimizations
            preloadPages();
            setTimeout(optimizeImages, 1000);
        }};

        frame.onerror = () => {{
            clearTimeout(loadTimeout);
            loading.style.display = 'none';
            error.style.display = 'block';
        }};

        // Prefetch on user interaction
        document.addEventListener('touchstart', preloadPages, {{ once: true }});
        document.addEventListener('click', preloadPages, {{ once: true }});
    </script>
</body>
</html>"""

        async with aiofiles.open(output_dir / "index.html", "w") as f:
            await f.write(html)

    async def _generate_service_worker(self, output_dir: Path) -> None:
        """Generate enhanced service worker with caching strategies."""
        sw_content = """const CACHE_NAME = 'pwa-reader-v2';
const STATIC_CACHE = 'static-v2';
const DYNAMIC_CACHE = 'dynamic-v2';
const IMAGE_CACHE = 'images-v2';

const staticAssets = [
    '/',
    '/index.html',
    '/manifest.json',
    '/preloaded.js'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => cache.addAll(staticAssets))
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (!cacheName.includes('v2')) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - advanced caching strategies
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Handle different resource types
    if (request.destination === 'image') {
        event.respondWith(handleImageRequest(request));
    } else if (url.pathname.endsWith('.html') || url.pathname === '/') {
        event.respondWith(handlePageRequest(request));
    } else {
        event.respondWith(handleStaticRequest(request));
    }
});

// Image caching with compression
async function handleImageRequest(request) {
    const cache = await caches.open(IMAGE_CACHE);
    const cached = await cache.match(request);

    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Return placeholder image on failure
        return new Response('', { status: 404 });
    }
}

// Page caching with network-first strategy
async function handlePageRequest(request) {
    const cache = await caches.open(DYNAMIC_CACHE);

    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await cache.match(request);
        return cached || new Response('Offline', { status: 503 });
    }
}

// Static assets with cache-first strategy
async function handleStaticRequest(request) {
    const cache = await caches.open(STATIC_CACHE);
    const cached = await cache.match(request);

    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return new Response('Resource not available', { status: 404 });
    }
}

// Background sync for preloading
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'PRELOAD_PAGES') {
        event.waitUntil(preloadPages(event.data.urls));
    }
});

async function preloadPages(urls) {
    const cache = await caches.open(DYNAMIC_CACHE);

    for (const url of urls) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                await cache.put(url, response);
            }
        } catch (error) {
            console.log(`Failed to preload: ${url}`);
        }
    }
}"""

        async with aiofiles.open(output_dir / "sw.js", "w") as f:
            await f.write(sw_content)

    async def serve(self, output_dir: Path, port: int) -> None:
        """Serve PWA locally."""
        os.chdir(output_dir)

        class Handler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self) -> None:
                self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
                self.send_header("Cross-Origin-Opener-Policy", "same-origin")
                self.send_header("Cache-Control", "no-cache")
                super().end_headers()

            def log_message(self, fmt: str, *args: Any) -> None:
                # Suppress default logging
                pass

        def open_browser() -> None:
            webbrowser.open(f"http://localhost:{port}")

        Timer(1, open_browser).start()

        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                console.print(
                    f"[green]✅ Server running at http://localhost:{port}[/green]"
                )
                console.print("[dim]• Open this URL in your mobile browser[/dim]")
                console.print(
                    "[dim]• Tap 'Add to Home Screen' to install the PWA[/dim]"
                )
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
