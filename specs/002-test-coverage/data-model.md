# Data Model: Complete Unit Test Coverage

**Feature**: 002-test-coverage  
**Date**: 2025-11-13  
**Status**: Complete

## Overview

This feature adds test cases to achieve 100% coverage. It does not introduce new data models but instead tests existing data structures comprehensively. This document describes the test-related entities and their relationships.

## Core Entities

### Test Coverage Gap

**Purpose**: Represents an uncovered line or branch in the codebase that needs testing

**Attributes**:
- `module_name` (string): Fully qualified module name (e.g., "hierarchical_docs_mcp.server")
- `line_numbers` (list[int]): Specific line numbers not covered (e.g., [42, 144-173])
- `functional_area` (string): What functionality is untested (e.g., "handler registration", "error paths")
- `priority` (enum: P1-P4): Priority level based on impact and module importance
- `test_strategy` (string): Approach to cover the gap (e.g., "mock stdio_server", "test with empty cache")

**Relationships**:
- One Coverage Gap → One or more Test Cases
- One Module → Multiple Coverage Gaps

**Validation Rules**:
- Line numbers must exist in the module
- Priority must be justified by coverage percentage and module criticality
- Test strategy must be feasible with existing test infrastructure

### Test Case

**Purpose**: Represents a single unit test that exercises a specific code path

**Attributes**:
- `test_name` (string): Descriptive test function name (e.g., "test_list_tools_handler_returns_all_tools")
- `test_file` (string): Location in test suite (e.g., "tests/unit/test_server.py")
- `target_module` (string): Production module being tested
- `target_lines` (list[int]): Specific lines this test covers
- `test_type` (enum): "positive", "negative", "edge_case", "error_path"
- `setup_required` (list[string]): Fixtures or mocks needed
- `assertions` (list[string]): What is being verified
- `execution_time_target` (float): Expected test duration in seconds (< 0.05)

**Relationships**:
- One Test Case → One or more Coverage Gaps (may cover multiple lines)
- One Test File → Multiple Test Cases
- One Test Case → Zero or more Fixtures

**Validation Rules**:
- Test name must follow pytest convention (start with "test_")
- Must use @pytest.mark.asyncio for async code
- Must be independently runnable (no test order dependencies)
- Must not modify global state without cleanup

### Test Fixture

**Purpose**: Reusable test setup data or mock objects

**Attributes**:
- `fixture_name` (string): Name of the pytest fixture
- `scope` (enum): "function", "class", "module", "session"
- `provides` (string): What data/object it creates
- `dependencies` (list[string]): Other fixtures it requires
- `reusable` (boolean): Can it be shared across test modules

**Relationships**:
- One Fixture → Multiple Test Cases (many-to-many)
- One Fixture → Zero or more Fixtures (dependencies)

**Examples**:
- `sample_documents`: Creates list of Document instances
- `sample_categories`: Creates dictionary of Category instances
- `mock_config`: Creates ServerConfig for testing
- `temp_docs`: Creates temporary documentation directory

**Validation Rules**:
- Scope must match usage pattern (function-scoped for mutable data)
- Must clean up resources (temp files, connections)
- Dependencies must not create circular references

### Coverage Metric

**Purpose**: Tracks measured code coverage progress

**Attributes**:
- `module_name` (string): Module being measured
- `total_statements` (int): Total executable lines
- `covered_statements` (int): Lines executed during tests
- `coverage_percentage` (float): (covered / total) * 100
- `missing_lines` (list[int]): Specific uncovered lines
- `timestamp` (datetime): When measurement was taken

**Relationships**:
- One Module → One Coverage Metric per test run
- One Test Run → Multiple Coverage Metrics (one per module)

**State Transitions**:
```
Initial State (94.90%) 
  → Add P1 Tests → Intermediate State (~85%)
  → Add P2 Tests → Intermediate State (~92%)
  → Add P3 Tests → Intermediate State (~98%)
  → Add P4 Tests → Final State (100%)
```

