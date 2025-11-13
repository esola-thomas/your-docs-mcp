# Tasks: Complete Unit Test Coverage

**Feature**: 002-test-coverage  
**Branch**: `002-test-coverage`  
**Input**: Design documents from `/specs/002-test-coverage/`  
**Prerequisites**: spec.md (user stories), research.md (testing strategies), data-model.md (test entities), contracts/test-requirements.md (test contracts), coverage-analysis.md (gap details)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Test files: `tests/unit/` at repository root
- Production code: `hierarchical_docs_mcp/` (no modifications needed)
- This feature only modifies test files

---

## Phase 1: Setup & Verification

**Purpose**: Verify baseline and prepare for test implementation

- [ ] T001 Verify current coverage baseline with pytest --cov=hierarchical_docs_mcp --cov-report=html
- [ ] T002 Review existing test patterns in tests/unit/test_server.py and tests/unit/test_handlers_tools.py
- [ ] T003 [P] Confirm pytest-asyncio, pytest-mock, and unittest.mock are available
- [ ] T004 [P] Review coverage-analysis.md to understand all 48 uncovered lines

**Checkpoint**: Baseline confirmed (94.90%), patterns understood, ready to implement tests

---

## Phase 2: User Story 1 - Server Lifecycle Coverage (Priority: P1) 🎯 MVP

**Goal**: Achieve 100% coverage for server.py (64% → 100%, 26 lines)

**Independent Test**: Server handler tests can be run independently with `pytest tests/unit/test_server.py --cov=hierarchical_docs_mcp/server.py`

**Impact**: HIGH - Core server functionality with lowest current coverage

### Implementation for User Story 1

- [ ] T005 [P] [US1] Add test for list_tools handler returns all 5 tools in tests/unit/test_server.py
- [ ] T006 [P] [US1] Add test for list_tools handler verifies tool schemas in tests/unit/test_server.py
- [ ] T007 [P] [US1] Add test for call_tool with search_documentation in tests/unit/test_server.py
- [ ] T008 [P] [US1] Add test for call_tool with navigate_to in tests/unit/test_server.py
- [ ] T009 [P] [US1] Add test for call_tool with get_table_of_contents in tests/unit/test_server.py
- [ ] T010 [P] [US1] Add test for call_tool with search_by_tags in tests/unit/test_server.py
- [ ] T011 [P] [US1] Add test for call_tool with get_document in tests/unit/test_server.py
- [ ] T012 [P] [US1] Add test for call_tool with unknown tool raises ValueError in tests/unit/test_server.py
- [ ] T013 [P] [US1] Add test for list_resources handler formats resources correctly in tests/unit/test_server.py
- [ ] T014 [P] [US1] Add test for read_resource with invalid URI raises ValueError in tests/unit/test_server.py
- [ ] T015 [US1] Add test for server run() method with mocked stdio_server in tests/unit/test_server.py
- [ ] T016 [US1] Verify server.py coverage reaches 100% with pytest --cov=hierarchical_docs_mcp/server.py

**Lines Covered**: 42, 144-173, 178-179, 192-197, 235-236 (26 lines total)

**Checkpoint**: Server module at 100% coverage - core functionality fully tested

---

## Phase 3: User Story 2 - Model Property and Method Coverage (Priority: P2)

**Goal**: Achieve 100% coverage for Document and NavigationContext models (8 lines)

**Independent Test**: Model tests can be run independently with `pytest tests/unit/test_document.py tests/unit/test_navigation.py --cov=hierarchical_docs_mcp/models`

**Impact**: MEDIUM - Data consistency and computed properties

### Implementation for User Story 2

- [ ] T017 [P] [US2] Create or update tests/unit/test_document.py with test for excerpt() strips frontmatter
- [ ] T018 [P] [US2] Add test for excerpt() truncates long content at word boundary in tests/unit/test_document.py
- [ ] T019 [P] [US2] Add test for excerpt() handles empty content in tests/unit/test_document.py
- [ ] T020 [P] [US2] Add test for excerpt() returns short content as-is in tests/unit/test_document.py
- [ ] T021 [P] [US2] Create tests/unit/test_navigation.py if it doesn't exist
- [ ] T022 [P] [US2] Add test for Category.breadcrumbs with empty path in tests/unit/test_navigation.py
- [ ] T023 [P] [US2] Add test for Category.breadcrumbs without docs:// prefix in tests/unit/test_navigation.py
- [ ] T024 [P] [US2] Add test for NavigationContext.can_navigate_up returns False without parent in tests/unit/test_navigation.py
- [ ] T025 [P] [US2] Add test for NavigationContext.can_navigate_down returns True with children in tests/unit/test_navigation.py
- [ ] T026 [P] [US2] Add test for Category.is_root returns True at depth 0 in tests/unit/test_navigation.py
- [ ] T027 [US2] Verify models coverage reaches 100% with pytest --cov=hierarchical_docs_mcp/models

