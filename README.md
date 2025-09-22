# PGFR - PWA Generator for Reading

Generate mobile-optimized PWAs from any website for fullscreen reading experience.

## Features

- 📱 **Mobile-optimized fullscreen reading experience**
- 🎨 **Automatic logo extraction and fallback generation**
- 📦 **Installable PWA with service worker caching**
- 🌐 **Local development server**
- ⚡ **Content optimization with page preloading**
- 🖼️ **Image optimization and lazy loading**
- 🤖 **Termux compatibility layer** (no Playwright dependency)

## Installation

### Standard Installation
```bash
uv add pgfr
```

### Full Installation (with Playwright)
```bash
uv add "pgfr[full]"
```

### Termux Installation
```bash
# In Termux, use standard installation (Playwright not available)
pkg install python
pip install pgfr
```

## Usage

### Interactive Mode (Default)
```bash
pgfr generate
```

### Quick Generation
```bash
pgfr generate https://example.com
```

### Custom Options
```bash
pgfr generate https://example.com --output-dir ./my-pwa --port 3000
```

### Non-Interactive Mode
```bash
pgfr generate https://example.com --no-interactive
```

## Environment Compatibility

PGFR automatically detects your environment and adapts:

- **Standard Environment**: Full features with advanced optimization
- **Termux Environment**: Lightweight mode without Playwright dependency
  - Simplified content optimization
  - Reduced memory usage
  - Mobile-first design
  - Basic image processing

## Development

```bash
# Install with dev dependencies
uv sync --dev

# Run the CLI
uv run pgfr generate https://example.com

# Run tests
uv run pytest

# Run all quality checks
make all

# Format code
make format

# Type checking
make type-check
```

## Generated PWA Features

The generated PWA includes:

- **Fullscreen mobile experience** with proper viewport settings
- **Service worker** with multi-tier caching (static, dynamic, images)
- **PWA manifest** with proper icons and metadata
- **Content optimization** with page preloading
- **Image optimization** with lazy loading
- **Offline support** with cached resources

## Termux Specific Features

When running in Termux:

- **Automatic detection** of Termux environment
- **Lightweight processing** to conserve battery and memory
- **Simplified UI** optimized for mobile terminals
- **Reduced network usage** with limited preloading
- **Portrait-first design** for mobile reading

## Requirements

- Python 3.12+
- Modern web browser with PWA support

### Optional Dependencies

- **Playwright** (for advanced features, not available in Termux)

## License

MIT License - see LICENSE file for details.
