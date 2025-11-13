# Research: Complete Unit Test Coverage

**Feature**: 002-test-coverage  
**Date**: 2025-11-13  
**Status**: Complete

## Overview

This document consolidates research findings for achieving 100% unit test coverage in the hierarchical_docs_mcp package. The project currently has 94.90% coverage with 48 uncovered lines across multiple modules.

## Research Tasks

### 1. Testing Async MCP Server Handlers

**Question**: How to properly test async MCP server handlers (list_tools, call_tool, list_resources, read_resource)?

**Decision**: Use pytest-asyncio with AsyncMock for mocking async server components

**Rationale**:
- Existing tests already use `@pytest.mark.asyncio` decorator successfully
- `unittest.mock.AsyncMock` properly handles async function mocking
- MCP Server class provides testable handler registration mechanism
- Can test handlers by directly invoking registered functions without full server lifecycle

**Implementation Approach**:
1. Access registered handlers via server instance after initialization
2. Use AsyncMock to mock dependencies (documents, categories)
3. Test handler functions directly with various input scenarios
4. Verify return values match expected schema format

**Alternatives Considered**:
- Full integration testing with stdio_server: Rejected - too complex for unit tests, already covered in integration tests
- Mocking entire Server class: Rejected - want to test actual handler registration, not just mocks
- Synchronous wrappers: Rejected - would not test actual async behavior

### 2. Testing Server run() Method with stdio_server

**Question**: How to test the DocumentationMCPServer.run() method which uses stdio_server context manager?

**Decision**: Mock stdio_server to return test streams and verify server.run() is called with correct parameters

**Rationale**:
- The run() method primarily orchestrates server startup
- Core logic is in handler registration (tested separately)
- Full stdio testing belongs in integration tests
- Unit test should verify correct server initialization and parameter passing

**Implementation Approach**:
1. Patch `hierarchical_docs_mcp.server.stdio_server` 
2. Mock async context manager to yield test read/write streams
3. Mock server.run() to verify it's called with correct streams
4. Verify initialization options are created properly

**Alternatives Considered**:
- Real stdio testing: Rejected - requires process spawning, too slow for unit tests
- Skip testing run(): Rejected - leaves gap in coverage and misses potential bugs
- Test only initialization_options: Rejected - doesn't verify full run() path

### 3. Testing Model Computed Properties

**Question**: What edge cases need coverage for Document.excerpt() and NavigationContext properties?

**Decision**: Test property accessors with boundary conditions and None/empty values

**Rationale**:
- Computed properties have logic that can fail silently
- Edge cases (empty content, missing parents, etc.) are common in real usage
- Property getters should be defensive against unexpected input
- Missing coverage is in rarely-hit branches (empty paths, edge conditions)

**Test Cases Identified**:
1. **Document.excerpt()**: 
   - Content with frontmatter (lines 55-57)
   - Content requiring ellipsis truncation (line 64)
   - Empty or None content
   - Content shorter than max_length
2. **Category.breadcrumbs**:
   - Empty URI path (line 25)
   - URI without "docs://" prefix (line 29)
3. **NavigationContext navigation properties**:
   - can_navigate_up with None parent_uri (line 75)
   - can_navigate_down with empty children (line 80)

**Alternatives Considered**:
- Skip edge cases: Rejected - these branches exist for a reason, need verification
- Test only happy paths: Rejected - doesn't achieve coverage goal
- Remove unused code: Rejected - code serves defensive purposes

### 4. Testing Service Error Paths

**Question**: How to trigger error paths in cache, hierarchy, markdown, and search services?

**Decision**: Use mocking to inject exceptions and verify error handling behavior

**Rationale**:
- Error paths are defensive code that's hard to trigger naturally
- Mocking allows controlled exception injection
- Error handling should be verified (logging, fallback behavior, exception propagation)
- Missing lines are in try-except blocks and error handlers

**Test Cases by Service**:
1. **cache.py (line 174)**: Test _evict_oldest() with empty cache
2. **hierarchy.py (line 290)**: Test get_navigation_context() with empty breadcrumbs
3. **markdown.py (lines 219-221, 260-261)**: Test _extract_excerpt() and _highlight_matches() with exceptions
4. **search.py (lines 234-236, 253-255)**: Test _extract_excerpt() and _highlight_matches() with malformed input

