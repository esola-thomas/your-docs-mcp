# Test Coverage Contracts

**Feature**: 002-test-coverage  
**Date**: 2025-11-13

## Overview

This document defines the "contracts" (requirements and expectations) for test coverage improvements. Unlike API contracts, these are testing contracts that specify what must be tested and how.

## Test Coverage Contracts

### Contract 1: Server Module Handler Testing

**Requirement**: All server handlers must be tested with both valid and invalid inputs

**Handler Functions to Test**:
1. `list_tools()` - Must return 5 tools with correct schemas
2. `call_tool(name, arguments)` - Must handle all 5 tool types + error case
3. `list_resources()` - Must return formatted Resource objects
4. `read_resource(uri)` - Must handle valid URIs and error on invalid

**Input Scenarios**:
- Valid inputs for each tool/resource type
- Invalid tool names (should raise ValueError)
- Invalid resource URIs (should raise ValueError)
- Edge cases (empty arguments, missing required fields)

**Expected Outputs**:
```python
# list_tools() returns:
[
    Tool(name="search_documentation", ...),
    Tool(name="navigate_to", ...),
    Tool(name="get_table_of_contents", ...),
    Tool(name="search_by_tags", ...),
    Tool(name="get_document", ...)
]

# call_tool() with valid input returns:
[{"type": "text", "text": json.dumps(result, indent=2)}]

# call_tool() with invalid name raises:
ValueError("Unknown tool: {name}")

# list_resources() returns:
[Resource(uri=..., name=..., mimeType="text/markdown", description=...)]

# read_resource() with invalid URI raises:
ValueError(error_message)
```

**Verification**:
- Lines 42, 144-173, 178-179, 192-197, 235-236 in server.py covered
- All assertion types: return value, exception type, exception message
- Mock dependencies: documents, categories, search_limit

---

### Contract 2: Model Computed Property Testing

**Requirement**: All computed properties and helper methods must be tested with edge cases

**Properties/Methods to Test**:

1. **Document.excerpt(max_length)**:
   - With frontmatter (should strip it)
   - With long content (should truncate at word boundary)
   - With short content (should return as-is)
   - With empty content (should handle gracefully)

2. **Category.breadcrumbs**:
   - With valid path (should return list of dicts)
   - With empty path (should return empty list)
   - Without "docs://" prefix (should return empty list)

3. **NavigationContext.can_navigate_up**:
   - With parent_uri = None (should return False)
   - With parent_uri set (should return True)

4. **NavigationContext.can_navigate_down**:
   - With empty children (should return False)
   - With children present (should return True)

5. **Category.is_root**:
   - With depth = 0 (should return True)
   - With depth > 0 (should return False)

**Expected Behaviors**:
```python
# Document.excerpt() with frontmatter
content = "---\ntitle: Test\n---\n\nActual content here"
doc.excerpt(20) == "Actual content here"

# Document.excerpt() with long content
content = "A" * 300
doc.excerpt(200).endswith("...") == True

# Category.breadcrumbs with empty path
category.uri = "docs://"
category.breadcrumbs == []

# NavigationContext.can_navigate_up
context.parent_uri = None
context.can_navigate_up == False

# NavigationContext.can_navigate_down
context.children = [{"name": "child"}]
context.can_navigate_down == True
```

**Verification**:
- Lines 55-57, 64 in document.py covered
- Lines 25, 29, 75, 80 in navigation.py covered
- Edge cases handled without exceptions

---

### Contract 3: Service Error Path Testing

**Requirement**: All error handling paths must be tested with exception injection

**Error Paths to Test**:

1. **DocumentCache._evict_oldest()** with empty cache:
   - Should return immediately without error
   - Should not attempt to access cache keys

2. **get_navigation_context()** with empty breadcrumbs:
   - Should set parent_uri to "docs://" (root)
   - Should not crash on empty breadcrumb list

3. **Markdown service error handlers**:
   - `_extract_excerpt()` with exception during processing
   - `_highlight_matches()` with malformed regex pattern

4. **Search service error handlers**:
   - `_extract_excerpt()` with exception during extraction
   - `_highlight_matches()` with invalid query pattern

**Mocking Strategy**:
```python
# For cache eviction with empty cache
cache = DocumentCache()
cache._cache = {}  # Explicitly empty
cache._evict_oldest()  # Should not raise

# For excerpt/highlight exceptions
with patch('module.operation') as mock_op:
    mock_op.side_effect = Exception("Test error")
    result = _extract_excerpt(...)
    # Should return fallback, not raise
```

