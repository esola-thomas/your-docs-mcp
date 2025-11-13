---
title: "Configuration Guide"
tags: [configuration, setup, environment, settings]
category: "Guides"
order: 2
---

# Configuration Guide

Learn how to configure the Hierarchical Documentation MCP server for your needs.

## Basic Configuration

The simplest way to configure the server is using environment variables.

### Required Settings

**DOCS_ROOT** - The path to your documentation directory:

```bash
export DOCS_ROOT=/path/to/your/docs
```

This is the only required configuration to get started.

### Optional Settings

```bash
# Cache settings
export MCP_DOCS_CACHE_TTL=3600        # Cache time-to-live in seconds (default: 3600)
export MCP_DOCS_MAX_CACHE_MB=500      # Maximum cache size in MB (default: 500)

# Search settings
export MCP_DOCS_SEARCH_LIMIT=10       # Maximum search results (default: 10)

# Security settings
export MCP_DOCS_ALLOW_HIDDEN=false    # Allow hidden files (default: false)
export MCP_DOCS_AUDIT_LOG=true        # Enable audit logging (default: true)

# Logging
export LOG_LEVEL=INFO                  # Logging level: DEBUG, INFO, WARN, ERROR
```

## Configuration File

For more complex setups, create a `.env` file in your project root:

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

## Advanced: Multi-Source Configuration

For advanced users, you can configure multiple documentation sources using a `.mcp-docs.yaml` file:

```yaml
sources:
  - path: ./docs/guides
    category: guides
    label: User Guides
    recursive: true
    include_patterns:
      - "*.md"
      - "*.mdx"
    exclude_patterns:
      - "node_modules"
      - ".git"

  - path: ./docs/api
    category: api
    label: API Reference
    format_type: openapi
    recursive: true

cache:
  ttl: 3600
  max_memory_mb: 500

security:
  allow_hidden_files: false
  audit_logging: true
```

## Platform-Specific Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "docs": {
      "command": "hierarchical-docs-mcp",
      "env": {
        "DOCS_ROOT": "/absolute/path/to/your/docs",
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
      "command": "hierarchical-docs-mcp",
      "env": {
        "DOCS_ROOT": "${workspaceFolder}/docs",
        "MCP_DOCS_CACHE_TTL": "3600"
      }
    }
  }
}
```

## Testing Your Configuration

After configuring, test that everything works:

```bash
# Start the server
hierarchical-docs-mcp

# Check logs for any errors
# The server should report the DOCS_ROOT path and number of documents loaded
```

## Next Steps

- Review [Performance Optimization](advanced/performance.md) for tuning
- Learn about [API Authentication](../api/authentication.md)
- Explore [CLI Commands](../reference/cli-commands.md)