**Lines Covered**: document.py (55-57, 64), navigation.py (25, 29, 75, 80) - 8 lines total

**Checkpoint**: Model properties at 100% coverage - data transformations fully tested

---

## Phase 4: User Story 3 - Service Error Path Coverage (Priority: P3)

**Goal**: Achieve 100% coverage for service error handling paths (13 lines)

**Independent Test**: Service tests can be run independently with `pytest tests/unit/test_cache.py tests/unit/test_hierarchy.py tests/unit/test_markdown.py tests/unit/test_search.py --cov=hierarchical_docs_mcp/services`

**Impact**: LOW - Edge cases and error paths

### Implementation for User Story 3

- [ ] T028 [P] [US3] Add test for DocumentCache._evict_oldest() with empty cache in tests/unit/test_cache.py
- [ ] T029 [P] [US3] Add test for get_navigation_context() with empty breadcrumbs in tests/unit/test_hierarchy.py
- [ ] T030 [P] [US3] Add test for _extract_excerpt() exception handling in tests/unit/test_markdown.py
- [ ] T031 [P] [US3] Add test for _highlight_matches() exception handling in tests/unit/test_markdown.py
- [ ] T032 [P] [US3] Add test for _extract_excerpt() with malformed pattern in tests/unit/test_search.py
- [ ] T033 [P] [US3] Add test for _highlight_matches() with invalid query in tests/unit/test_search.py
- [ ] T034 [US3] Verify services coverage reaches 100% with pytest --cov=hierarchical_docs_mcp/services

**Lines Covered**: cache.py (174), hierarchy.py (290), markdown.py (219-221, 260-261), search.py (234-236, 253-255) - 13 lines total

**Checkpoint**: Service error paths at 100% coverage - robust error handling verified

---

## Phase 5: User Story 4 - Entry Point Coverage (Priority: P4)

**Goal**: Achieve 100% coverage for CLI entry point (1 line)

**Independent Test**: Entry point test can be run independently with `pytest tests/unit/test_main.py --cov=hierarchical_docs_mcp/__main__.py`

**Impact**: LOW - Single exception handling path

### Implementation for User Story 4

- [ ] T035 [US4] Add test for main() exception handling with mocked serve() in tests/unit/test_main.py
- [ ] T036 [US4] Verify main() test calls sys.exit(1) on exception in tests/unit/test_main.py
- [ ] T037 [US4] Verify __main__.py coverage reaches 100% with pytest --cov=hierarchical_docs_mcp/__main__.py

**Lines Covered**: __main__.py (41) - 1 line total

**Checkpoint**: Entry point at 100% coverage - complete test coverage achieved

---

## Phase 6: Validation & Documentation

**Purpose**: Verify all success criteria met and document results

- [ ] T038 Run complete test suite with pytest --cov=hierarchical_docs_mcp --cov-report=html --cov-report=term -v
- [ ] T039 Verify total coverage is 100% (from 94.90%)
- [ ] T040 Verify all 48 previously uncovered lines are now covered
- [ ] T041 Verify test execution time is under 6 seconds
- [ ] T042 Verify zero test failures in pytest output
- [ ] T043 Verify zero warnings in pytest output
- [ ] T044 [P] Review htmlcov/index.html to confirm all modules at 100%
- [ ] T045 [P] Document any testing patterns used in tests that differ from existing conventions
- [ ] T046 [P] Update quickstart.md if any steps differ from actual implementation

**Checkpoint**: 100% coverage achieved, all success criteria met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **User Story 1 (Phase 2)**: Depends on Setup - Can start once baseline verified
- **User Story 2 (Phase 3)**: Depends on Setup - **INDEPENDENT** of User Story 1
- **User Story 3 (Phase 4)**: Depends on Setup - **INDEPENDENT** of User Stories 1 & 2
- **User Story 4 (Phase 5)**: Depends on Setup - **INDEPENDENT** of all other stories
- **Validation (Phase 6)**: Depends on completion of desired user stories

### User Story Independence

