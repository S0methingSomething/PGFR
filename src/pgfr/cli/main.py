"""Simple CLI for PWA generation."""

from pathlib import Path

import typer
from rich.console import Console

from pgfr.services.pwa_generator import PWAGenerator

app = typer.Typer(name="pgfr", help="Generate PWAs from websites")
console = Console()


@app.command()
def generate(url: str = typer.Argument(..., help="Website URL")) -> None:
    """Generate PWA from website URL."""
    import asyncio

    asyncio.run(_generate(url))


async def _generate(url: str) -> None:
    """Generate PWA."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    generator = PWAGenerator()
    await generator.generate_pwa(url, Path("./pwa"), 8080)
    console.print("✅ PWA generated successfully!")


@app.command()
def info() -> None:
    """Show PGFR info."""
    console.print("PGFR - PWA Generator for Reading")


if __name__ == "__main__":
    app()
