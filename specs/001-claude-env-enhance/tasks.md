# Tasks: Claude Code Environment Enhancements

**Input**: Design documents from `/specs/001-claude-env-enhance/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not applicable — this feature produces configuration files only. Verification is manual per quickstart.md.

**Organization**: Tasks grouped by user story. Note that `.claude/settings.json` is a shared file (permissions + hooks), so it's created once in the Foundational phase with all sections complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure for all new configuration files

- [x] T001 Create hooks directory at .claude/hooks/
- [x] T002 Create rules directory at .claude/rules/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared `.claude/settings.json` that US2, US3, and US6 all depend on. This single file contains permissions (US3), PostToolUse hooks (US2), Notification hooks (US2), and SessionStart hooks (US6).

**Why foundational**: `.claude/settings.json` is one JSON file that cannot be created piecemeal across stories. It must be complete and valid from the start.

- [x] T003 Create .claude/settings.json with complete permissions allowlist (Bash patterns for pytest, ruff, git, gh, pip, your-docs-*, ls, cat), denylist (rm -rf, sudo, git push --force, git push -f, git reset --hard), built-in tool allows (Edit, Read, Glob, Grep, Write), PostToolUse hook referencing .claude/hooks/post-edit-lint.sh with matcher "Edit|Write", Notification hook with inline notify-send command, and SessionStart hook referencing .claude/hooks/session-context.sh — per research.md R2/R3 and contracts/file-formats.md Contract 2

**Checkpoint**: Settings file ready — hook scripts and rules can now be created in any order

---

## Phase 3: User Story 1 - Developer Gets Productive Immediately (Priority: P1) MVP

**Goal**: Create a project-level CLAUDE.md so Claude knows build/test/lint commands, architecture, and conventions at session start

**Independent Test**: Start a fresh Claude Code session and ask "run the tests" — Claude should respond with the correct command without asking

### Implementation for User Story 1

- [x] T004 [US1] Replace auto-generated CLAUDE.md at repository root with hand-crafted version containing: Commands section (pip install -e ".[dev]" for install, pytest for test, ruff check . and ruff format . for lint, your-docs-server for run), Architecture section (docs_mcp/ with handlers/, models/, services/, security/, utils/ and their purposes), Conventions section (ruff line-length 100, target py310, select E/F/I/N/W/UP, type hints on public interfaces, async/await for all I/O, Pydantic v2 for models), and Constitution reference linking to .specify/memory/constitution.md — per research.md R1 and contracts/file-formats.md Contract 1, target <100 lines

**Checkpoint**: US1 complete — Claude knows all project commands and conventions at session start

---

## Phase 4: User Story 2 - Code Quality Enforced Automatically via Hooks (Priority: P2)

**Goal**: Auto-lint Python files after every edit and notify developer when Claude needs attention

**Independent Test**: Have Claude edit a Python file — ruff should auto-format it immediately after the edit completes

### Implementation for User Story 2

- [x] T005 [US2] Create .claude/hooks/post-edit-lint.sh: read JSON from stdin, extract file_path via jq or python -c, check if file ends in .py, run ruff check --fix then ruff format on the file, wrap all commands in || true for graceful failure, handle missing ruff with warning to stderr, set executable permission — per research.md R2 and contracts/file-formats.md Contract 4

**Checkpoint**: US2 complete — every Python file edit is auto-formatted, notifications work

---

## Phase 5: User Story 3 - Safe Permissions Without Constant Prompting (Priority: P2)

**Goal**: Replace blanket `skipDangerousModePermissionPrompt` with targeted project allowlist

**Independent Test**: Run pytest without prompt, then try sudo — pytest passes silently, sudo is blocked

### Implementation for User Story 3

- [x] T006 [US3] Remove skipDangerousModePermissionPrompt from ~/.claude/settings.json (keep model, alwaysThinkingEnabled, feedbackSurveyState) — per research.md R7

**Checkpoint**: US3 complete — safe commands flow freely, dangerous commands are blocked

---

## Phase 6: User Story 4 - Context-Aware Rules for Different Code Areas (Priority: P3)

**Goal**: Auto-load directory-specific conventions when Claude edits tests, security, or service files

**Independent Test**: Ask Claude to write a new test — it should use pytest-asyncio and Arrange-Act-Assert without being told

### Implementation for User Story 4

- [x] T007 [P] [US4] Create .claude/rules/testing.md with paths: ["tests/**"] frontmatter and rules: use pytest with pytest-asyncio, @pytest.mark.asyncio for async tests, Arrange-Act-Assert structure, use existing fixtures from conftest.py, three test tiers (contract/ integration/ unit/), minimum 80% coverage target 95%+, test file naming test_*.py — per research.md R4
- [x] T008 [P] [US4] Create .claude/rules/security.md with paths: ["docs_mcp/security/**"] frontmatter and rules: validate all inputs at system boundaries, use pathlib.Path.resolve() for path operations, test for directory traversal patterns (../, encoded variants), sanitize all query inputs, include attack pattern tests in corresponding test files, audit log all security-relevant operations — per research.md R4
- [x] T009 [P] [US4] Create .claude/rules/services.md with paths: ["docs_mcp/services/**"] frontmatter and rules: use async/await for all I/O operations, specific exception types (not bare except), services must be independently testable with dependency injection, use docs_mcp.utils.logger for structured logging, follow existing service patterns (cache.py, search.py as reference) — per research.md R4

**Checkpoint**: US4 complete — Claude adapts behavior based on which directory it's working in

---

## Phase 7: User Story 5 - Dogfood the MCP Server During Development (Priority: P3)

**Goal**: Configure the project's own MCP server so Claude can use its tools during development

**Independent Test**: Ask Claude "What MCP tools do you have?" — should list search_documentation, get_table_of_contents, etc.

### Implementation for User Story 5

- [x] T010 [US5] Create .mcp.json at repository root with mcpServers.your-docs configuration: command "your-docs-mcp", env DOCS_ROOT "./docs" — per research.md R5 and contracts/file-formats.md Contract 5

**Checkpoint**: US5 complete — Claude can search and navigate project docs via MCP tools

---

## Phase 8: User Story 6 - Session Start Injects Project Context (Priority: P3)

**Goal**: Inject current branch, recent commits, and active feature spec at session start

**Independent Test**: Start a new session — Claude should know the current branch without being asked

### Implementation for User Story 6

- [x] T011 [US6] Create .claude/hooks/session-context.sh: output current git branch (git branch --show-current), last 5 commits oneline (git log --oneline -5), detect active spec directory by matching branch name to specs/ directories, wrap all git commands in if-checks for non-git environments, set executable permission — per research.md R6 and contracts/file-formats.md Contract 4

**Checkpoint**: US6 complete — every session starts with branch awareness and recent activity context

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Validate everything works together and clean up

- [x] T012 Verify all hook scripts have executable permission (chmod +x .claude/hooks/*.sh)
- [x] T013 Validate .claude/settings.json is valid JSON (python -m json.tool .claude/settings.json)
- [x] T014 Validate .mcp.json is valid JSON (python -m json.tool .mcp.json)
- [x] T015 Run full quickstart.md verification steps 1-6 from specs/001-claude-env-enhance/quickstart.md
- [x] T016 Add .claude/settings.local.json to .gitignore if not already present (for developer-specific overrides)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (directories must exist for hook paths)
- **US1 (Phase 3)**: Independent — can start after Phase 1 (no dependency on settings.json)
- **US2 (Phase 4)**: Depends on Phase 2 (hook referenced in settings.json)
- **US3 (Phase 5)**: Depends on Phase 2 (project permissions must exist before removing global skip)
- **US4 (Phase 6)**: Depends on Phase 1 (rules directory must exist)
- **US5 (Phase 7)**: Independent — can start after Phase 1
- **US6 (Phase 8)**: Depends on Phase 2 (hook referenced in settings.json)
- **Polish (Phase 9)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — can complete as standalone MVP
- **US2 (P2)**: No dependencies on other stories — hook script is self-contained
- **US3 (P2)**: No dependencies on other stories — but should be done after Phase 2 settings.json exists
- **US4 (P3)**: No dependencies on other stories — rule files are independent
- **US5 (P3)**: No dependencies on other stories — .mcp.json is independent
- **US6 (P3)**: No dependencies on other stories — hook script is self-contained

### Within Each User Story

- Each story produces 1-3 files with no cross-story file conflicts
- The only shared file (.claude/settings.json) is fully created in Phase 2

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel
- **After Phase 2**: US1, US4, and US5 can all start in parallel (different files, no dependencies)
- **Phase 6**: T007, T008, T009 can all run in parallel (different rule files)
- **After Phase 2**: US2, US3, and US6 can run in parallel (different files; settings.json already complete)

---

## Parallel Example: After Foundational Phase

```
# These can all launch simultaneously after Phase 2:
Task T004: "Create CLAUDE.md at repository root"           (US1 - different file)
Task T007: "Create .claude/rules/testing.md"                (US4 - different file)
Task T008: "Create .claude/rules/security.md"               (US4 - different file)
Task T009: "Create .claude/rules/services.md"               (US4 - different file)
Task T010: "Create .mcp.json at repository root"            (US5 - different file)
Task T005: "Create .claude/hooks/post-edit-lint.sh"         (US2 - different file)
Task T011: "Create .claude/hooks/session-context.sh"        (US6 - different file)
Task T006: "Remove skipDangerousModePermissionPrompt"       (US3 - different file)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: User Story 1 (T004)
4. **STOP and VALIDATE**: Start a Claude Code session, verify commands and architecture are known
5. This alone provides significant value — Claude is immediately productive

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. Add US1 (CLAUDE.md) → Test independently → Claude knows the project (MVP!)
3. Add US2 (auto-lint hook) → Test independently → Every edit auto-formatted
4. Add US3 (permissions) → Test independently → No more prompt interruptions
5. Add US4 (rules) → Test independently → Context-aware assistance
6. Add US5 (MCP dogfooding) → Test independently → Claude can search project docs
7. Add US6 (session context) → Test independently → Branch awareness at start
8. Polish → Full validation → Done

### Parallel Team Strategy

With multiple developers after Phase 2:
- Developer A: US1 (CLAUDE.md) + US4 (rules)
- Developer B: US2 (lint hook) + US6 (session hook)
- Developer C: US3 (permissions migration) + US5 (MCP config)

All stories complete independently, no merge conflicts (different files).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All 6 user stories are independently testable after Phase 2
- The shared .claude/settings.json is created once in Phase 2 to avoid multi-story conflicts
- Commit after each phase or logical group
- Stop at any checkpoint to validate that story independently
- Total: 16 tasks across 9 phases
