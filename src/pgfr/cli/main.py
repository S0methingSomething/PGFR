"""Interactive CLI for PWA generation."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from pgfr.services.pwa_generator import PWAGenerator

app = typer.Typer(
    name="pgfr",
    help="🚀 PWA Generator for Reading - Create mobile-optimized PWAs from any website",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def generate(
    url: str | None = typer.Argument(None, help="Website URL to create PWA for"),
    output_dir: str | None = typer.Option(
        None, "--output-dir", "-o", help="Output directory"
    ),
    port: int | None = typer.Option(None, "--port", "-p", help="Local server port"),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", "-i", help="Interactive mode"
    ),
) -> None:
    """Generate PWA from website URL."""
    if interactive:
        asyncio.run(_interactive_generate(url, output_dir, port))
    else:
        if not url:
            console.print("[red]Error: URL is required in non-interactive mode[/red]")
            raise typer.Exit(1)
        asyncio.run(_generate(url, Path(output_dir or "./pwa"), port or 8080))


async def _interactive_generate(
    url: str | None, output_dir: str | None, port: int | None
) -> None:
    """Interactive PWA generation."""
    console.print(
        Panel.fit(
            "[bold blue]🚀 PWA Generator for Reading[/bold blue]\n"
            "[dim]Create mobile-optimized PWAs from any website[/dim]",
            border_style="blue",
        )
    )

    # Get URL
    if not url:
        url = Prompt.ask(
            "[bold cyan]Enter website URL[/bold cyan]", default="https://example.com"
        )

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Get output directory
    if not output_dir:
        output_dir = Prompt.ask(
            "[bold cyan]Output directory[/bold cyan]", default="./pwa"
        )

    # Get port
    if not port:
        port = int(
            Prompt.ask("[bold cyan]Local server port[/bold cyan]", default="8080")
        )

    # Show configuration
    config_table = Table(show_header=False, box=None)
    config_table.add_row("[bold]URL:[/bold]", f"[green]{url}[/green]")
    config_table.add_row("[bold]Output:[/bold]", f"[yellow]{output_dir}[/yellow]")
    config_table.add_row("[bold]Port:[/bold]", f"[blue]{port}[/blue]")

    console.print("\n[bold]Configuration:[/bold]")
    console.print(config_table)

    if not Confirm.ask("\n[bold]Generate PWA?[/bold]", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        return

    await _generate(url, Path(output_dir), port)


async def _generate(url: str, output_dir: Path, port: int) -> None:
    """Generate PWA with progress indicators."""
    generator = PWAGenerator()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        # Analyze website
        task = progress.add_task("🔍 Analyzing website...", total=None)
        try:
            await generator.generate(url, output_dir)
            progress.update(task, description="✅ PWA generated successfully!")
        except Exception as e:
            progress.update(task, description=f"❌ Error: {e}")
            console.print(f"[red]Failed to generate PWA: {e}[/red]")
            return

    # Show results
    console.print(
        Panel(
            f"[green]✅ PWA generated successfully![/green]\n\n"
            f"[bold]Location:[/bold] {output_dir.absolute()}\n"
            f"[bold]Files created:[/bold]\n"
            f"  • index.html (main app)\n"
            f"  • manifest.json (PWA config)\n"
            f"  • sw.js (service worker)\n"
            f"  • icon file (app icon)",
            title="[bold green]Success[/bold green]",
            border_style="green",
        )
    )

    if Confirm.ask(f"\n[bold]Start local server on port {port}?[/bold]", default=True):
        console.print(
            f"\n[yellow]🌐 Starting server at http://localhost:{port}[/yellow]"
        )
        console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

        try:
            await generator.serve(output_dir, port)
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")


@app.command()
def info() -> None:
    """Show information about PGFR."""
    info_panel = Panel(
        "[bold blue]PGFR - PWA Generator for Reading[/bold blue]\n\n"
        "[bold]Features:[/bold]\n"
        "• 📱 Mobile-optimized fullscreen reading\n"
        "• 🎨 Automatic logo extraction\n"
        "• 📦 Installable PWA generation\n"
        "• 🌐 Local development server\n"
        "• ⚡ Fast and lightweight\n\n"
        "[bold]Usage:[/bold]\n"
        "  pgfr generate [URL]     Generate PWA\n"
        "  pgfr info              Show this info\n\n"
        "[dim]Visit: https://github.com/your-repo/pgfr[/dim]",
        border_style="blue",
    )
    console.print(info_panel)


if __name__ == "__main__":
    app()