**Alternatives Considered**:
- Integration tests only: Rejected - error paths need explicit unit test verification
- Remove error handling: Rejected - defensive code is good practice
- Mock less, use real failures: Rejected - would require complex setup and be fragile

### 5. Testing CLI Entry Point Exception Handling

**Question**: How to test the main() function's exception handler in __main__.py?

**Decision**: Mock serve() function to raise exception and verify sys.exit(1) is called

**Rationale**:
- Entry point exception handling ensures graceful failure messaging
- Line 41 (sys.exit(1)) is in the except Exception block
- Need to verify exit code and error output

**Implementation Approach**:
1. Patch `hierarchical_docs_mcp.__main__.serve` to raise exception
2. Mock `sys.exit` to capture exit code
3. Verify error message printed to stderr
4. Confirm exit(1) called for general exceptions

**Alternatives Considered**:
- Test with real failures: Rejected - requires actual configuration errors, fragile
- Skip testing: Rejected - leaves gap in coverage
- Integration test only: Rejected - unit test is simpler and faster

## Testing Patterns & Best Practices

### Existing Patterns to Follow

Based on analysis of `tests/unit/test_server.py` and `tests/unit/test_handlers_tools.py`:

1. **Fixture Usage**:
   ```python
   @pytest.fixture
   def sample_documents(self):
       return [Document(...), ...]
   ```

2. **Async Test Pattern**:
   ```python
   @pytest.mark.asyncio
   async def test_async_function(self, fixture):
       result = await async_function(fixture)
       assert result == expected
   ```

3. **Mocking with Patch**:
   ```python
   with patch("module.function") as mock_func:
       mock_func.return_value = test_value
       # test code
   ```

4. **Class Organization**:
   ```python
   class TestComponentName:
       """Test ComponentName functionality."""
       
       def test_specific_behavior(self):
           # test implementation
   ```

### Performance Considerations

- Current test suite: 464 tests in 4.47 seconds
- Target: Under 6 seconds total
- Adding ~15-20 new tests
- Each test should complete in < 50ms average
- Use mocking to avoid I/O operations
- Share fixtures where possible

### Test Isolation

- Each test must be independently runnable
- Use pytest fixtures for setup/teardown
- Mock external dependencies (filesystem, network)
- Don't rely on test execution order
- Clean up temp files/state in fixtures

## Dependencies

### Already Available
- pytest 7.4+
- pytest-asyncio 0.21+
- pytest-mock 3.11+
- pytest-cov 4.1+
- unittest.mock (standard library)

### No New Dependencies Required
All testing needs can be met with existing tooling.

## Risk Assessment

### Low Risk Areas
- Model property tests (simple, isolated)
- Service error path tests (well-contained)
- Entry point exception test (single function)

### Medium Risk Areas
- Server handler tests (requires understanding MCP Server internals)
- Async mocking (can be tricky with context managers)

### Mitigation Strategies
1. Reference existing test patterns closely
2. Test handlers incrementally (one at a time)
3. Use explicit AsyncMock configuration
4. Verify tests actually increase coverage after each addition
5. Run full suite after each change to catch regressions

## Coverage Verification Strategy

After implementing tests:

1. Run pytest with coverage:
   ```bash
   pytest --cov=hierarchical_docs_mcp --cov-report=html --cov-report=term
   ```

2. Verify each module reaches 100%:
   - server.py: 64% → 100%
   - models/document.py: 90% → 100%
   - models/navigation.py: 92% → 100%
   - services/cache.py: 99% → 100%
   - services/hierarchy.py: 99% → 100%
   - services/markdown.py: 95% → 100%
   - services/search.py: 94% → 100%
   - __main__.py: 95% → 100%

3. Check htmlcov/index.html for visual confirmation

4. Verify no test warnings in output

## Summary

All research tasks completed. Clear path forward to achieve 100% coverage:
- Use existing pytest/AsyncMock patterns
- Focus on server handlers first (biggest impact)
- Add edge case tests for model properties
- Mock exceptions for service error paths
- Test CLI exception handling last

No blockers identified. All necessary tools and patterns already in place.