**Validation Rules**:
- Percentage must be in range [0, 100]
- covered_statements <= total_statements
- Missing lines must correspond to actual uncovered code

## Test Organization Structure

### Test Module Hierarchy

```
tests/unit/
├── test_main.py              # CLI entry point tests
├── test_server.py            # Server lifecycle tests
├── test_handlers_tools.py    # Tool handler tests
├── test_handlers_resources.py # Resource handler tests
├── test_document.py          # Document model tests (may need creation)
├── test_navigation.py        # Navigation model tests (create if needed)
├── test_cache.py             # Cache service tests
├── test_hierarchy.py         # Hierarchy service tests
├── test_markdown.py          # Markdown service tests
└── test_search.py            # Search service tests
```

**Organization Rules**:
- One test file per production module (generally)
- Test file name matches module: `test_{module_name}.py`
- Test classes group related functionality: `class TestComponentName`
- Test functions are specific: `test_{what}_{when}_{then}`

## Test Data Patterns

### Mock Document Structure

```python
Document(
    uri="docs://category/document",
    title="Document Title",
    content="Full markdown content...",
    category="category",
    tags=["tag1", "tag2"],
    file_path=Path("/path/to/file.md"),
    relative_path=Path("category/file.md"),
    size_bytes=100,
    last_modified=datetime.now(UTC),
    frontmatter={"key": "value"}
)
```

### Mock Category Structure

```python
Category(
    name="category",
    label="Category Label",
    uri="docs://category",
    parent_uri="docs://",
    depth=1,
    child_categories=["docs://category/subcategory"],
    child_documents=["docs://category/document"],
    document_count=5,
    source_category="category"
)
```

### Mock Server Configuration

```python
ServerConfig(
    docs_root="/path/to/docs",
    sources=[DocumentationSource(...)],
    search_limit=10,
    allow_hidden=False,
    log_level="INFO"
)
```

## Coverage Gap to Test Case Mapping

### Priority 1: Server Module (26 lines)

**Coverage Gap**: server.py lines 42, 144-173, 178-179, 192-197, 235-236

**Test Cases**:
1. `test_list_tools_handler_returns_five_tools` → lines 144-173
2. `test_list_tools_handler_has_correct_schemas` → lines 144-173
3. `test_call_tool_search_documentation` → lines 144-173
4. `test_call_tool_navigate_to` → lines 144-173
5. `test_call_tool_get_table_of_contents` → lines 144-173
6. `test_call_tool_search_by_tags` → lines 144-173
7. `test_call_tool_get_document` → lines 144-173
8. `test_call_tool_unknown_tool_raises_error` → lines 144-173
9. `test_list_resources_handler_formats_correctly` → lines 178-179
10. `test_read_resource_handler_with_invalid_uri` → lines 192-197
11. `test_server_run_method_starts_stdio` → lines 235-236

### Priority 2: Model Properties (8 lines)

**Coverage Gap**: 
- document.py lines 55-57, 64
- navigation.py lines 25, 29, 75, 80

**Test Cases**:
1. `test_document_excerpt_strips_frontmatter` → lines 55-57
2. `test_document_excerpt_truncates_with_ellipsis` → line 64
3. `test_category_breadcrumbs_empty_path` → line 25
4. `test_category_breadcrumbs_without_docs_prefix` → line 29
5. `test_navigation_context_can_navigate_up_false` → line 75
6. `test_navigation_context_can_navigate_down_true` → line 80

### Priority 3: Service Error Paths (13 lines)

**Coverage Gap**:
- cache.py line 174
- hierarchy.py line 290
- markdown.py lines 219-221, 260-261
- search.py lines 234-236, 253-255

