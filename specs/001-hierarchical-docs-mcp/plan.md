# Implementation Plan: Hierarchical Documentation MCP Server

**Branch**: `001-hierarchical-docs-mcp` | **Date**: November 4, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-hierarchical-docs-mcp/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an open-source Model Context Protocol (MCP) server that enables AI assistants (Claude Desktop, GitHub Copilot) to navigate and query documentation through a hierarchical structure. The system will support markdown files with YAML frontmatter metadata and OpenAPI 3.x specifications, providing both structured navigation (via URI-based resources) and intelligent search capabilities. The server must work cross-platform with stdio transport for local use and HTTP transport for remote team deployments, with comprehensive security validation to prevent directory traversal and injection attacks.

## Technical Context

**Language/Version**: Python 3.11+ (for MCP SDK compatibility and modern async features)  
**Primary Dependencies**: 
- `mcp` SDK (official Model Context Protocol Python SDK)
- `pyyaml` (YAML frontmatter parsing)
- `pydantic` + `pydantic-settings` (configuration validation and data models)
- `openapi-spec-validator` (OpenAPI validation)
- `prance` (OpenAPI parsing with $ref resolution)
- `watchdog` (cross-platform file watching for cache invalidation)
- *Optional*: `whoosh` (full-text search if regex performance insufficient)

**Storage**: File system based (markdown files, OpenAPI YAML/JSON specs) - no database required  
**Testing**: pytest with pytest-asyncio (for async MCP handlers), pytest-mock  
**Target Platform**: Cross-platform (Linux, macOS, Windows) - stdio transport for local, HTTP for remote  
**Project Type**: Single library with CLI entry point (installable via pip/pipx)  
**Performance Goals**: 
- <2s document retrieval for 1GB documentation sets
- <3s search results for 5000 document corpus
- <500ms navigation operations
- Support 10 concurrent queries with <20% degradation

**Constraints**: 
- Must implement MCP protocol correctly per official spec
- Read-only operations (no file system writes through MCP)
- Path validation to prevent directory traversal
- Memory usage <1GB for 10k+ document sets
- Compatible with both Claude Desktop and VS Code/GitHub Copilot

**Scale/Scope**: 
- Handle documentation sets up to 10GB
- Support 10,000+ markdown files
- Multiple documentation sources per configuration
- Multiple OpenAPI spec files per configuration

**Research Resolution**: All technical uncertainties resolved in [research.md](./research.md):
- OpenAPI parser: openapi-spec-validator + prance combination
- Search strategy: Start with regex + caching, add whoosh if performance requires
- File watching: watchdog library for cross-platform support

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Status** (Pre-Phase 0): ✅ PASSED
- Constitution file is template-only (not yet customized for this project)
- Proceeding with standard Python project best practices

**Post-Design Status** (After Phase 1): ✅ PASSED

Design review confirms continued compliance:

- ✅ **Single library focus**: One MCP server library with clear purpose (hierarchical documentation access for AI assistants)
- ✅ **CLI interface**: MCP servers run as CLI processes via stdio transport (stdin/stdout protocol). No web UI or complex interfaces.
- ✅ **Test-first approach**: Contract tests for MCP protocol, integration tests for security, unit tests for all modules
- ✅ **Integration tests planned**: MCP protocol compliance, cross-platform compatibility (Claude/Copilot), security validation with attack patterns
- ✅ **Simplicity**: File-system based, no database, no complex abstractions. Start with regex search, add whoosh only if performance requires
- ✅ **Observability**: Text I/O for debuggability, structured logging for all operations, audit logging for security events

**Architecture Decisions Validated**:
- Models separate from services: Clear separation of data (models/) from logic (services/)
- No repository pattern needed: Direct file system access is simplest for read-only documentation
- Security layer isolated: Validation concentrated in security/ module, not scattered
- Caching is pragmatic: Simple TTL + file watching, no complex cache coordination

**No constitution violations identified.** Standard single-library Python project structure with appropriate separation of concerns.

## Project Structure

### Documentation (this feature)

```text
specs/001-hierarchical-docs-mcp/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (created by /speckit.plan)
├── data-model.md        # Phase 1 output (created by /speckit.plan)
├── quickstart.md        # Phase 1 output (created by /speckit.plan)
├── contracts/           # Phase 1 output (created by /speckit.plan)
│   └── mcp-protocol.json   # MCP tool/resource definitions
├── checklists/          # Spec validation
│   └── requirements.md  # Completed validation checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
docs_mcp/
├── __init__.py          # Package initialization, version
├── __main__.py          # CLI entry point for stdio transport
├── server.py            # MCP server initialization and configuration
├── config.py            # Configuration loading (env vars, YAML files)
├── models/              # Data models
│   ├── __init__.py
│   ├── document.py      # Document, Category entities
│   ├── navigation.py    # NavigationContext, SearchResult
│   └── openapi.py       # OpenAPI entities
├── handlers/            # MCP protocol handlers
│   ├── __init__.py
│   ├── tools.py         # Tool request handlers (search, navigate, etc.)
│   ├── resources.py     # Resource request handlers (URI-based access)
│   └── prompts.py       # Prompt handlers (if needed)
├── services/            # Core business logic
│   ├── __init__.py
│   ├── markdown.py      # Markdown parsing with frontmatter
│   ├── openapi_loader.py # OpenAPI spec parsing and validation
│   ├── search.py        # Full-text and metadata search engine
│   ├── hierarchy.py     # Tree traversal and navigation
│   └── cache.py         # Caching layer with TTL and invalidation
├── security/            # Security and validation
│   ├── __init__.py
│   ├── path_validator.py # Directory traversal prevention
│   └── sanitizer.py     # Query and content sanitization
└── utils/               # Utilities
    ├── __init__.py
    └── logger.py        # Structured logging

tests/
├── contract/            # MCP protocol compliance tests
│   ├── test_mcp_tools.py
│   └── test_mcp_resources.py
├── integration/         # Cross-platform and security tests
│   ├── test_claude_desktop.py
│   ├── test_vscode_copilot.py
│   └── test_security.py
└── unit/                # Unit tests for all modules
    ├── test_markdown.py
    ├── test_openapi_loader.py
    ├── test_search.py
    ├── test_hierarchy.py
    ├── test_cache.py
    ├── test_path_validator.py
    └── test_sanitizer.py

docs/                    # Sample documentation for testing
├── guides/
│   ├── getting-started.md
│   └── security/
│       └── authentication.md
└── api/
    └── openapi.yaml

pyproject.toml           # Project metadata and dependencies
README.md                # Usage documentation
.env.example             # Example configuration
```

**Structure Decision**: Single library project structure chosen because:
- MCP server is a standalone tool, not a web/mobile app
- No frontend/backend separation needed
- Python package installable via pip/pipx
- Clear separation: models (data), handlers (MCP protocol), services (business logic), security (validation)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
