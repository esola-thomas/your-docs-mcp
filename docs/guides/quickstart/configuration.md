---
title: Configuration Guide
tags: [configuration, setup, environment, settings]
category: Guides
order: 2
---

# Configuration Guide

Configure the Hierarchical Documentation MCP server for your environment.

## Environment Variables

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCS_ROOT` | Path to documentation directory | `/path/to/docs` |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_DOCS_CACHE_TTL` | Cache TTL in seconds | `3600` |
| `MCP_DOCS_MAX_CACHE_MB` | Max cache size in MB | `500` |
| `MCP_DOCS_SEARCH_LIMIT` | Max search results | `10` |
| `MCP_DOCS_ALLOW_HIDDEN` | Allow hidden files | `false` |
| `MCP_DOCS_AUDIT_LOG` | Enable audit logging | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Web server port | `8080` |

## Configuration File

Create a `.env` file in your project root:

```env
# Documentation settings
DOCS_ROOT=/absolute/path/to/docs

# Cache configuration
MCP_DOCS_CACHE_TTL=7200
MCP_DOCS_MAX_CACHE_MB=1000

# Search configuration
MCP_DOCS_SEARCH_LIMIT=20

# Logging
LOG_LEVEL=INFO
```

## Platform Configuration

### Claude Desktop

Add to Claude Desktop's configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "docs": {
      "command": "your-docs-mcp",
      "env": {
        "DOCS_ROOT": "/path/to/your/documentation",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### VS Code / GitHub Copilot

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "docs": {
      "command": "your-docs-mcp",
      "env": {
        "DOCS_ROOT": "${workspaceFolder}/docs",
        "MCP_DOCS_CACHE_TTL": "3600"
      }
    }
  }
}
```

### Web Server

Start with environment variables:

```bash
DOCS_ROOT=/path/to/docs PORT=3000 your-docs-web
```

Or use a `.env` file:

```bash
# .env file in working directory
DOCS_ROOT=/path/to/docs
PORT=3000
```

## Documentation Structure

### Recommended Directory Layout

```text
docs/
├── guides/
│   ├── getting-started.md
│   └── quickstart/
│       ├── installation.md
│       └── configuration.md
├── api/
│   ├── authentication.md
│   ├── endpoints.md
│   └── openapi.yaml
├── architecture/
│   └── overview.md
└── reference/
    └── cli-commands.md
```

### Markdown Frontmatter

Each markdown file should include YAML frontmatter:

```markdown
---
title: Document Title
tags: [tag1, tag2]
category: Category Name
order: 1
---

# Document Title

Content here...
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Display title |
| `tags` | No | Array of tags for search/filtering |
| `category` | No | Category for grouping |
| `order` | No | Sort order within category |
| `description` | No | Short description |

## Security Configuration

### Path Validation

By default, the server prevents access to:
- Files outside `DOCS_ROOT`
- Hidden files (starting with `.`)
- System directories

To allow hidden files:

```bash
export MCP_DOCS_ALLOW_HIDDEN=true
```

### Audit Logging

Enable detailed logging for debugging:

```bash
export MCP_DOCS_AUDIT_LOG=true
export LOG_LEVEL=DEBUG
```

## Performance Tuning

### Cache Settings

For frequently accessed documentation:

```bash
# Increase cache TTL (2 hours)
export MCP_DOCS_CACHE_TTL=7200

# Increase cache size (1 GB)
export MCP_DOCS_MAX_CACHE_MB=1000
```

### Search Limits

Adjust based on documentation size:

```bash
# More results for large documentation sets
export MCP_DOCS_SEARCH_LIMIT=20
```

## Validating Configuration

Test your configuration:

```bash
# Start with verbose logging
LOG_LEVEL=DEBUG your-docs-mcp

# Check the startup output for:
# - DOCS_ROOT path
# - Number of documents loaded
# - Any errors or warnings
```

## Next Steps

- [Installation Guide](installation.md) - Install the server
- [Getting Started](../getting-started.md) - Quick start guide
- [CLI Reference](../../reference/cli-commands.md) - Command line options