**Expected Behaviors**:
```python
# Cache eviction returns None on empty
_evict_oldest() -> None  # No exception

# Hierarchy handles empty breadcrumbs
get_navigation_context(doc_with_empty_breadcrumbs)
assert result.parent_uri == "docs://"

# Markdown error handlers return fallback
_extract_excerpt(content_that_raises) -> truncated_content[:400] + "..."
_highlight_matches(text_that_raises) -> original_text

# Search error handlers return fallback
_extract_excerpt(content_that_raises) -> truncated_content[:400] + "..."
_highlight_matches(text_that_raises) -> original_text
```

**Verification**:
- Lines 174 (cache), 290 (hierarchy) covered
- Lines 219-221, 260-261 (markdown) covered
- Lines 234-236, 253-255 (search) covered
- All error paths return gracefully, no unhandled exceptions

---

### Contract 4: Entry Point Exception Testing

**Requirement**: CLI main() function must handle exceptions gracefully

**Scenarios to Test**:

1. **Configuration exception during startup**:
   - Mock `serve()` to raise Exception
   - Verify error printed to stderr
   - Verify sys.exit(1) called

**Mocking Strategy**:
```python
with patch('hierarchical_docs_mcp.__main__.serve') as mock_serve:
    with patch('sys.exit') as mock_exit:
        mock_serve.side_effect = Exception("Test error")
        main()
        mock_exit.assert_called_once_with(1)
```

**Expected Behavior**:
```python
# When serve() raises exception
main()  # Should catch exception
# Should print: "Error: {exception message}"
# Should call: sys.exit(1)
```

**Verification**:
- Line 41 in __main__.py covered
- Exception caught and handled
- Exit code = 1 for errors

---

## Performance Contract

**Requirement**: Test suite must complete within performance budget

**Constraints**:
- Total execution time: < 6 seconds
- Per-test average: < 50ms (120 tests in 6s)
- No external I/O (filesystem operations via tempfile only)
- No network calls (all external services mocked)
- No sleep/wait operations

**Verification Method**:
```bash
pytest --durations=10  # Show 10 slowest tests
pytest --maxfail=1     # Fail fast if any test is too slow
```

**Test Performance Targets**:
- Simple property tests: < 10ms each
- Mock-heavy tests: < 20ms each
- Async handler tests: < 50ms each
- File operation tests: < 100ms each

---

## Code Quality Contract

**Requirement**: Tests must follow established patterns and conventions

**Pattern Requirements**:

1. **Test Organization**:
   - Test files match module names: `test_{module}.py`
   - Test classes group related functionality
   - Test function names describe scenario: `test_{what}_{when}_{then}`

2. **Fixture Usage**:
   - Use pytest fixtures for setup data
   - Function scope for mutable test data
   - Module/session scope for read-only data

3. **Async Testing**:
   - Use `@pytest.mark.asyncio` for async tests
   - Use `AsyncMock` for async function mocks
   - Properly await async operations

4. **Mocking**:
   - Use `patch` for function/method mocking
   - Use `AsyncMock` for async mocks
   - Use `MagicMock` for object mocks
   - Minimize mocking scope (only external dependencies)

5. **Assertions**:
   - Test positive and negative cases
   - Verify return values explicitly
   - Check exception types and messages
   - Validate side effects (mock calls, state changes)

**Anti-Patterns to Avoid**:
- Tests without assertions (coverage inflation)
- Tests dependent on execution order
- Over-mocking (mocking code under test)
- Brittle tests (depends on implementation details)
- Slow tests (I/O operations, sleeps)

---

## Acceptance Criteria

**All contracts must be met for feature completion**:

- [ ] Contract 1: All server handlers tested (26 lines covered)
- [ ] Contract 2: All model properties tested (8 lines covered)
- [ ] Contract 3: All service error paths tested (13 lines covered)
- [ ] Contract 4: Entry point exception tested (1 line covered)
- [ ] Performance: Test suite < 6 seconds
- [ ] Quality: Zero warnings in pytest output
- [ ] Coverage: 100% across all modules
- [ ] Patterns: All tests follow existing conventions

**Verification Command**:
```bash
pytest --cov=hierarchical_docs_mcp --cov-report=html --cov-report=term -v
```

**Expected Output**:
```
TOTAL                                                942    0   100%
Required test coverage of 80% reached. Total coverage: 100.00%
========== 480+ passed in < 6.00s ==========
```
