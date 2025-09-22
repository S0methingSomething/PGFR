# PGFR - PWA Generator for Reading

Generate mobile-optimized PWAs from any website for fullscreen reading experience.

## Installation

```bash
uv add pgfr
```

## Development

```bash
# Install with dev dependencies
uv sync --dev

# Run the CLI
uv run pgfr generate https://example.com

# Run tests
uv run pytest

# Format code
uv run ruff format
uv run ruff check --fix
```

## Usage

```bash
# Generate PWA for a website
pgfr generate https://example.com

# Custom output directory and port
pgfr generate https://example.com --output-dir ./my-pwa --port 3000
```

The generated PWA will:
- Extract the site's logo automatically
- Create a fullscreen, mobile-optimized reading experience
- Start a local server for installation
- Be installable as a PWA on mobile devices
