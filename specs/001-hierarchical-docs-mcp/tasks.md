# Tasks: Hierarchical Documentation MCP Server

**Input**: Design documents from `/specs/001-hierarchical-docs-mcp/`  
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/ (complete)

**Tests**: This project follows TDD per constitution - tests are written first and must fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to repository root:
- Source code: `hierarchical_docs_mcp/`
- Tests: `tests/`
- Documentation: `docs/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in hierarchical_docs_mcp/
- [ ] T002 Initialize Python project with pyproject.toml including dependencies (mcp, pyyaml, pydantic, pydantic-settings, openapi-spec-validator, prance, watchdog, pytest, pytest-asyncio, pytest-mock)
- [ ] T003 [P] Create hierarchical_docs_mcp/__init__.py with package version and exports
- [ ] T004 [P] Create empty module __init__.py files in hierarchical_docs_mcp/models/, hierarchical_docs_mcp/handlers/, hierarchical_docs_mcp/services/, hierarchical_docs_mcp/security/, hierarchical_docs_mcp/utils/
- [ ] T005 [P] Create test directory structure with tests/contract/, tests/integration/, tests/unit/
- [ ] T006 [P] Create sample documentation structure in docs/guides/ and docs/api/
- [ ] T007 [P] Create docs/guides/getting-started.md with YAML frontmatter for testing
- [ ] T008 [P] Create docs/api/openapi.yaml with sample OpenAPI 3.0 spec for testing
- [ ] T009 [P] Create .env.example with configuration template (DOCS_ROOT, MCP_DOCS_CACHE_TTL, etc.)
- [ ] T010 [P] Create README.md with quickstart instructions
- [ ] T011 [P] Configure pytest.ini with asyncio settings and test paths

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T012 Create hierarchical_docs_mcp/utils/logger.py with structured logging setup (supports audit trail)
- [ ] T013 Create hierarchical_docs_mcp/config.py with pydantic-settings configuration classes (ServerConfig, SourceConfig)
- [ ] T014 Create hierarchical_docs_mcp/security/path_validator.py with validate_path() function preventing directory traversal
- [ ] T015 Create hierarchical_docs_mcp/security/sanitizer.py with sanitize_query() and sanitize_openapi_description() functions
- [ ] T016 Write tests/unit/test_path_validator.py with security attack patterns (../../etc/passwd, hidden files, etc.)
- [ ] T017 Write tests/unit/test_sanitizer.py with injection pattern tests
- [ ] T018 Implement path validation logic in hierarchical_docs_mcp/security/path_validator.py to pass security tests
- [ ] T019 Implement sanitization logic in hierarchical_docs_mcp/security/sanitizer.py to pass injection tests
- [ ] T020 Create hierarchical_docs_mcp/models/document.py with DocumentationSource and Document pydantic models
- [ ] T021 Create hierarchical_docs_mcp/models/navigation.py with Category, NavigationContext, SearchResult pydantic models
- [ ] T022 Create hierarchical_docs_mcp/models/openapi.py with OpenAPISpecification and APIOperation pydantic models
- [ ] T023 Create hierarchical_docs_mcp/services/cache.py with CacheEntry model and TTL-based caching logic
- [ ] T024 Write tests/unit/test_cache.py for cache hit/miss, TTL expiration, and invalidation
- [ ] T025 Implement caching functionality in hierarchical_docs_mcp/services/cache.py to pass cache tests
- [ ] T026 Create hierarchical_docs_mcp/server.py with MCP Server initialization and capability declaration
- [ ] T027 Create hierarchical_docs_mcp/__main__.py with CLI entry point for stdio transport

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - AI-Assisted Documentation Navigation (Priority: P1) 🎯 MVP

**Goal**: Enable AI assistants to navigate hierarchical markdown documentation with breadcrumb context

**Independent Test**: Configure local docs directory, connect AI assistant to MCP server, ask "List all available guides" and "Show me the getting started guide"

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T028 [P] [US1] Write tests/contract/test_mcp_tools.py with test cases for list_tools() response format (must declare search_documentation, navigate_to, get_table_of_contents tools)
- [ ] T029 [P] [US1] Write tests/contract/test_mcp_resources.py with test cases for list_resources() response format (must declare docs:// URI patterns)
- [ ] T030 [P] [US1] Write tests/integration/test_markdown_navigation.py with end-to-end test: load docs, navigate hierarchy, verify breadcrumbs
- [ ] T031 [P] [US1] Write tests/unit/test_markdown.py with test cases for YAML frontmatter parsing (valid, invalid, missing cases)
- [ ] T032 [P] [US1] Write tests/unit/test_hierarchy.py with test cases for tree building, breadcrumb generation, parent/child relationships

### Implementation for User Story 1

- [ ] T033 [P] [US1] Implement hierarchical_docs_mcp/services/markdown.py with parse_markdown_with_metadata() function using pyyaml
- [ ] T034 [P] [US1] Implement hierarchical_docs_mcp/services/hierarchy.py with build_category_tree(), get_breadcrumbs(), and navigate_to_uri() functions
- [ ] T035 [US1] Implement hierarchical_docs_mcp/services/search.py with basic regex-based search_content() function (full-text search with caching)
- [ ] T036 [US1] Implement hierarchical_docs_mcp/handlers/tools.py with search_documentation(), navigate_to(), and get_table_of_contents() tool handlers
- [ ] T037 [US1] Implement hierarchical_docs_mcp/handlers/resources.py with resource handlers for docs:// URI patterns (root, category, section, document)
- [ ] T038 [US1] Integrate file watching in hierarchical_docs_mcp/services/cache.py using watchdog library for auto-invalidation
- [ ] T039 [US1] Register tool and resource handlers in hierarchical_docs_mcp/server.py with MCP Server instance
- [ ] T040 [US1] Add configuration loading logic in hierarchical_docs_mcp/__main__.py to read DOCS_ROOT and initialize server
- [ ] T041 [US1] Verify all User Story 1 tests pass (T028-T032)

**Checkpoint**: At this point, User Story 1 should be fully functional - AI assistants can navigate markdown documentation hierarchically

---

## Phase 4: User Story 2 - API Documentation Discovery from OpenAPI Specs (Priority: P1)

**Goal**: Enable AI assistants to query OpenAPI specifications and discover API endpoints with full details

**Independent Test**: Provide OpenAPI spec file, configure MCP to load it, ask AI "What endpoints are available for users?" and "How do I create a new user?"

### Tests for User Story 2

- [ ] T042 [P] [US2] Write tests/unit/test_openapi_loader.py with test cases for OpenAPI parsing (valid 3.0/3.1 specs, invalid specs, $ref resolution, schema extraction)
- [ ] T043 [P] [US2] Write tests/integration/test_openapi_navigation.py with end-to-end test: load OpenAPI spec, list operations by tag, get endpoint details
- [ ] T044 [P] [US2] Add test cases to tests/contract/test_mcp_tools.py for list_api_endpoints(), get_endpoint_docs(), and get_schema_definition() tools
- [ ] T045 [P] [US2] Add test cases to tests/contract/test_mcp_resources.py for api:// URI patterns (api://{tag}, api://{tag}/{operation_id})

### Implementation for User Story 2

- [ ] T046 [P] [US2] Implement hierarchical_docs_mcp/services/openapi_loader.py with load_openapi_spec() function using openapi-spec-validator and prance
- [ ] T047 [P] [US2] Implement resolve_openapi_references() in hierarchical_docs_mcp/services/openapi_loader.py using prance ResolvingParser
- [ ] T048 [P] [US2] Implement extract_operations_by_tag() and extract_schema_definitions() in hierarchical_docs_mcp/services/openapi_loader.py
- [ ] T049 [US2] Add list_api_endpoints(), get_endpoint_docs(), and get_schema_definition() tool handlers to hierarchical_docs_mcp/handlers/tools.py
- [ ] T050 [US2] Add resource handlers for api:// URI patterns to hierarchical_docs_mcp/handlers/resources.py
- [ ] T051 [US2] Integrate OpenAPI sanitization in hierarchical_docs_mcp/security/sanitizer.py (check for prompt injection in descriptions)
- [ ] T052 [US2] Add OpenAPI spec loading to hierarchical_docs_mcp/config.py (MCP_DOCS_OPENAPI_SPECS environment variable)
- [ ] T053 [US2] Register OpenAPI tools and resources in hierarchical_docs_mcp/server.py
- [ ] T054 [US2] Verify all User Story 2 tests pass (T042-T045)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - markdown navigation AND OpenAPI discovery

---

## Phase 5: User Story 5 - Secure Documentation Access with Path Validation (Priority: P2)

**Goal**: Ensure all file system access is secure with comprehensive validation preventing attacks

**Independent Test**: Attempt directory traversal attacks (../../etc/passwd), hidden file access (.git), and verify all are blocked while legitimate paths work

**Note**: This is prioritized before US3 and US4 because security is foundational for production use

### Tests for User Story 5

- [ ] T055 [P] [US5] Write tests/integration/test_security.py with comprehensive attack pattern tests (directory traversal, hidden files, symlink cycles, malicious queries)
- [ ] T056 [P] [US5] Add security violation test cases to tests/unit/test_path_validator.py (100+ attack patterns)
- [ ] T057 [P] [US5] Add query injection test cases to tests/unit/test_sanitizer.py (special chars, control chars, length limits)

### Implementation for User Story 5

- [ ] T058 [US5] Integrate path validation into all file access points in hierarchical_docs_mcp/services/markdown.py (before reading files)
- [ ] T059 [US5] Integrate path validation into hierarchical_docs_mcp/services/hierarchy.py (before directory scanning)
- [ ] T060 [US5] Integrate query sanitization into hierarchical_docs_mcp/services/search.py (before regex compilation)
- [ ] T061 [US5] Add audit logging for all security violations in hierarchical_docs_mcp/security/path_validator.py and sanitizer.py
- [ ] T062 [US5] Add audit logging for all file access attempts in hierarchical_docs_mcp/services/markdown.py
- [ ] T063 [US5] Implement timeout protection for long-running searches in hierarchical_docs_mcp/handlers/tools.py (30 second default)
- [ ] T064 [US5] Add error handling with clear security error messages in hierarchical_docs_mcp/handlers/tools.py and resources.py
- [ ] T065 [US5] Verify all User Story 5 security tests pass (T055-T057)

**Checkpoint**: Security hardening complete - system blocks 100% of tested attack patterns

---

## Phase 6: User Story 3 - Cross-Platform Compatibility (Priority: P2)

**Goal**: Ensure MCP server works seamlessly with both Claude Desktop and VS Code/GitHub Copilot

**Independent Test**: Configure server in Claude Desktop config and VS Code mcp.json, verify same queries work in both environments

### Tests for User Story 3

- [ ] T066 [P] [US3] Write tests/integration/test_claude_desktop.py simulating Claude Desktop stdio transport and configuration
- [ ] T067 [P] [US3] Write tests/integration/test_vscode_copilot.py simulating VS Code MCP integration and workspace-relative paths
- [ ] T068 [P] [US3] Add cross-platform path handling tests to tests/unit/test_hierarchy.py (Windows backslashes, POSIX forward slashes)

### Implementation for User Story 3

- [ ] T069 [P] [US3] Ensure pathlib.Path usage throughout for cross-platform path handling in all services
- [ ] T070 [P] [US3] Add workspace-relative path resolution in hierarchical_docs_mcp/config.py (support ${workspaceFolder} variable)
- [ ] T071 [US3] Test stdio transport on Windows, macOS, and Linux in CI (update GitHub Actions workflow if exists)
- [ ] T072 [US3] Create Claude Desktop config example in docs/config-examples/claude-desktop.json
- [ ] T073 [US3] Create VS Code config example in docs/config-examples/vscode-mcp.json
- [ ] T074 [US3] Update README.md with configuration instructions for both platforms
- [ ] T075 [US3] Verify all User Story 3 tests pass (T066-T068) on all platforms

**Checkpoint**: Cross-platform compatibility verified - works on Claude Desktop and VS Code

---

## Phase 7: User Story 4 - Multi-Source Documentation Aggregation (Priority: P3)

**Goal**: Support multiple documentation sources with unified hierarchical view and cross-source search

**Independent Test**: Configure multiple source paths (./docs, ./api-specs, external repo), verify unified navigation and search across all sources

### Tests for User Story 4

- [ ] T076 [P] [US4] Write tests/integration/test_multi_source.py with tests for multiple source loading, unified hierarchy, source attribution
- [ ] T077 [P] [US4] Write tests/unit/test_hierarchy.py test cases for merging overlapping category names with source labels
- [ ] T078 [P] [US4] Add search test cases to tests/unit/test_search.py for cross-source search with source filtering

### Implementation for User Story 4

- [ ] T079 [P] [US4] Extend hierarchical_docs_mcp/config.py to support sources list with SourceConfig objects
- [ ] T080 [P] [US4] Implement multi-source scanning in hierarchical_docs_mcp/services/hierarchy.py (iterate all configured sources)
- [ ] T081 [US4] Add source attribution to Category and Document models in hierarchical_docs_mcp/models/document.py and navigation.py
- [ ] T082 [US4] Update hierarchical_docs_mcp/services/search.py to search across all sources with source filtering
- [ ] T083 [US4] Update navigation context in hierarchical_docs_mcp/handlers/tools.py to show source labels in breadcrumbs
- [ ] T084 [US4] Add search_by_metadata() tool handler in hierarchical_docs_mcp/handlers/tools.py supporting tag-based search across sources
- [ ] T085 [US4] Create .mcp-docs.yaml configuration file example in docs/config-examples/ showing multi-source setup
- [ ] T086 [US4] Update README.md with multi-source configuration documentation
- [ ] T087 [US4] Verify all User Story 4 tests pass (T076-T078)

**Checkpoint**: Multi-source aggregation complete - unified view across distributed documentation

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T088 [P] Write comprehensive unit tests for all edge cases in tests/unit/ (empty directories, malformed YAML, Unicode filenames, symlinks)
- [ ] T089 [P] Add performance tests to tests/integration/test_performance.py (5000 document corpus, concurrent queries, memory usage)
- [ ] T090 [P] Verify success criteria SC-001 through SC-020 from spec.md with performance tests
- [ ] T091 [P] Create detailed API documentation in docs/api-reference.md documenting all MCP tools and resources
- [ ] T092 [P] Create troubleshooting guide in docs/troubleshooting.md based on quickstart.md common issues
- [ ] T093 [P] Create security guide in docs/security.md documenting validation patterns and best practices
- [ ] T094 [P] Add type hints and docstrings to all public functions across hierarchical_docs_mcp/
- [ ] T095 Code cleanup and refactoring across all modules for readability
- [ ] T096 Run quickstart.md validation manually with real Claude Desktop and VS Code
- [ ] T097 Create GitHub Actions CI workflow for automated testing (pytest, coverage, security scans)
- [ ] T098 Add code coverage reporting and ensure >80% coverage threshold
- [ ] T099 Create CONTRIBUTING.md with development setup and contribution guidelines
- [ ] T100 Final integration test: Run MCP Inspector tool to validate protocol compliance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core markdown navigation (MVP)
- **User Story 2 (Phase 4)**: Depends on Foundational - OpenAPI discovery (parallel to US1)
- **User Story 5 (Phase 5)**: Depends on Foundational - Security hardening (should complete before production)
- **User Story 3 (Phase 6)**: Depends on US1, US2 complete - Cross-platform testing
- **User Story 4 (Phase 7)**: Depends on US1 complete - Multi-source builds on single-source
- **Polish (Phase 8)**: Depends on all user stories - Final production hardening

### User Story Dependencies

```
Foundational (Phase 2)
    ├─> User Story 1 (P1) - Markdown Navigation [MVP - Can deploy after this]
    ├─> User Story 2 (P1) - OpenAPI Discovery [Parallel to US1]
    └─> User Story 5 (P2) - Security [Should complete before production]
            └─> User Story 3 (P2) - Cross-Platform [Needs US1+US2 to test]
                    └─> User Story 4 (P3) - Multi-Source [Builds on US1]