**Test Cases**:
1. `test_cache_evict_oldest_empty_cache` → line 174
2. `test_get_navigation_context_empty_breadcrumbs` → line 290
3. `test_extract_excerpt_exception_handling` → lines 219-221 (markdown)
4. `test_highlight_matches_exception_handling` → lines 260-261 (markdown)
5. `test_extract_excerpt_exception_handling` → lines 234-236 (search)
6. `test_highlight_matches_exception_handling` → lines 253-255 (search)

### Priority 4: Entry Point (1 line)

**Coverage Gap**: __main__.py line 41

**Test Cases**:
1. `test_main_exception_handling_exits_with_code_1` → line 41

## Test Execution Flow

### Per Test Case

1. **Setup Phase**:
   - Load fixtures (documents, categories, configs)
   - Initialize mocks (AsyncMock for async functions)
   - Set up patches (for external dependencies)

2. **Execution Phase**:
   - Call function/method under test
   - Trigger specific code path (positive/negative/edge case)

3. **Assertion Phase**:
   - Verify return values match expectations
   - Check mock calls (assert_called_once, assert_called_with)
   - Validate state changes if applicable

4. **Teardown Phase**:
   - Automatic via pytest fixtures
   - Clean up temp files/resources
   - Reset mocks

### Coverage Verification Flow

1. Run tests: `pytest --cov=hierarchical_docs_mcp`
2. Generate report: `--cov-report=html --cov-report=term`
3. Review htmlcov/index.html for visual gaps
4. Iterate: Add tests for remaining gaps
5. Verify: Confirm 100% coverage and zero warnings

## Success Criteria Mapping

| Success Criterion | Data Model Element | Verification Method |
|------------------|-------------------|---------------------|
| SC-001: 100% coverage | Coverage Metric | pytest-cov report shows 100% |
| SC-002: 48 lines covered | Coverage Gap → Test Case mapping | All gaps have corresponding tests |
| SC-003: Server 64%→100% | Coverage Metric (server.py) | Module-specific coverage = 100% |
| SC-004: < 6 seconds | Test Case.execution_time | Total test time < 6s |
| SC-005: Zero failures/warnings | Test Case assertions | pytest exit code = 0, no warnings |
| SC-006: Follow patterns | Test Case structure | Code review confirms pattern consistency |
| SC-007: Meaningful tests | Test Case assertions | Tests verify behavior, not just coverage |
| SC-008: Documentation | Test Case comments | Docstrings explain non-obvious test scenarios |

## Anti-Patterns to Avoid

### Coverage Inflation
❌ **Bad**: Tests that execute code but don't assert behavior
```python
def test_function():
    result = function()  # Just calling it for coverage
```

✅ **Good**: Tests that verify expected behavior
```python
def test_function_returns_expected_value():
    result = function(input_data)
    assert result == expected_value
    assert isinstance(result, ExpectedType)
```

### Test Interdependence
❌ **Bad**: Tests that rely on execution order
```python
def test_step_1():
    global state
    state = setup()

def test_step_2():
    result = use(state)  # Depends on test_step_1
```

✅ **Good**: Independent tests with fixtures
```python
@pytest.fixture
def state():
    return setup()

def test_step_2(state):
    result = use(state)
```

### Over-Mocking
❌ **Bad**: Mocking everything, testing nothing
```python
def test_function(mocker):
    mocker.patch('module.everything')
    result = function()  # Not testing real behavior
```

✅ **Good**: Mock only external dependencies
```python
def test_function(mocker):
    mocker.patch('module.external_api')  # Mock external only
    result = function()  # Test real internal logic
    assert result.processed_correctly
```

## Summary

This data model describes the test coverage improvement work in terms of:
- **Coverage Gaps**: What needs testing (48 lines across 8 modules)
- **Test Cases**: How to test it (~20 new tests following existing patterns)
- **Fixtures**: Reusable test data (documents, categories, configs)
- **Metrics**: How to measure success (100% coverage, <6s execution)

The model emphasizes:
- Following existing pytest patterns
- Independent, meaningful tests
- Proper mocking of async operations
- Verification of behavior, not just coverage numbers
