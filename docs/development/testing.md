---
title: Testing Guide
tags: [development, testing, pytest, tdd]
category: Development
order: 2
---

# Testing Guide

This guide covers the testing practices and tools used in the project.

## Test Philosophy

The project follows **Test-Driven Development (TDD)** principles:
- Minimum 80% code coverage required
- Target 95%+ coverage for new code
- All new features require tests before implementation

## Test Structure

```text
tests/
├── __init__.py
├── conftest.py         # Shared fixtures
├── unit/               # Unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_handlers.py
├── integration/        # Integration tests
│   ├── test_mcp_protocol.py
│   └── test_web_api.py
└── contract/           # Contract tests
    └── test_mcp_contract.py
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_search.py

# Run specific test function
pytest tests/unit/test_search.py::test_search_returns_results

# Run tests matching pattern
pytest -k "search"
```

### Coverage

```bash
# Run with coverage report
pytest --cov=docs_mcp

# Generate HTML report
pytest --cov=docs_mcp --cov-report=html
# Open htmlcov/index.html

# Fail if below threshold
pytest --cov=docs_mcp --cov-fail-under=80
```

## Writing Tests

### Unit Tests

Test individual functions and classes in isolation:

```python
import pytest

from docs_mcp.models.document import Document


class TestDocument:
    """Tests for Document model."""

    def test_document_creation(self):
        """Document can be created with required fields."""
        doc = Document(
            uri="docs://test",
            title="Test Document",
            content="Test content",
            category="Test",
        )
        assert doc.title == "Test Document"
        assert doc.uri == "docs://test"

    def test_document_requires_title(self):
        """Document raises error without title."""
        with pytest.raises(ValueError):
            Document(uri="docs://test", content="Test")
```

### Async Tests

Use `pytest-asyncio` for async functions:

```python
import pytest

from docs_mcp.services.search import search_documents


@pytest.mark.asyncio
async def test_search_documentation():
    """Search returns relevant results."""
    results = await search_documents("authentication")
    assert len(results) > 0
    assert any("auth" in r.title.lower() for r in results)
```

### Fixtures

Define reusable test data in `conftest.py`:

```python
import pytest

from docs_mcp.models.document import Document


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    return Document(
        uri="docs://test/sample",
        title="Sample Document",
        content="This is sample content for testing.",
        category="Test",
        tags=["test", "sample"],
    )


@pytest.fixture
def sample_documents(sample_document) -> list[Document]:
    """Create a list of sample documents."""
    return [
        sample_document,
        Document(
            uri="docs://test/another",
            title="Another Document",
            content="More test content.",
            category="Test",
        ),
    ]
```

### Mocking

Use `pytest-mock` for mocking dependencies:

```python
from unittest.mock import AsyncMock


async def test_search_with_mock(mocker):
    """Test search with mocked vector store."""
    mock_store = mocker.patch(
        "docs_mcp.services.search.get_vector_store"
    )
    mock_store.return_value.search = AsyncMock(return_value=[])

    results = await search_documents("query")

    mock_store.return_value.search.assert_called_once()
```

## Integration Tests

Test components working together:

```python
import pytest
from httpx import AsyncClient

from docs_mcp.web import create_app


@pytest.fixture
async def client():
    """Create test client for web API."""
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_search_endpoint(client):
    """Search endpoint returns results."""
    response = await client.get("/api/search?query=test")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
```

## Contract Tests

Verify MCP protocol compliance:

```python
from mcp.types import Tool


def test_search_tool_schema():
    """Search tool matches MCP specification."""
    tool = create_search_tool()

    assert isinstance(tool, Tool)
    assert tool.name == "search_documentation"
    assert "query" in tool.inputSchema["properties"]
    assert "query" in tool.inputSchema["required"]
```

## Test Configuration

### pytest.ini

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["docs_mcp"]
omit = ["tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch

CI configuration validates:
- All tests pass
- Coverage meets threshold
- Linting passes
- Type checking passes

## Debugging Tests

### Verbose Output

```bash
pytest -v --tb=long
```

### Print Statements

```bash
pytest -s  # Shows print output
```

### Debug with pdb

```python
def test_something():
    import pdb; pdb.set_trace()
    # ... test code
```

```bash
pytest --pdb  # Drop into debugger on failure
```

## Best Practices

1. **One assertion per test** - Makes failures clear
2. **Descriptive names** - `test_search_returns_empty_for_no_matches`
3. **Arrange-Act-Assert** - Clear test structure
4. **Independent tests** - No dependencies between tests
5. **Fast tests** - Unit tests should be milliseconds

## Next Steps

- [Contributing Guide](contributing.md) - Development workflow
- [Architecture Overview](../architecture/overview.md) - System design
- [CI/CD Integration](../ci-cd-integration.md) - Pipeline setup
