# Quickstart: Implementing Test Coverage Improvements

**Feature**: 002-test-coverage  
**Date**: 2025-11-13  
**Time to Complete**: 2-4 hours

## Prerequisites

- Python 3.11+ installed
- Repository cloned and on branch `002-test-coverage`
- Dependencies installed: `pip install -e ".[dev]"`
- Baseline coverage confirmed: `pytest --cov=hierarchical_docs_mcp`

## Quick Start (5 minutes)

### 1. Verify Current State

```bash
# Check you're on the correct branch
git branch --show-current  # Should show: 002-test-coverage

# Run tests to confirm baseline
pytest --cov=hierarchical_docs_mcp --cov-report=term

# Expected output:
# TOTAL    942     48    95%
# Required test coverage of 80% reached. Total coverage: 94.90%
```

### 2. Review Coverage Gaps

```bash
# Generate HTML coverage report
pytest --cov=hierarchical_docs_mcp --cov-report=html

# Open in browser
firefox htmlcov/index.html  # or your preferred browser
```

Key files to review:
- `server.py` - 26 missing lines (Priority 1)
- `models/document.py` - 4 missing lines (Priority 2)
- `models/navigation.py` - 4 missing lines (Priority 2)
- Service files - 13 missing lines total (Priority 3)
- `__main__.py` - 1 missing line (Priority 4)

### 3. Start with High Impact Tests

Begin with server handler tests (biggest impact):

```bash
# Open the server test file
code tests/unit/test_server.py

# Review existing patterns
# Look for: @pytest.mark.asyncio, fixtures, AsyncMock usage
```

## Implementation Phases

### Phase 1: Server Handler Tests (~1 hour)

**Goal**: Cover lines 42, 144-173, 178-179, 192-197, 235-236 in server.py

#### Step 1.1: Test list_tools Handler

Add to `tests/unit/test_server.py`:

```python
@pytest.mark.asyncio
async def test_list_tools_handler_returns_all_tools(self, server):
    """Test that list_tools handler returns all 5 tools."""
    # Access the registered handler
    tools = await server.server._tool_handlers['list_tools']()
    
    # Verify all tools are present
    assert len(tools) == 5
    tool_names = [t.name for t in tools]
    assert "search_documentation" in tool_names
    assert "navigate_to" in tool_names
    assert "get_table_of_contents" in tool_names
    assert "search_by_tags" in tool_names
    assert "get_document" in tool_names
```

#### Step 1.2: Test call_tool Handler

```python
@pytest.mark.asyncio
async def test_call_tool_with_unknown_tool_raises_error(self, server):
    """Test that call_tool raises ValueError for unknown tool."""
    await server.initialize()
    
    with pytest.raises(ValueError, match="Unknown tool"):
        await server.server._tool_handlers['call_tool'](
            "invalid_tool_name",
            {}
        )
```

#### Step 1.3: Test Resource Handlers

```python
@pytest.mark.asyncio
async def test_list_resources_handler_formats_correctly(self, server):
    """Test that list_resources returns properly formatted resources."""
    await server.initialize()
    
    resources = await server.server._resource_handlers['list_resources']()
    
    # Verify resource format
    for resource in resources:
        assert hasattr(resource, 'uri')
        assert hasattr(resource, 'name')
        assert hasattr(resource, 'mimeType')
```

#### Verify Progress

```bash
pytest tests/unit/test_server.py --cov=hierarchical_docs_mcp/server.py --cov-report=term
```

Expected: Server coverage increases from 64% toward 100%

---

### Phase 2: Model Property Tests (~30 minutes)

**Goal**: Cover lines in document.py and navigation.py

#### Step 2.1: Test Document.excerpt()

Create or add to `tests/unit/test_document.py`:

```python
from hierarchical_docs_mcp.models.document import Document
from datetime import datetime, UTC
from pathlib import Path

def test_document_excerpt_strips_frontmatter():
    """Test that excerpt removes frontmatter delimiters."""
    doc = Document(
        uri="docs://test",
        title="Test",
        content="---\ntitle: Test\n---\n\nActual content here",
        file_path=Path("/test.md"),
        relative_path=Path("test.md"),
        size_bytes=100,
        last_modified=datetime.now(UTC)
    )
    
    excerpt = doc.excerpt(200)
    assert "---" not in excerpt
    assert "Actual content" in excerpt

def test_document_excerpt_truncates_long_content():
    """Test that excerpt truncates at word boundary."""
    long_content = " ".join(["word"] * 100)
    doc = Document(
        uri="docs://test",
        title="Test",
        content=long_content,
        file_path=Path("/test.md"),
        relative_path=Path("test.md"),
        size_bytes=len(long_content),
        last_modified=datetime.now(UTC)
    )
    
    excerpt = doc.excerpt(50)
    assert len(excerpt) <= 53  # 50 + "..."
    assert excerpt.endswith("...")
```

