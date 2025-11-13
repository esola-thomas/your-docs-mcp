# Test Coverage Analysis

**Date**: 2025-11-13  
**Current Coverage**: 94.90% (942 statements, 48 missing)  
**Target**: 100%

## Coverage by Module

### Critical Priority (P1) - Server Module
**File**: `hierarchical_docs_mcp/server.py`  
**Coverage**: 64% (73 statements, 26 missing)  
**Missing Lines**: 42, 144-173, 178-179, 192-197, 235-236

#### Uncovered Areas:
1. **Lines 144-173**: Handler functions (list_tools, call_tool)
2. **Lines 178-179**: Handler functions (list_resources, read_resource)
3. **Lines 192-197**: Error handling in read_resource
4. **Lines 235-236**: Logging in run() method
5. **Line 42**: Part of list_tools handler

### High Priority (P2) - Models

#### Document Model
**File**: `hierarchical_docs_mcp/models/document.py`  
**Coverage**: 90% (39 statements, 4 missing)  
**Missing Lines**: 55-57, 64

**Uncovered Areas**:
- Lines 55-57: Content extraction logic in excerpt() method
- Line 64: Ellipsis logic in excerpt() method

#### Navigation Model
**File**: `hierarchical_docs_mcp/models/navigation.py`  
**Coverage**: 92% (50 statements, 4 missing)  
**Missing Lines**: 25, 29, 75, 80

**Uncovered Areas**:
- Line 25: Empty path handling in breadcrumbs property
- Line 29: Breadcrumb list comprehension
- Line 75: can_navigate_up property getter
- Line 80: can_navigate_down property getter

### Medium Priority (P3) - Services

#### Cache Service
**File**: `hierarchical_docs_mcp/services/cache.py`  
**Coverage**: 99% (100 statements, 1 missing)  
**Missing Lines**: 174

**Uncovered Areas**:
- Line 174: Return statement in _evict_oldest() when cache is empty

#### Hierarchy Service
**File**: `hierarchical_docs_mcp/services/hierarchy.py`  
**Coverage**: 99% (116 statements, 1 missing)  
**Missing Lines**: 290

**Uncovered Areas**:
- Line 290: Breadcrumbs assignment in get_navigation_context()

#### Markdown Service
**File**: `hierarchical_docs_mcp/services/markdown.py`  
**Coverage**: 95% (107 statements, 5 missing)  
**Missing Lines**: 219-221, 260-261

**Uncovered Areas**:
- Lines 219-221: Error handling in _extract_excerpt()
- Lines 260-261: Error handling in _highlight_matches()

#### Search Service
**File**: `hierarchical_docs_mcp/services/search.py`  
**Coverage**: 94% (103 statements, 6 missing)  
**Missing Lines**: 234-236, 253-255

**Uncovered Areas**:
- Lines 234-236: Error path in _extract_excerpt()
- Lines 253-255: Error path in _highlight_matches()

### Low Priority (P4) - Entry Point

#### Main Entry Point
**File**: `hierarchical_docs_mcp/__main__.py`  
**Coverage**: 95% (22 statements, 1 missing)  
**Missing Lines**: 41

**Uncovered Areas**:
- Line 41: sys.exit(1) in exception handler

## Test Strategy

### P1: Server Module (26 lines)
**Impact**: HIGH - Core server functionality  
**Effort**: HIGH - Requires async mocking and handler testing  
**Tests Needed**:
1. Test list_tools() handler returns all tools
2. Test call_tool() with each tool type
3. Test call_tool() with unknown tool (error path)
4. Test list_resources() handler
5. Test read_resource() with valid URI
6. Test read_resource() with invalid URI (error path)
7. Test run() method initialization

### P2: Models (8 lines)
**Impact**: MEDIUM - Data consistency  
**Effort**: LOW - Simple property tests  
**Tests Needed**:
1. Test Document.excerpt() with frontmatter
2. Test Document.excerpt() with long content
3. Test Category.breadcrumbs with empty path
4. Test NavigationContext.can_navigate_up/down properties

### P3: Services (13 lines)
**Impact**: LOW - Error paths and edge cases  
**Effort**: LOW - Targeted exception tests  
**Tests Needed**:
1. Test cache _evict_oldest() with empty cache
2. Test hierarchy breadcrumbs logic for edge cases
3. Test markdown error paths in excerpt and highlight
4. Test search error paths in excerpt and highlight

### P4: Entry Point (1 line)
**Impact**: LOW - CLI error handling  
**Effort**: LOW - Single exception test  
**Tests Needed**:
1. Test main() exception handling

## Testing Patterns to Follow

Based on existing tests in `tests/unit/`:

1. **Fixtures**: Use pytest fixtures for sample data
2. **Async Testing**: Use `@pytest.mark.asyncio` for async functions
3. **Mocking**: Use `unittest.mock.patch` and `AsyncMock`
4. **Assertions**: Test both positive and negative cases
5. **Organization**: Group related tests in classes

## Success Metrics

- [ ] All 48 missing lines covered
- [ ] Server module reaches 100% (from 64%)
- [ ] Total coverage reaches 100% (from 94.90%)
- [ ] All tests pass without warnings
- [ ] Test execution time stays under 6 seconds

## Implementation Order

1. **Phase 1**: Server handlers (P1) - Biggest impact
2. **Phase 2**: Model properties (P2) - Quick wins
3. **Phase 3**: Service error paths (P3) - Edge cases
4. **Phase 4**: Entry point (P4) - Final cleanup
