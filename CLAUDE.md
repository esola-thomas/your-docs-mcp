# your-docs-mcp

Hierarchical Documentation MCP Server — gives AI assistants structured access to documentation via the Model Context Protocol.

## Commands

- **Install**: `pip install -e ".[dev]"` (dev) or `pip install -e ".[dev,vector,pdf]"` (all features)
- **Test**: `pytest` (all) or `pytest tests/unit/` `tests/integration/` `tests/contract/`
- **Lint**: `ruff check .` and `ruff format .`
- **Type check**: `mypy docs_mcp/`
- **Run MCP server**: `your-docs-mcp` (stdio)
- **Run web server**: `your-docs-web` (HTTP on port 8123)
- **Run both**: `your-docs-server`
- **Validate docs**: `python scripts/validate_docs.py`

## Architecture

```
docs_mcp/
├── __main__.py          # CLI entry points (mcp_main, web_main, main)
├── server.py            # MCP server (FastMCP, stdio transport)
├── config.py            # Pydantic settings (env vars, YAML config)
├── web.py               # FastAPI web server + REST API
├── handlers/
│   ├── tools.py         # MCP tool implementations (search, navigate, PDF)
│   └── resources.py     # MCP resource handlers
├── models/
│   ├── document.py      # Document, DocumentationSource models
│   ├── navigation.py    # Category, SearchResult models
│   └── openapi.py       # OpenAPI spec models
├── services/
│   ├── markdown.py      # Markdown parsing, YAML frontmatter scanning
│   ├── hierarchy.py     # Category tree building, navigation
│   ├── search.py        # Full-text search with relevance scoring
│   ├── vector.py        # ChromaDB semantic search (optional)
│   └── cache.py         # TTL caching with auto-invalidation
├── security/
│   ├── path_validator.py # Directory traversal prevention
│   └── sanitizer.py     # Query input sanitization
└── utils/
    └── logger.py        # Structured logging
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