#### Step 2.2: Test Navigation Properties

Create or add to `tests/unit/test_navigation.py`:

```python
from hierarchical_docs_mcp.models.navigation import Category, NavigationContext

def test_category_breadcrumbs_empty_path():
    """Test breadcrumbs with empty path returns empty list."""
    category = Category(
        name="root",
        label="Root",
        uri="docs://",
        depth=0,
        source_category="root"
    )
    
    assert category.breadcrumbs == []

def test_navigation_context_can_navigate_up_without_parent():
    """Test can_navigate_up returns False when no parent."""
    context = NavigationContext(
        current_uri="docs://root",
        current_type="category",
        parent_uri=None
    )
    
    assert context.can_navigate_up == False

def test_navigation_context_can_navigate_down_with_children():
    """Test can_navigate_down returns True with children."""
    context = NavigationContext(
        current_uri="docs://category",
        current_type="category",
        children=[{"name": "child", "uri": "docs://category/child"}]
    )
    
    assert context.can_navigate_down == True
```

#### Verify Progress

```bash
pytest tests/unit/test_document.py tests/unit/test_navigation.py \
  --cov=hierarchical_docs_mcp/models --cov-report=term
```

Expected: Model coverage increases to 100%

---

### Phase 3: Service Error Path Tests (~30 minutes)

**Goal**: Cover error handling in cache, hierarchy, markdown, search

#### Step 3.1: Test Cache Edge Cases

Add to `tests/unit/test_cache.py`:

```python
def test_evict_oldest_with_empty_cache():
    """Test that _evict_oldest handles empty cache gracefully."""
    cache = DocumentCache()
    
    # Explicitly empty the cache
    cache._cache.clear()
    
    # Should not raise exception
    cache._evict_oldest()
    
    # Cache should still be empty
    assert len(cache._cache) == 0
```

#### Step 3.2: Test Hierarchy Edge Cases

Add to `tests/unit/test_hierarchy.py`:

```python
def test_get_navigation_context_empty_breadcrumbs(sample_documents):
    """Test navigation context with document at root (empty breadcrumbs)."""
    # Create document with no parent path
    doc = sample_documents[0]
    doc.breadcrumbs = []  # Force empty breadcrumbs
    
    context = get_navigation_context(doc.uri, sample_documents, {})
    
    assert context.parent_uri == "docs://"
```

#### Step 3.3: Test Service Error Handlers

Add to `tests/unit/test_markdown.py` and `tests/unit/test_search.py`:

```python
from unittest.mock import patch

def test_extract_excerpt_exception_handling():
    """Test that _extract_excerpt handles exceptions gracefully."""
    with patch('hierarchical_docs_mcp.services.markdown.re.search') as mock_search:
        mock_search.side_effect = Exception("Test error")
        
        content = "A" * 500
        result = _extract_excerpt(content, "query", 200)
        
        # Should return fallback, not raise
        assert isinstance(result, str)
        assert len(result) <= 403  # 400 + "..."

def test_highlight_matches_exception_handling():
    """Test that _highlight_matches handles malformed patterns."""
    result = _highlight_matches("test content", "**[invalid", "**")
    
    # Should return original text, not raise
    assert result == "test content"
```

#### Verify Progress

```bash
pytest tests/unit/test_cache.py tests/unit/test_hierarchy.py \
  tests/unit/test_markdown.py tests/unit/test_search.py \
  --cov=hierarchical_docs_mcp/services --cov-report=term
```

Expected: Service coverage increases to 100%

---

### Phase 4: Entry Point Test (~15 minutes)

**Goal**: Cover exception handling in __main__.py

#### Step 4.1: Test Main Exception Handling

Add to `tests/unit/test_main.py`:

```python
from unittest.mock import patch
import sys

def test_main_exception_handling():
    """Test that main() handles exceptions and exits with code 1."""
    with patch('hierarchical_docs_mcp.__main__.serve') as mock_serve:
        with patch('sys.exit') as mock_exit:
            # Make serve raise an exception
            mock_serve.side_effect = Exception("Test error")
            
            # Import and run main
            from hierarchical_docs_mcp.__main__ import main
            main()
            
            # Verify sys.exit(1) was called
            mock_exit.assert_called_once_with(1)
```

