---
title: CLI Commands Reference
tags: [cli, command-line, reference, terminal]
category: Reference
order: 1
---

# CLI Commands Reference

Complete reference for all command-line interface commands.

## Available Commands

The package provides three entry points:

| Command | Description |
|---------|-------------|
| `your-docs-mcp` | MCP server (stdio transport) |
| `your-docs-web` | Web server with MCP SSE transport |
| `your-docs-server` | Combined server |

## your-docs-mcp

Start the MCP server for AI assistant integration.

### Usage

```bash
your-docs-mcp [OPTIONS]
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DOCS_ROOT` | Documentation root directory (required) |
| `LOG_LEVEL` | Logging level: DEBUG, INFO, WARN, ERROR |
| `MCP_DOCS_CACHE_TTL` | Cache TTL in seconds |
| `MCP_DOCS_SEARCH_LIMIT` | Maximum search results |

### Examples

```bash
# Start with documentation path
DOCS_ROOT=/path/to/docs your-docs-mcp

# With debug logging
DOCS_ROOT=/path/to/docs LOG_LEVEL=DEBUG your-docs-mcp
```

## your-docs-web

Start the web server with REST API and web UI.

### Usage

```bash
your-docs-web [OPTIONS]
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DOCS_ROOT` | Documentation root directory (required) |
| `PORT` | Server port (default: 8080) |
| `HOST` | Server host (default: 0.0.0.0) |
| `LOG_LEVEL` | Logging level |

### Examples

```bash
# Start web server
DOCS_ROOT=/path/to/docs your-docs-web

# Custom port
DOCS_ROOT=/path/to/docs PORT=3000 your-docs-web
```

### Web UI Features

- Browse documentation hierarchy
- Full-text search
- Tag-based filtering
- Markdown rendering with syntax highlighting
- Dark/light theme toggle

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| GET | `/api/health` | Health check |
| GET | `/api/search` | Search documentation |
| GET | `/api/toc` | Table of contents |
| GET | `/api/document` | Get document by URI |
| GET | `/api/tags` | List all tags |
| POST | `/api/search-by-tags` | Search by tags |
| GET | `/sse` | MCP SSE transport |

## your-docs-server

Combined server supporting both stdio and web modes.

### Usage

```bash
your-docs-server [--mode MODE]
```

### Modes

| Mode | Description |
|------|-------------|
| `stdio` | MCP stdio transport (default) |
| `web` | Web server with SSE |
| `all` | Both transports |

## Global Options

These options work with all commands via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCS_ROOT` | Documentation directory | Required |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `MCP_DOCS_CACHE_TTL` | Cache TTL (seconds) | 3600 |
| `MCP_DOCS_MAX_CACHE_MB` | Max cache size (MB) | 500 |
| `MCP_DOCS_SEARCH_LIMIT` | Max search results | 10 |
| `MCP_DOCS_ALLOW_HIDDEN` | Allow hidden files | false |
| `MCP_DOCS_AUDIT_LOG` | Enable audit logging | true |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Documentation not found |

## Troubleshooting

### Command Not Found

```bash
# Verify installation
pip show your-docs-mcp

# Check if in PATH
which your-docs-mcp

# Install with user flag if needed
pip install --user your-docs-mcp
```

### DOCS_ROOT Not Set

```bash
Error: DOCS_ROOT environment variable must be set
```

Solution: Set the `DOCS_ROOT` variable:

```bash
export DOCS_ROOT=/path/to/your/documentation
```

### Permission Denied

```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install your-docs-mcp
```

### Port Already in Use

```bash
# Use different port
PORT=3001 your-docs-web
```

## Integration Examples

### systemd Service

```ini
[Unit]
Description=Documentation MCP Server
After=network.target

[Service]
Type=simple
Environment="DOCS_ROOT=/var/docs"
Environment="PORT=8080"
ExecStart=/usr/local/bin/your-docs-web
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Compose

```yaml
version: '3.8'
services:
  docs:
    image: python:3.11-slim
    command: your-docs-web
    environment:
      - DOCS_ROOT=/docs
      - PORT=8080
    volumes:
      - ./docs:/docs:ro
    ports:
      - "8080:8080"
```

## Next Steps

- [Configuration Guide](../guides/quickstart/configuration.md) - Detailed settings
- [Getting Started](../guides/getting-started.md) - Quick start
- [Architecture](../architecture/overview.md) - System design
