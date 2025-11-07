---
title: CLI Commands Reference
tags: [cli, command-line, reference, terminal]
category: "Reference"
order: 1
---

# CLI Commands Reference

Complete reference for all command-line interface commands.

## Installation

Ensure the CLI is installed:

```bash
pip install hierarchical-docs-mcp
```

## Global Options

These options work with all commands:

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message |
| `--verbose, -v` | Enable verbose output |
| `--quiet, -q` | Suppress non-error output |
| `--config FILE` | Use specified config file |

## Commands

### start

Start the MCP server.

**Usage:**

```bash
hierarchical-docs-mcp [OPTIONS]
```

**Options:**

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--docs-root PATH` | `DOCS_ROOT` | Documentation root directory |
| `--cache-ttl SECONDS` | `MCP_DOCS_CACHE_TTL` | Cache TTL in seconds |
| `--log-level LEVEL` | `LOG_LEVEL` | Logging level (DEBUG, INFO, WARN, ERROR) |
| `--port PORT` | `MCP_DOCS_PORT` | Server port (default: auto) |

**Examples:**

```bash
# Start with default settings
hierarchical-docs-mcp

# Specify docs root
hierarchical-docs-mcp --docs-root /path/to/docs

# Enable debug logging
hierarchical-docs-mcp --log-level DEBUG

# Use custom config file
hierarchical-docs-mcp --config /path/to/.mcp-docs.yaml
```

## validate

Validate documentation structure and metadata.

**Usage:**

```bash
hierarchical-docs-mcp validate [OPTIONS] PATH
```

**Options:**

| Option | Description |
|--------|-------------|
| `--strict` | Fail on warnings |
| `--format FORMAT` | Output format: text, json (default: text) |
| `--check-links` | Verify internal links |

**Examples:**

```bash
# Validate documentation
hierarchical-docs-mcp validate /path/to/docs

# Strict validation with JSON output
hierarchical-docs-mcp validate --strict --format json /path/to/docs

# Check for broken links
hierarchical-docs-mcp validate --check-links /path/to/docs
```

**Output:**

```text
Validating documentation at: /path/to/docs

✓ Found 15 documents
✓ All documents have valid frontmatter
✓ Category hierarchy is valid
⚠ Warning: 2 documents missing 'order' field
⚠ Warning: 1 broken internal link found

Summary:
  Total documents: 15
  Valid: 15
  Warnings: 3
  Errors: 0
```

## index

Build or rebuild the search index.

**Usage:**

```bash
hierarchical-docs-mcp index [OPTIONS] PATH
```

**Options:**

| Option | Description |
|--------|-------------|
| `--rebuild` | Rebuild index from scratch |
| `--optimize` | Optimize index after building |

**Examples:**

```bash
# Build index
hierarchical-docs-mcp index /path/to/docs

# Rebuild and optimize
hierarchical-docs-mcp index --rebuild --optimize /path/to/docs
```

## search

Search documentation from the command line.

**Usage:**

```bash
hierarchical-docs-mcp search [OPTIONS] QUERY
```

**Options:**

| Option | Description |
|--------|-------------|
| `--docs-root PATH` | Documentation directory to search |
| `--limit N` | Maximum results (default: 10) |
| `--category CAT` | Filter by category |
| `--tags TAG1,TAG2` | Filter by tags |
| `--format FORMAT` | Output format: text, json |

**Examples:**

```bash
# Simple search
hierarchical-docs-mcp search "authentication"

# Search with filters
hierarchical-docs-mcp search "API" --category api --limit 5

# JSON output
hierarchical-docs-mcp search "setup" --format json
```

**Output:**

```text
Search results for: "authentication"

