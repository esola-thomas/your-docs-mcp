# Contributing to Hierarchical Documentation MCP Server

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Project Constitution

**IMPORTANT**: This project follows strict development principles defined in `.specify/memory/constitution.md`. All contributions must comply with:

- **Library-First Architecture**: Self-contained, independently testable modules
- **Protocol Compliance**: Strict MCP specification adherence
- **Test-First Development**: TDD mandatory (write tests before implementation)
- **Security-By-Design**: Path validation, input sanitization, audit logging
- **Performance & Observability**: Measured performance targets, structured logging

Pull requests that violate these principles without documented justification will be rejected.

Read the full constitution before contributing: [.specify/memory/constitution.md](.specify/memory/constitution.md)

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [CI/CD Pipeline](#cicd-pipeline)

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/esola-thomas/Markdown-MCP.git
   cd Markdown-MCP
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/esola-thomas/Markdown-MCP.git
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git

### Installation

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

This installs:
- The main package with all dependencies
- Development tools (pytest, ruff, mypy, etc.)

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Contract tests (MCP protocol compliance)
pytest tests/contract/

# Security tests
pytest tests/unit/test_path_validator.py tests/unit/test_sanitizer.py
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=hierarchical_docs_mcp --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Fast Tests (for quick iteration)

```bash
pytest tests/unit/ -x --maxfail=5
```

## Code Style

### Linting

We use **Ruff** for linting and formatting:

```bash
# Check for issues
ruff check hierarchical_docs_mcp/ tests/

# Auto-fix issues
ruff check --fix hierarchical_docs_mcp/ tests/

# Format code
ruff format hierarchical_docs_mcp/ tests/
```

### Type Checking

We use **MyPy** for type checking:

```bash
mypy hierarchical_docs_mcp/ --ignore-missing-imports
```

### Code Standards

- **Line length**: 100 characters
- **Python version**: Target 3.11+
- **Imports**: Sorted and organized (Ruff handles this)
- **Type hints**: Required for all public functions
- **Docstrings**: Required for all public classes and functions

Example:

```python
def validate_path(
    requested_path: str | Path,
    allowed_root: str | Path,
    allow_hidden: bool = False,
) -> Path:
    """Validate that a requested path is safe and within allowed directory.

    Args:
        requested_path: The path to validate
        allowed_root: The root directory that paths must be within
        allow_hidden: Whether to allow hidden files (starting with '.')

    Returns:
        Resolved absolute path if valid

    Raises:
        PathValidationError: If path is invalid or outside allowed root
    """
    # Implementation...
```

## Submitting Changes

### Before Submitting

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the code style guidelines

3. **Write tests** for your changes:
   - Unit tests for new functions
   - Integration tests for new features
   - Update existing tests if behavior changes

4. **Run the full test suite**:
   ```bash
   pytest tests/
   ```

5. **Run linting and formatting**:
   ```bash
   ruff check --fix .
   ruff format .
   ```

6. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "feat: add support for OpenAPI 3.1 specs"
   # or
   git commit -m "fix: resolve path traversal vulnerability in validate_path"
   ```

### Commit Message Format

We follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks
- `ci:` CI/CD changes

### Creating a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub:
   - Use the pull request template
   - Provide a clear title and description
   - Link related issues
   - Add screenshots if applicable

3. **Wait for CI checks** to pass:
   - Tests must pass
   - Linting must pass
   - Coverage should not decrease significantly

4. **Respond to review feedback** promptly

## CI/CD Pipeline

Our CI/CD pipeline automatically runs on all pull requests and includes:

### Test Jobs

- **Quick Test**: Fast unit tests (Python 3.11)
- **Full Test Suite**: All tests on Python 3.11 and 3.12
- **Integration Tests**: End-to-end workflow tests
- **Coverage Report**: Code coverage analysis (target: 80%+)

### Quality Checks

- **Ruff Linting**: Code style and quality
- **Ruff Formatting**: Code formatting consistency
- **MyPy**: Type checking (advisory, doesn't block)

### Security Checks

- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking

### Required Status Checks

For a PR to be mergeable:
- ✅ All tests must pass
- ✅ Linting must pass
- ✅ Coverage must be ≥80%

Security checks are advisory and won't block merging.

## Development Workflow

### Typical Development Cycle

1. **Pick an issue** or create one for discussion
2. **Create a branch** from `main`
3. **Write tests** (TDD approach preferred)
4. **Implement the feature** or fix
5. **Run tests locally** to ensure they pass
6. **Commit and push** your changes
7. **Create a PR** and wait for review
8. **Address feedback** and update the PR
9. **Merge** when approved and CI passes

### Working with the Test Suite

#### Adding New Tests

Place tests in the appropriate directory:

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests across components
- `tests/contract/` - MCP protocol compliance tests

Example test structure:

```python
import pytest
from hierarchical_docs_mcp.services.markdown import parse_markdown

class TestMarkdownParsing:
    """Test markdown parsing functionality."""

    def test_parse_valid_frontmatter(self):
        """Test parsing markdown with valid YAML frontmatter."""
        content = """---
title: Test
---
# Content
"""
        result = parse_markdown(content)
        assert result.title == "Test"
```

#### Running Specific Tests

```bash
# Run a specific test file
pytest tests/unit/test_markdown.py

# Run a specific test class
pytest tests/unit/test_markdown.py::TestMarkdownParsing

# Run a specific test
pytest tests/unit/test_markdown.py::TestMarkdownParsing::test_parse_valid_frontmatter

# Run with verbose output
pytest -vv tests/unit/test_markdown.py
```

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/esola-thomas/Markdown-MCP/discussions)
- **Bugs**: Create a [Bug Report](https://github.com/esola-thomas/Markdown-MCP/issues/new?template=bug_report.md)
- **Feature Requests**: Create a [Feature Request](https://github.com/esola-thomas/Markdown-MCP/issues/new?template=feature_request.md)

## Code of Conduct

Please note that this project follows a Code of Conduct. By participating, you agree to uphold this code. Please report unacceptable behavior to the project maintainers.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).