#### Verify Progress

```bash
pytest tests/unit/test_main.py \
  --cov=hierarchical_docs_mcp/__main__.py --cov-report=term
```

Expected: __main__.py coverage increases to 100%

---

## Final Verification

### Run Complete Test Suite

```bash
# Run all tests with coverage
pytest --cov=hierarchical_docs_mcp --cov-report=html --cov-report=term -v

# Check for warnings
pytest -v  # Should show 0 warnings

# Check execution time
pytest --durations=10  # Should complete in < 6 seconds
```

### Expected Results

```
Name                                               Stmts   Miss  Cover
----------------------------------------------------------------------
hierarchical_docs_mcp/__init__.py                      2      0   100%
hierarchical_docs_mcp/__main__.py                     22      0   100%
hierarchical_docs_mcp/server.py                       73      0   100%
hierarchical_docs_mcp/models/document.py              39      0   100%
hierarchical_docs_mcp/models/navigation.py            50      0   100%
hierarchical_docs_mcp/services/cache.py              100      0   100%
hierarchical_docs_mcp/services/hierarchy.py          116      0   100%
hierarchical_docs_mcp/services/markdown.py           107      0   100%
hierarchical_docs_mcp/services/search.py             103      0   100%
----------------------------------------------------------------------
TOTAL                                                942      0   100%

Required test coverage of 80% reached. Total coverage: 100.00%
========== 480+ passed in < 6.00s ==========
```

### View Coverage Report

```bash
firefox htmlcov/index.html
```

All modules should show 100% with no missing lines highlighted.

## Troubleshooting

### Tests Fail to Run

```bash
# Ensure dependencies installed
pip install -e ".[dev]"

# Check Python version
python --version  # Should be 3.11+
```

### Coverage Not Increasing

```bash
# Run specific test file with verbose coverage
pytest tests/unit/test_server.py --cov=hierarchical_docs_mcp/server.py \
  --cov-report=term-missing -v

# Check which lines are still missing
# Review test to ensure it actually executes those lines
```

### Async Tests Not Working

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check for @pytest.mark.asyncio decorator
# Verify AsyncMock is used for async mocks
```

### Tests Too Slow

```bash
# Identify slow tests
pytest --durations=10

# Common issues:
# - Real file I/O (use tempfile fixtures)
# - Network calls (should be mocked)
# - Sleep/wait operations (shouldn't exist in unit tests)
```

## Next Steps

After achieving 100% coverage:

1. **Commit Changes**:
   ```bash
   git add tests/
   git commit -m "test: achieve 100% unit test coverage
   
   - Add server handler tests (26 lines)
   - Add model property edge case tests (8 lines)
   - Add service error path tests (13 lines)
   - Add CLI exception handling test (1 line)
   
   Coverage: 94.90% → 100.00%
   Tests: 464 → 480+
   Time: 4.47s → <6s
   ```

2. **Push Branch**:
   ```bash
   git push origin 002-test-coverage
   ```

3. **Create Pull Request**:
   - Title: "Achieve 100% unit test coverage"
   - Reference: `specs/002-test-coverage/spec.md`
   - Include before/after coverage stats
   - Note test count increase and execution time

4. **Code Review**:
   - Verify all tests are meaningful (not just coverage inflation)
   - Check that patterns match existing tests
   - Confirm no warnings in output
   - Validate performance target met

## Resources

- **Feature Spec**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Test Contracts**: [contracts/test-requirements.md](./contracts/test-requirements.md)
- **Coverage Analysis**: [coverage-analysis.md](./coverage-analysis.md)

## Time Estimates

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 0 | Setup & verification | 5 minutes |
| 1 | Server handler tests | 60 minutes |
| 2 | Model property tests | 30 minutes |
| 3 | Service error path tests | 30 minutes |
| 4 | Entry point test | 15 minutes |
| Final | Verification & commit | 10 minutes |
| **Total** | | **2.5 hours** |

Add buffer for troubleshooting: **3-4 hours total**

## Success Checklist

- [ ] All phases completed
- [ ] Coverage report shows 100%
- [ ] All tests pass (0 failures)
- [ ] No warnings in output
- [ ] Execution time < 6 seconds
- [ ] Tests follow existing patterns
- [ ] Meaningful assertions (not just coverage)
- [ ] Changes committed to branch
- [ ] Ready for pull request
