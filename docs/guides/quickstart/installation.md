---
title: Installation Guide
tags: [quickstart, installation, setup, beginner]
category: Guides
order: 1
---

# Installation Guide

This guide covers installing the Hierarchical Documentation MCP server.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git (optional, for development installation)

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install your-docs-mcp
```

### Method 2: Install from Source

For the latest development version:

```bash
# Clone the repository
git clone https://github.com/esola-thomas/Markdown-MCP
cd Markdown-MCP

# Install in development mode
pip install -e .
```

### Method 3: With Development Dependencies

For contributing or running tests:

```bash
pip install your-docs-mcp[dev]
```

## Verify Installation

Check that the installation succeeded:

```bash
# Check MCP server
your-docs-mcp --help

# Check web server
your-docs-web --help
```

## Dependencies

The package automatically installs:

| Package | Purpose |
|---------|---------|
| `mcp>=0.1.0` | Model Context Protocol SDK |
| `chromadb>=0.4.0` | Vector database for semantic search |
| `sentence-transformers>=2.2.2` | Embedding model for search |
| `fastapi>=0.104.0` | Web API framework |
| `uvicorn>=0.24.0` | ASGI server |
| `pyyaml>=6.0` | YAML frontmatter parsing |

## Environment Setup

### Minimum Configuration

Set your documentation root directory:

```bash
export DOCS_ROOT=/path/to/your/documentation
```

### Recommended Configuration

```bash
# Documentation location
export DOCS_ROOT=/path/to/your/docs

# Optional: Logging level (DEBUG, INFO, WARN, ERROR)
export LOG_LEVEL=INFO

# Optional: Server port for web interface
export PORT=8080
```

## Quick Start

After installation, start the server:

```bash
# Start MCP server (stdio transport for Claude Desktop)
your-docs-mcp

# Or start web server (HTTP/SSE transport)
your-docs-web
```

## Platform-Specific Notes

### Linux/macOS

No special requirements. Use the standard installation commands.

### Windows

Use PowerShell or Windows Terminal:

```powershell
# Set environment variable
$env:DOCS_ROOT = "C:\path\to\docs"

# Start server
your-docs-mcp
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN pip install your-docs-mcp

ENV DOCS_ROOT=/docs
EXPOSE 8080

CMD ["your-docs-web"]
```

## Troubleshooting

### Permission Denied

```bash
# Install to user directory
pip install --user your-docs-mcp

# Or use a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install your-docs-mcp
```

### Python Version Error

Verify Python version:

```bash
python --version
# Should be 3.10 or higher
```

### Package Not Found After Install

Ensure pip's bin directory is in your PATH:

```bash
# Find pip's bin directory
python -m site --user-base

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"
```

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Getting Started](../getting-started.md) - Connect to AI assistants
- [Architecture Overview](../../architecture/overview.md) - System design
