# your-docs-server

Full-featured documentation server with MCP protocol support, server-rendered web UI, and REST API.

This is a convenience meta-package that installs [`your-docs-mcp`](https://pypi.org/project/your-docs-mcp/) with the `[server]` extras (MCP + web server + OpenAPI support).

## Installation

```bash
pip install your-docs-server
```

This is equivalent to:

```bash
pip install "your-docs-mcp[server]"
```

## Quick Start

```bash
# Point to your markdown documentation
export DOCS_ROOT=/path/to/your/docs

# Start the server (MCP + Web UI)
your-docs-server
```

The web UI is available at `http://127.0.0.1:8123/docs/` with:
- Server-rendered documentation pages with full SEO support
- Search with keyword + semantic matching
- Dark/light theme toggle
- Mobile-responsive layout
- REST API at `/api/*`
- MCP protocol via SSE at `/sse`

## Other Install Flavors

| Command | What you get |
|---------|-------------|
| `pip install your-docs-mcp` | MCP server only (for Claude Desktop, VS Code) |
| `pip install your-docs-server` | Full server (MCP + Web UI + REST API) |
| `pip install "your-docs-mcp[full]"` | Everything (+ vector search + PDF generation) |

For full documentation, configuration, and API reference, see the [main project repository](https://github.com/esola-thomas/your-docs-mcp).