All user stories (US1-US4) are **completely independent**:
- ✅ Can be implemented in any order
- ✅ Can be implemented in parallel by different developers
- ✅ Each story tests different modules with no overlap
- ✅ Each story can be verified independently

**Recommended order** (by impact):
1. User Story 1 (P1) - Server handlers (26 lines, highest impact)
2. User Story 2 (P2) - Model properties (8 lines, medium impact)
3. User Story 3 (P3) - Service error paths (13 lines, edge cases)
4. User Story 4 (P4) - Entry point (1 line, lowest impact)

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003 and T004 can run in parallel

**Phase 2 (User Story 1)**:
- T005-T014 can all run in parallel (different test functions in same file)
- T016 verification runs after all tests added

**Phase 3 (User Story 2)**:
- T017-T020 can run in parallel (Document tests)
- T022-T026 can run in parallel (Navigation tests)
- T021 may need to run before T022-T026 if file doesn't exist

**Phase 4 (User Story 3)**:
- T028-T033 can all run in parallel (different test files)

**Phase 5 (User Story 4)**:
- Single file, T035-T036 sequential

**Phase 6 (Validation)**:
- T044-T046 can run in parallel after main verification complete

### Cross-Story Parallelization

**Maximum parallelization** (if 4 developers available):
```bash
# All stories can proceed simultaneously after Setup
Developer 1: Phase 2 (US1) - Server tests
Developer 2: Phase 3 (US2) - Model tests  
Developer 3: Phase 4 (US3) - Service tests
Developer 4: Phase 5 (US4) - Entry point test

# Each completes independently, no blocking
```

**Sequential approach** (single developer):
```bash
# Follow priority order for maximum value delivery
1. Setup → 2. US1 (P1) → 3. US2 (P2) → 4. US3 (P3) → 5. US4 (P4) → 6. Validation

# Can stop after any story and still have improved coverage
```

---

## Parallel Example: User Story 1 (Server Tests)

If multiple developers work on User Story 1:

```bash
# Developer A: Handler return value tests
pytest -k "test_list_tools or test_list_resources" --cov=hierarchical_docs_mcp/server.py

# Developer B: call_tool positive tests  
pytest -k "test_call_tool" --cov=hierarchical_docs_mcp/server.py

# Developer C: Error path tests
pytest -k "unknown_tool or invalid_uri" --cov=hierarchical_docs_mcp/server.py

# Developer D: run() method test
pytest -k "test_server_run" --cov=hierarchical_docs_mcp/server.py

# All merge to tests/unit/test_server.py when complete
```

---

## Implementation Strategy

### MVP (Minimum Viable Product)

**Scope**: User Story 1 only (Server Lifecycle Coverage)

**Rationale**:
- Provides biggest coverage improvement (26 lines)
- Tests most critical code (server handlers)
- Improves coverage from 94.90% to ~97.2%
- Demonstrates testing approach for remaining stories

**Time**: ~1 hour (Phase 1 + Phase 2)

**Deliverable**: Server module at 100% coverage

### Incremental Delivery

After MVP, stories can be delivered incrementally:

1. **MVP Delivery**: US1 complete → 97.2% coverage
2. **Second Increment**: US1 + US2 → 98.1% coverage  
3. **Third Increment**: US1 + US2 + US3 → 99.4% coverage
4. **Final Increment**: All stories → 100% coverage

Each increment is:
- Independently testable
- Independently valuable
- Independently deployable
- Reduces risk incrementally

---

## Task Summary

**Total Tasks**: 46
- Setup: 4 tasks
- User Story 1 (P1): 12 tasks (26 lines covered)
- User Story 2 (P2): 11 tasks (8 lines covered)
- User Story 3 (P3): 7 tasks (13 lines covered)
- User Story 4 (P4): 3 tasks (1 line covered)
- Validation: 9 tasks

**Parallelization**:
- 35 tasks marked [P] can run in parallel within their phase
- All 4 user stories can run in parallel (independent)
- Maximum parallel efficiency with 4+ developers

**Independent Test Verification**:
- Each user story has specific coverage verification task
- Each story can be tested with targeted pytest commands
- No story depends on another story's completion

**Success Criteria**:
- ✅ 100% line coverage (from 94.90%)
- ✅ All 48 lines covered
- ✅ Test execution < 6 seconds
- ✅ Zero failures, zero warnings
- ✅ All tests follow existing patterns

**Suggested MVP**: User Story 1 only (Tasks T001-T016)
- Time: ~1 hour
- Coverage: 94.90% → 97.2%
- Value: Core server functionality fully tested
