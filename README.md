# Hierarchical Documentation MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to navigate and query documentation through hierarchical structures, supporting markdown files with YAML frontmatter and OpenAPI 3.x specifications.

## Features

- **Hierarchical Navigation**: Navigate documentation organized in nested directory structures with unlimited depth
- **Markdown Support**: Parse markdown files with YAML frontmatter metadata (title, tags, category, order)
- **OpenAPI Integration**: Load and query OpenAPI 3.x specifications as documentation resources
- **Intelligent Search**: Full-text search with metadata filtering and hierarchical context
- **Cross-Platform**: Works with Claude Desktop, VS Code/GitHub Copilot, and other MCP-compatible AI assistants
- **Security**: Built-in path validation, query sanitization, and audit logging
- **Performance**: Caching with TTL and automatic file change detection

## Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install hierarchical-docs-mcp

# Or install from source
git clone https://github.com/esola-thomas/Markdown-MCP
cd Markdown-MCP
pip install -e .
```

### Basic Configuration

1. Set your documentation root directory:

```bash
export DOCS_ROOT=/path/to/your/docs
```

2. Start the MCP server:

```bash
hierarchical-docs-mcp
```

### Claude Desktop Configuration

Add to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "docs": {
      "command": "hierarchical-docs-mcp",
      "env": {
        "DOCS_ROOT": "/absolute/path/to/your/docs"
      }
    }
  }
}
```

### VS Code Configuration

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "docs": {
      "command": "hierarchical-docs-mcp",
      "env": {
        "DOCS_ROOT": "${workspaceFolder}/docs"
      }
    }
  }
}
```

### Try the Example

This repository includes a complete example documentation structure in the [`example/`](example/) folder that you can use to test the MCP server or as a template for your own documentation.

**Quick test:**

```bash
# Point DOCS_ROOT to the example folder
export DOCS_ROOT=/path/to/Markdown-MCP/example

# Start the server
hierarchical-docs-mcp
```

The example includes:
- Hierarchical documentation structure with nested categories
- Markdown files with proper YAML frontmatter
- Sample API documentation and guides
- OpenAPI 3.0 specification example
- Comprehensive README explaining the structure

See the [`example/README.md`](example/README.md) for detailed information about the structure and how to customize it for your project.

## Usage Examples

### Ask Your AI Assistant

Once configured, you can ask your AI assistant natural language questions:

- "Show me the getting started guide"
- "List all available documentation"
- "What authentication methods are available?"
- "Show me all API endpoints for user management"
- "Search for documentation about deployment"

### Supported Document Formats

**Markdown Files** (`.md`, `.mdx`):
```markdown
---
title: Getting Started
tags: [guide, quickstart]
category: guides
order: 1
---

# Getting Started

Your documentation content here...
```

**OpenAPI Specifications** (`.yaml`, `.json`):
```yaml
openapi: 3.0.3
info:
  title: My API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: listUsers
      summary: List all users
      ...
```

## Advanced Configuration

### Multi-Source Setup

Create `.mcp-docs.yaml` in your project:

```yaml
sources:
  - path: ./docs
    category: guides
    label: User Guides
    recursive: true

  - path: ./api-specs
    category: api
    label: API Reference
    format_type: openapi

cache:
  ttl: 3600
  max_memory_mb: 500

security:
  allow_hidden_files: false
  audit_logging: true
```

### Environment Variables

See `.env.example` for all available configuration options:

- `DOCS_ROOT`: Documentation root directory (required)
- `MCP_DOCS_CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `MCP_DOCS_OPENAPI_SPECS`: Comma-separated OpenAPI spec paths
- `MCP_DOCS_SEARCH_LIMIT`: Maximum search results (default: 10)
- `LOG_LEVEL`: Logging level (default: INFO)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/esola-thomas/Markdown-MCP
cd Markdown-MCP

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy hierarchical_docs_mcp

# Run linting
ruff check hierarchical_docs_mcp
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m contract

# Run with coverage
pytest --cov=hierarchical_docs_mcp --cov-report=html
```

## Architecture

```
hierarchical_docs_mcp/
├── models/          # Data models (Document, Category, OpenAPI entities)
├── handlers/        # MCP protocol handlers (tools, resources)
├── services/        # Business logic (markdown parsing, search, hierarchy)
├── security/        # Security validation (path validation, sanitization)
└── utils/           # Utilities (logging, helpers)
```

## Security

- **Path Validation**: All file paths are validated to prevent directory traversal attacks
- **Hidden Files**: Hidden files (starting with `.`) are excluded by default
- **Query Sanitization**: Search queries are sanitized to prevent injection attacks
- **Audit Logging**: All file access attempts are logged for security auditing

## Contributing

Contributions are welcome! Please see the contribution guidelines for more information.

## License

MIT License - see LICENSE file for details

## Links

- [Documentation](https://github.com/esola-thomas/Markdown-MCP/tree/main/docs)
- [Issue Tracker](https://github.com/esola-thomas/Markdown-MCP/issues)
- [MCP Documentation](https://modelcontextprotocol.io)
