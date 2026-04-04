# your-docs-mcp

Hierarchical Documentation MCP Server — gives AI assistants structured access to documentation via the Model Context Protocol.

## Commands

- **Install**: `pip install -e ".[dev]"` (dev) or `pip install -e ".[dev,vector,pdf]"` (all features)
- **Test**: `pytest` (all) or `pytest tests/unit/` `tests/integration/` `tests/contract/`
- **Lint**: `ruff check .` and `ruff format .`
- **Type check**: `mypy docs_mcp/`
- **Run MCP server**: `your-docs-mcp` (stdio, for AI clients)
- **Run web server**: `your-docs-server` (HTTP on port 8123, with MCP SSE transport)
- **Validate docs**: `python scripts/validate_docs.py`

## Architecture

```
docs_mcp/
├── __main__.py          # CLI entry points (mcp_main, main)
├── core/
│   ├── config.py        # Pydantic settings (env vars, YAML config)
│   ├── models/          # Document, Category, SearchResult models
│   ├── services/        # Markdown parsing, hierarchy, search, cache
│   ├── security/        # Path validation, input sanitization
│   └── utils/           # Structured logging
├── mcp/
│   ├── server.py        # MCP server (stdio transport)
│   └── handlers/
│       ├── registry.py  # Shared MCP handler registration (tools + resources)
│       ├── tools.py     # MCP tool implementations (search, navigate, PDF)
│       └── resources.py # MCP resource handlers
├── web/
│   ├── app.py           # FastAPI web server + REST API + MCP SSE
│   ├── routes.py        # Server-rendered documentation pages
│   ├── partials.py      # HTMX partial endpoints
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS, JS, vendor assets
├── vector/              # ChromaDB semantic search (optional)
└── pdf/                 # PDF documentation generation
```

## Conventions

- **Ruff**: line-length 100, target py310, select E/F/I/N/W/UP, ignore E501
- **Type hints**: required on all public interfaces
- **Async**: use async/await for all I/O operations
- **Models**: Pydantic v2 with strict typing
- **Logging**: use `docs_mcp.utils.logger` for structured logging
- **Tests**: pytest + pytest-asyncio, 80% min coverage (target 95%+)
- **TDD**: write tests first, verify they fail, then implement (see constitution)

## Key References

- Constitution: `.specify/memory/constitution.md` (5 non-negotiable principles)
- Doc standards: `.claude/DOCUMENTATION_STANDARDS.md`
- Feature specs: `specs/` directory