1. API Authentication (docs://api/authentication)
   Category: API
   Tags: api, authentication, security

   Learn how to authenticate with the API and secure your requests...

2. Security Guide (docs://guides/security)
   Category: Guides
   Tags: security, authentication

   Best practices for securing your application...

Found 2 results
```

## stats

Show documentation statistics.

**Usage:**

```bash
hierarchical-docs-mcp stats [OPTIONS] PATH
```

**Options:**

| Option | Description |
|--------|-------------|
| `--format FORMAT` | Output format: text, json (default: text) |
| `--detailed` | Show detailed statistics |

**Examples:**

```bash
# Basic statistics
hierarchical-docs-mcp stats /path/to/docs

# Detailed JSON output
hierarchical-docs-mcp stats --detailed --format json /path/to/docs
```

**Output:**

```text
Documentation Statistics
========================

Documents:
  Total: 15
  Markdown: 13
  OpenAPI: 2

Categories:
  Total: 4
  Top level: 2
  Nested: 2

Tags:
  Unique tags: 24
  Most used: api (5), guide (4), security (3)

Size:
  Total: 245 KB
  Average: 16 KB
  Largest: 45 KB (api/endpoints.md)

Last updated: 2024-01-15 10:30:00
```

## serve

Start a development server with live reload.

**Usage:**

```bash
hierarchical-docs-mcp serve [OPTIONS] PATH
```

**Options:**

| Option | Description |
|--------|-------------|
| `--port PORT` | Server port (default: 8080) |
| `--watch` | Enable file watching and live reload |
| `--open` | Open browser automatically |

**Examples:**

```bash
# Start development server
hierarchical-docs-mcp serve /path/to/docs

# With live reload on custom port
hierarchical-docs-mcp serve --watch --port 3000 /path/to/docs
```

## export

Export documentation in various formats.

**Usage:**

```bash
hierarchical-docs-mcp export [OPTIONS] PATH OUTPUT
```

**Options:**

| Option | Description |
|--------|-------------|
| `--format FORMAT` | Export format: json, html, pdf |
| `--include-metadata` | Include frontmatter metadata |
| `--compress` | Compress output |

**Examples:**

```bash
# Export as JSON
hierarchical-docs-mcp export /path/to/docs ./output.json

# Export as HTML with metadata
hierarchical-docs-mcp export --format html --include-metadata \
  /path/to/docs ./output.html

# Export and compress
hierarchical-docs-mcp export --compress /path/to/docs ./docs.tar.gz
```

## config

Manage configuration.

**Usage:**

```bash
hierarchical-docs-mcp config [SUBCOMMAND]
```

**Subcommands:**

| Subcommand | Description |
|------------|-------------|
| `show` | Display current configuration |
| `init` | Create default config file |
| `validate` | Validate config file |

**Examples:**

```bash
# Show current config
hierarchical-docs-mcp config show

# Create default config
hierarchical-docs-mcp config init

# Validate config file
hierarchical-docs-mcp config validate .mcp-docs.yaml
```

## Environment Variables

All options can be configured via environment variables:

```bash
# Documentation settings
export DOCS_ROOT=/path/to/docs

# Cache settings
export MCP_DOCS_CACHE_TTL=3600
export MCP_DOCS_MAX_CACHE_MB=500

# Search settings
export MCP_DOCS_SEARCH_LIMIT=10

# Logging
export LOG_LEVEL=INFO

# Server settings
export MCP_DOCS_PORT=8080
```

## Configuration File

Create `.mcp-docs.yaml` for persistent configuration:

```yaml
# Documentation sources
sources:
  - path: ./docs
    category: docs
    label: Documentation

# Cache configuration
cache:
  ttl: 3600
  max_memory_mb: 500

# Search configuration
search:
  limit: 10
  fuzzy: true

# Logging
logging:
  level: INFO
  format: json
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Configuration error |
| 4 | File not found |
| 5 | Validation error |

## Troubleshooting

## Command not found

```bash
# Verify installation
pip show hierarchical-docs-mcp

# Check PATH
which hierarchical-docs-mcp
```

## Permission denied

```bash
# Install with --user flag
pip install --user hierarchical-docs-mcp

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install hierarchical-docs-mcp
```

## Configuration errors

```bash
# Validate config
hierarchical-docs-mcp config validate

# Show current config
hierarchical-docs-mcp config show --verbose
```

## Getting Help

For detailed help on any command:

```bash
hierarchical-docs-mcp COMMAND --help
```

## Next Steps

- Review [Configuration Guide](../guides/configuration.md)
- Explore [API Endpoints](../api/endpoints.md)
- Learn about [Performance Optimization](../guides/advanced/performance.md)
