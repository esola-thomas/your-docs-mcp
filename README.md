# Documentation MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to navigate and query documentation through hierarchical structures, supporting markdown files with YAML frontmatter and OpenAPI 3.x specifications.

## Features

- **Hierarchical Navigation**: Navigate documentation organized in nested directory structures with unlimited depth
- **Markdown Support**: Parse markdown files with YAML frontmatter metadata (title, tags, category, order)
- **OpenAPI Integration**: Load and query OpenAPI 3.x specifications as documentation resources
- **Intelligent Search**: Full-text search with metadata filtering and hierarchical context
- **Web Interface**: Built-in web server provides browser-based access to documentation with the same tools available to LLMs
- **Cross-Platform**: Works with Claude Desktop, VS Code/GitHub Copilot, and other MCP-compatible AI assistants
- **Security**: Built-in path validation, query sanitization, and audit logging
- **Performance**: Caching with TTL and automatic file change detection

## Quick Start

### Installation

```bash
# Install from PyPI
pip install docs-mcp

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
docs-mcp
```

### Claude Desktop Configuration

Add to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "docs": {
      "command": "docs-mcp",
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
      "command": "docs-mcp",
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
docs-mcp
```

The example includes:
- Hierarchical documentation structure with nested categories
- Markdown files with proper YAML frontmatter
- Sample API documentation and guides
- OpenAPI 3.0 specification example
- Comprehensive README explaining the structure

See the [`example/README.md`](example/README.md) for detailed information about the structure and how to customize it for your project.

## Web Interface

The Markdown MCP server includes a built-in web interface that allows users to browse and search documentation directly in their browser, using the same tools available to AI assistants.

### Accessing the Web Interface

When you start the server, it automatically launches both the MCP server (for AI assistants) and a web server (for browser access):

```bash
export DOCS_ROOT=/path/to/your/docs
hierarchical-docs-mcp
```

By default, the web interface is available at: **http://127.0.0.1:8080**

Open this URL in your browser to access the documentation interface.

### Features

The web interface provides:

- **Search Documentation**: Full-text search with relevance scoring and highlighted excerpts
- **Table of Contents**: Browse the complete documentation hierarchy
- **Tag-based Search**: Filter documentation by metadata tags
- **Document Viewer**: View full document content with formatting
- **Real-time Stats**: See the number of loaded documents and categories

### Configuration

You can customize the web server settings using environment variables:

```bash
# Enable/disable web server (default: true)
export MCP_DOCS_ENABLE_WEB_SERVER=true

# Web server host (default: 127.0.0.1)
export MCP_DOCS_WEB_HOST=127.0.0.1

# Web server port (default: 8080)
export MCP_DOCS_WEB_PORT=8080
```

### API Endpoints

The web interface also exposes REST API endpoints that you can use programmatically:

- `GET /api/health` - Health check and statistics
- `GET|POST /api/search` - Search documentation
- `GET|POST /api/navigate` - Navigate to specific URIs
- `GET|POST /api/toc` - Get table of contents
- `POST /api/search-by-tags` - Search by tags
- `GET|POST /api/document` - Get document content

Example API usage:

```bash
# Search for documentation
curl "http://localhost:8080/api/search?query=authentication"

# Get a specific document
curl "http://localhost:8080/api/document?uri=docs://guides/quickstart/installation"

# Get table of contents
curl "http://localhost:8080/api/toc"
```

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
- `MCP_DOCS_ENABLE_WEB_SERVER`: Enable/disable web server (default: true)
- `MCP_DOCS_WEB_HOST`: Web server host (default: 127.0.0.1)
- `MCP_DOCS_WEB_PORT`: Web server port (default: 8080)
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
mypy docs_mcp

# Run linting
ruff check docs_mcp
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
pytest --cov=docs_mcp --cov-report=html
```

## Architecture

```
docs_mcp/
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
