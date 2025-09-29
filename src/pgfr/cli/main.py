"""Interactive CLI for PWA generation."""

import asyncio
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from pgfr.services.pwa_generator import PWAGenerator

console = Console()


def main() -> None:
    """Interactive PWA generator."""
    console.print("🚀 [bold cyan]PGFR - PWA Generator[/bold cyan]")
    console.print("Turn any website into a mobile app!\n")

    # Get URL with examples
    console.print(
        "💡 [dim]Examples: reddit.com, news.ycombinator.com, github.com[/dim]"
    )
    url = Prompt.ask("📱 Enter website URL")

    if not url:
        console.print("❌ URL is required!")
        return

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Simple defaults with confirmation
    output = "./pwa"
    port = 8080

    if Confirm.ask(f"\n📁 Save PWA to '{output}' folder?", default=True):
        pass  # Use default
    else:
        output = Prompt.ask("📁 Enter output directory", default="./pwa")

    if Confirm.ask(f"🌐 Use port {port} for local server?", default=True):
        pass  # Use default
    else:
        port = int(Prompt.ask("🌐 Enter port number", default="8080"))

    # Generate PWA
    console.print(f"\n🔄 Creating PWA from: [green]{url}[/green]")
    console.print("⏳ This may take a moment...")

    try:
        asyncio.run(_generate_pwa(url, output, port))
    except KeyboardInterrupt:
        console.print("\n❌ Cancelled by user")
    except Exception as e:
        console.print(f"\n❌ Error: {e}")


async def _generate_pwa(url: str, output: str, port: int) -> None:
    """Generate PWA."""
    generator = PWAGenerator()
    await generator.generate_pwa(url, Path(output), port)

    console.print("\n✅ [bold green]PWA created successfully![/bold green]")
    console.print(f"📂 Location: [yellow]{output}/[/yellow]")
    console.print(
        f"🚀 To test: [cyan]cd {output} && python -m http.server {port}[/cyan]"
    )
    console.print(f"🌐 Then visit: [blue]http://localhost:{port}[/blue]")


if __name__ == "__main__":
    main()
