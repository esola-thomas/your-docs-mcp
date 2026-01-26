---
title: Contributing Guide
tags: [development, contributing, guide]
category: Development
order: 1
---

# Contributing Guide

Thank you for your interest in contributing to the Hierarchical Documentation MCP project!

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/esola-thomas/Markdown-MCP
cd Markdown-MCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install with development dependencies
pip install -e ".[dev]"
```

### Verify Setup

```bash
# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy docs_mcp
```

## Project Structure

```text
├── docs_mcp/           # Main package
│   ├── handlers/       # MCP protocol handlers
│   ├── models/         # Data models
│   ├── services/       # Business logic
│   ├── security/       # Security utilities
│   ├── static/         # Web UI assets
│   └── utils/          # Shared utilities
├── tests/              # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── contract/       # Contract tests
├── docs/               # Documentation
└── scripts/            # Development scripts
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the code style guidelines (see below).

### 3. Write Tests

All new code should have tests:

```bash
# Run tests with coverage
pytest --cov=docs_mcp

# Target: 80% minimum, 95% preferred
```

### 4. Run Quality Checks

```bash
# Linting
ruff check .

# Type checking
mypy docs_mcp

# Format code
ruff format .
```

### 5. Submit Pull Request

- Write a clear description
- Reference any related issues
- Ensure CI passes

## Code Style

### Python Guidelines

- Follow PEP 8 style guide
- Use type hints for all public functions
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Example

```python
from typing import Optional

from docs_mcp.models.document import Document


async def search_documents(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
) -> list[Document]:
    """Search documents by query.

    Args:
        query: Search query string.
        category: Optional category filter.
        limit: Maximum number of results.

    Returns:
        List of matching documents.
    """
    # Implementation
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed spanning
    multiple lines.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When something is wrong.
    """
```

## Testing Guidelines

### Test Structure

```python
import pytest

from docs_mcp.services.search import search_documents


class TestSearchDocuments:
    """Tests for search_documents function."""

    async def test_search_returns_results(self):
        """Search should return matching documents."""
        results = await search_documents("test query")
        assert len(results) > 0

    async def test_search_respects_limit(self):
        """Search should respect the limit parameter."""
        results = await search_documents("query", limit=5)
        assert len(results) <= 5
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_search.py

# With coverage report
pytest --cov=docs_mcp --cov-report=html
```

## Documentation

### Adding Documentation

1. Create markdown file in appropriate `docs/` subdirectory
2. Include YAML frontmatter:
   ```yaml
   ---
   title: Your Title
   tags: [relevant, tags]
   category: Category Name
   order: 1
   ---
   ```
3. Write clear, concise content
4. Include code examples where helpful

### Documentation Validation

```bash
python scripts/validate_docs.py docs/
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create pull request
4. After merge, tag the release
5. CI/CD handles publishing to PyPI

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Review existing issues before creating new ones

## Code of Conduct

Be respectful and inclusive. We welcome contributors of all backgrounds and experience levels.
