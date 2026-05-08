# your-docs-mcp

An MCP server that gives AI assistants structured access to your documentation. Supports markdown with YAML frontmatter, OpenAPI specs, full-text search, a web interface, and PDF generation.

## Installation

Install from [PyPI](https://pypi.org/project/your-docs-mcp/):

```bash
pip install your-docs-mcp
```

With semantic search (recommended):

```bash
pip install "your-docs-mcp[vector]" --extra-index-url https://download.pytorch.org/whl/cpu
```

With PDF generation:

```bash
pip install "your-docs-mcp[pdf]"
```

All features:

```bash
pip install "your-docs-mcp[vector,pdf]" --extra-index-url https://download.pytorch.org/whl/cpu
```

PDF generation requires system packages:

- macOS: `brew install pandoc basictex`
- Ubuntu/Debian: `sudo apt install pandoc texlive-xetex texlive-latex-extra`

## Quick Start

```bash
export DOCS_ROOT=/path/to/your/docs
your-docs-server
```

Open http://localhost:8123 to browse your docs. The MCP server is also running for AI clients.

## AI Client Setup

**Claude Desktop** - edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "docs": {
      "command": "your-docs-mcp",
      "env": {
        "DOCS_ROOT": "/absolute/path/to/your/docs"
      }
    }
  }
}
```

**VS Code** - create `.vscode/mcp.json`:

```json
{
  "servers": {
    "docs": {
      "command": "your-docs-mcp",
      "env": {
        "DOCS_ROOT": "${workspaceFolder}/docs"
      }
    }
  }
}
```

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `search_documentation` | Full-text search with relevance scoring |
| `navigate_to` | Navigate to a doc by URI (e.g. `docs://guides/quickstart`) |
| `get_table_of_contents` | Get the full documentation hierarchy |
| `get_document` | Retrieve a document and its metadata |
| `search_by_tags` | Filter docs by tags |
| `get_all_tags` | List all tags across documentation |
| `generate_pdf_release` | Generate a PDF of all documentation |

## Supported Formats

**Markdown with YAML frontmatter:**

```markdown
---
title: Getting Started
tags: [guide, quickstart]
order: 1
---

# Getting Started

Your content here...
```

**OpenAPI 3.x** (`.yaml` or `.json`) is also supported.

## Configuration

Key environment variables:

```bash
DOCS_ROOT=/path/to/docs          # Required: documentation root directory
MCP_DOCS_CACHE_TTL=3600          # Cache TTL in seconds
MCP_DOCS_SEARCH_LIMIT=10         # Max search results
MCP_DOCS_WEB_PORT=8123           # Web server port
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
```

## Running Modes

```bash
your-docs-server   # MCP server + web interface
your-docs-mcp      # MCP server only
your-docs-web      # Web interface only
```

## Development

```bash
git clone https://github.com/esola-thomas/your-docs-mcp
cd your-docs-mcp
pip install -e ".[dev,vector,pdf]" --extra-index-url https://download.pytorch.org/whl/cpu
pytest
ruff check .
```

## Contributing

See the [contributing guide](docs/development/contributing.md) for details on running tests, code style, and submitting pull requests. Open an [issue](https://github.com/esola-thomas/your-docs-mcp/issues) to report bugs or request features.

## License

MIT - see [LICENSE](LICENSE) for details.

## Links

- [PyPI](https://pypi.org/project/your-docs-mcp/)
- [Issue tracker](https://github.com/esola-thomas/your-docs-mcp/issues)
- [Documentation](docs/)
- [MCP specification](https://modelcontextprotocol.io)