```

### Within Each User Story

1. Tests written FIRST (must fail)
2. Models implemented (data structures)
3. Services implemented (business logic)
4. Handlers implemented (MCP protocol)
5. Integration points added
6. Tests verified passing
7. Story checkpoint validated

### Parallel Opportunities

**Phase 1 (Setup)**: Tasks T003-T011 can all run in parallel (different files)

**Phase 2 (Foundational)**: 
- Security: T016-T019 can run in parallel (test + impl for path validation and sanitizer)
- Models: T020-T022 can run in parallel (different entity files)
- Tests: T024, T016, T017 can run in parallel (different test files)

**Phase 3 (User Story 1)**:
- Tests: T028-T032 can all run in parallel (different test files)
- Initial impl: T033-T034 can run in parallel (markdown.py and hierarchy.py are independent)

**Phase 4 (User Story 2)**:
- Tests: T042-T045 can all run in parallel
- Initial impl: T046-T048 can run in parallel (OpenAPI loading functions)
- **ENTIRE PHASE 4 can run parallel to Phase 3** if team capacity allows (US1 and US2 are independent)

**Phase 5 (User Story 5)**:
- Tests: T055-T057 can all run in parallel

**Phase 6 (User Story 3)**:
- Tests: T066-T068 can all run in parallel
- Docs: T072-T073 can run in parallel

**Phase 7 (User Story 4)**:
- Tests: T076-T078 can all run in parallel
- Initial impl: T079-T080 can run in parallel

**Phase 8 (Polish)**:
- Most tasks T088-T094, T097-T099 can run in parallel (different files/concerns)

---

## Parallel Example: User Story 1 Implementation

Team of 3 developers can work in parallel after tests are written:

```bash
# Developer 1: Markdown parsing
T033: hierarchical_docs_mcp/services/markdown.py

