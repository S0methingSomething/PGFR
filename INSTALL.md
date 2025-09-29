# Installation Guide

## Quick Install (Recommended)

### For Termux
```bash
# Download and install wheel
wget https://github.com/S0methingSomething/PGFR/releases/download/v0.1.0/pgfr-0.1.0-py3-none-any.whl
pip install pgfr-0.1.0-py3-none-any.whl

# Or install directly from git
pip install git+https://github.com/S0methingSomething/PGFR.git
```

### For Other Environments
```bash
# Using uv (fastest)
uv pip install git+https://github.com/S0methingSomething/PGFR.git

# Using pip
pip install git+https://github.com/S0methingSomething/PGFR.git

# Or download wheel
wget https://github.com/S0methingSomething/PGFR/releases/download/v0.1.0/pgfr-0.1.0-py3-none-any.whl
pip install pgfr-0.1.0-py3-none-any.whl
```

## Usage

After installation, just run:
```bash
pgfr
```

The interactive CLI will guide you through:
1. Enter website URL (e.g., reddit.com)
2. Choose output directory (default: ./pwa)
3. Choose server port (default: 8080)
4. PWA gets generated and served locally
5. Visit the URL to install the PWA in your browser

## Requirements

- Python 3.12+
- Modern web browser with PWA support

## Dependencies

Only 5 lightweight runtime dependencies:
- aiofiles (async file operations)
- aiohttp (HTTP client)
- beautifulsoup4 (HTML parsing)
- rich (terminal UI)
- typer (CLI framework)

**Total install size: ~21 packages** (no bloat!)
