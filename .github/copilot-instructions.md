# Markdown-MCP Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-13

**Constitution**: See `.specify/memory/constitution.md` for non-negotiable principles and governance rules.

## Active Technologies

- Python 3.11+ (for MCP SDK compatibility and modern async features) (001-hierarchical-docs-mcp)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (for MCP SDK compatibility and modern async features): Follow standard conventions

## Recent Changes
- 002-test-coverage: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

- 2025-11-13: Established project constitution v1.0.0 with 5 core principles
- 001-hierarchical-docs-mcp: Added Python 3.11+ (for MCP SDK compatibility and modern async features)

## Development Principles

This project follows strict principles defined in the constitution:

1. **Library-First Architecture**: Self-contained, independently testable modules
2. **Protocol Compliance**: Strict MCP specification adherence
3. **Test-First Development**: TDD mandatory (80% min, 95%+ target coverage)
4. **Security-By-Design**: Path validation, input sanitization, audit logging
5. **Performance & Observability**: Measured targets, structured logging

See `.specify/memory/constitution.md` for full details.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