# Developer 2: Hierarchy building
T034: hierarchical_docs_mcp/services/hierarchy.py

# Developer 3: Search engine
T035: hierarchical_docs_mcp/services/search.py

# Then all integrate in handlers (sequential)
T036: hierarchical_docs_mcp/handlers/tools.py
T037: hierarchical_docs_mcp/handlers/resources.py
```

---

## MVP Scope (Minimum Viable Product)

**Recommended MVP: Phase 1 + Phase 2 + Phase 3 (User Story 1 only)**

This delivers:
- ✅ Core markdown navigation with hierarchy
- ✅ Breadcrumb context in results
- ✅ YAML frontmatter support
- ✅ Basic search functionality
- ✅ Security validation
- ✅ Caching with file watching
- ✅ stdio transport for local use

**MVP is independently testable**: Configure local docs, connect AI assistant, ask documentation questions

**Post-MVP Increments**:
1. Add User Story 2 (OpenAPI support) - attracts API-first projects
2. Add User Story 5 (Security hardening) - required before production
3. Add User Story 3 (Cross-platform) - expands user base
4. Add User Story 4 (Multi-source) - handles complex projects

---

## Implementation Strategy

### Week 1-2: Foundation (Phases 1-2)
- Setup project structure
- Implement security validation
- Create data models
- Setup MCP server skeleton

**Deliverable**: Project initialized, security layer working, ready for feature development

### Week 3-4: MVP (Phase 3 - US1)
- TDD: Write all tests first
- Implement markdown parsing
- Implement hierarchy navigation
- Implement search
- Integrate with MCP handlers

**Deliverable**: Working MVP - AI assistants can navigate markdown documentation

### Week 5-6: OpenAPI Support (Phase 4 - US2)
- TDD: Write OpenAPI tests
- Implement OpenAPI parsing
- Add API endpoint tools
- Integrate with existing search

**Deliverable**: Full markdown + OpenAPI support

### Week 7: Security Hardening (Phase 5 - US5)
- Comprehensive security testing
- Audit logging
- Timeout protection
- Error handling refinement

**Deliverable**: Production-ready security

### Week 8: Cross-Platform (Phase 6 - US3)
- Test on all platforms
- Configuration examples
- Documentation updates

**Deliverable**: Works on Claude Desktop and VS Code

### Week 9: Multi-Source (Phase 7 - US4)
- Multi-source configuration
- Unified navigation
- Cross-source search

**Deliverable**: Enterprise-ready for complex projects

### Week 10: Polish (Phase 8)
- Performance optimization
- Documentation completion
- CI/CD setup
- Final validation

**Deliverable**: Production release ready

---

## Task Count Summary

- **Total Tasks**: 100
- **Phase 1 (Setup)**: 11 tasks
- **Phase 2 (Foundational)**: 16 tasks (BLOCKING)
- **Phase 3 (US1 - MVP)**: 14 tasks
- **Phase 4 (US2)**: 13 tasks
- **Phase 5 (US5)**: 11 tasks
- **Phase 6 (US3)**: 10 tasks
- **Phase 7 (US4)**: 12 tasks
- **Phase 8 (Polish)**: 13 tasks

**Parallel Opportunities**: ~40% of tasks can run in parallel with proper coordination

**Critical Path**: Phase 1 → Phase 2 → Phase 3 (US1) → Phase 6 (US3) (for cross-platform validation)

**Fastest MVP**: ~4-5 weeks with 2-3 developers (Phases 1-3)

---

## Format Validation

✅ **All tasks follow required format**: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- ✅ Every task has checkbox `- [ ]`
- ✅ Every task has sequential ID (T001-T100)
- ✅ Parallelizable tasks marked with [P]
- ✅ User story tasks marked with [US1]-[US5]
- ✅ Setup and Foundational tasks have NO story label
- ✅ All tasks include specific file paths
- ✅ Tasks organized by user story phase
- ✅ Dependencies documented
- ✅ Independent test criteria per story defined
- ✅ Parallel opportunities identified
- ✅ MVP scope clearly defined (Phases 1-3)
