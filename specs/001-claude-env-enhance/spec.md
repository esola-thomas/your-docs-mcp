# Feature Specification: Claude Code Environment Enhancements

**Feature Branch**: `001-claude-env-enhance`
**Created**: 2026-03-14
**Status**: Draft
**Input**: User description: "Enhance the Claude Code development environment with project CLAUDE.md, hooks, permissions allowlist, path-specific rules, MCP server dogfooding config, and session start context"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Gets Productive Immediately (Priority: P1)

A developer clones the repository and starts a Claude Code session. Without reading any documentation, Claude already knows how to build, test, lint, and run the project. Claude understands the project architecture, conventions, and common commands because a project-level CLAUDE.md provides this context automatically.

**Why this priority**: This is the foundation — every Claude Code session benefits from accurate project context. Without it, Claude guesses at commands, misunderstands conventions, and produces inconsistent output.

**Independent Test**: Start a fresh Claude Code session and ask "run the tests" — Claude should execute the correct command without being told what it is.

**Acceptance Scenarios**:

1. **Given** a fresh Claude Code session in the repo, **When** a developer asks Claude to run tests, **Then** Claude uses the correct test command without asking
2. **Given** a fresh session, **When** a developer asks Claude to lint the code, **Then** Claude uses ruff with the project's configured rules
3. **Given** a developer new to the project, **When** they start a session, **Then** Claude can describe the project architecture and key modules without reading every file

---

### User Story 2 - Code Quality Enforced Automatically via Hooks (Priority: P2)

When Claude edits or creates Python files, a post-tool hook automatically runs the project linter (ruff) on the changed file. This catches formatting and style issues immediately rather than at commit time. Additionally, a notification hook alerts the developer when Claude needs attention during long-running tasks.

**Why this priority**: Automated quality enforcement reduces review cycles and catches issues early. Hooks are a force multiplier that improves every editing action.

**Independent Test**: Have Claude edit a Python file with a minor style violation — the hook should auto-fix it and Claude should see the formatted result.

**Acceptance Scenarios**:

1. **Given** Claude edits a Python file, **When** the edit completes, **Then** ruff automatically formats the file
2. **Given** Claude creates a new Python file, **When** the write completes, **Then** ruff check runs on the file
3. **Given** Claude finishes a long task while the terminal is in the background, **When** a notification event fires, **Then** the developer receives a desktop notification

---

### User Story 3 - Safe Permissions Without Constant Prompting (Priority: P2)

The developer can work without being interrupted by permission prompts for common, safe operations (running tests, git commands, reading files) while still being protected from dangerous operations (force pushes, recursive deletes, sudo). This replaces the current "skip all dangerous mode prompts" setting with a targeted allowlist.

**Why this priority**: The current `skipDangerousModePermissionPrompt: true` setting is an all-or-nothing approach. A permissions allowlist provides both safety and flow state.

**Independent Test**: Run a session with the new settings — common commands execute without prompts, but `rm -rf` or `sudo` triggers a permission dialog.

**Acceptance Scenarios**:

1. **Given** the permissions allowlist is configured, **When** Claude runs `pytest`, **Then** the command executes without a permission prompt
2. **Given** the allowlist, **When** Claude runs `git commit`, **Then** it executes without prompting
3. **Given** the allowlist, **When** Claude attempts `rm -rf /`, **Then** the action is denied

---

### User Story 4 - Context-Aware Rules for Different Code Areas (Priority: P3)

When Claude works in the test directory, it follows TDD conventions and uses the project's testing patterns. When working in the security module, it applies extra scrutiny for input validation and path traversal. When working in services, it follows the async handler pattern. These rules load automatically based on file paths.

**Why this priority**: Path-specific rules reduce the need for developers to remind Claude of conventions when working in different parts of the codebase.

**Independent Test**: Ask Claude to write a new test — it should follow the project's existing test patterns (pytest, async, fixtures) without being told.

**Acceptance Scenarios**:

1. **Given** Claude is editing files in `tests/`, **When** rules load, **Then** Claude follows TDD patterns with pytest-asyncio conventions
2. **Given** Claude is editing files in `docs_mcp/security/`, **When** rules load, **Then** Claude prioritizes input validation and path traversal prevention
3. **Given** Claude is editing files in `docs_mcp/services/`, **When** rules load, **Then** Claude follows the async service pattern with proper error handling

---

### User Story 5 - Dogfood the MCP Server During Development (Priority: P3)

The project's own MCP server is configured in `.mcp.json` so Claude can use it during development. This means Claude can search the project's documentation, navigate the doc hierarchy, and verify MCP tool behavior directly — eating your own dog food.

**Why this priority**: Using your own product during development catches usability issues early and validates that the MCP tools work correctly from an AI assistant's perspective.

**Independent Test**: Ask Claude to search the project documentation using the MCP server tools — it should return results from the `docs/` directory.

**Acceptance Scenarios**:

1. **Given** the MCP server is configured in `.mcp.json`, **When** Claude starts a session, **Then** the MCP server tools are available
2. **Given** the MCP server is running, **When** Claude uses `search_documentation`, **Then** it returns results from the project's docs
3. **Given** the MCP server is running, **When** Claude uses `get_table_of_contents`, **Then** it returns the documentation hierarchy

---

### User Story 6 - Session Start Injects Project Context (Priority: P3)

When a Claude Code session starts, a hook injects useful project state — current branch, recent commits, test coverage status, and any active feature specs. This gives Claude immediate situational awareness.

**Why this priority**: Session start context eliminates the "where were we?" problem and reduces the warm-up time for each session.

**Independent Test**: Start a new session — Claude should immediately know the current branch and recent activity without being asked.

**Acceptance Scenarios**:

1. **Given** a session starts, **When** the SessionStart hook fires, **Then** Claude receives the current branch name and recent commit summary
2. **Given** a session starts on a feature branch, **When** context is injected, **Then** Claude knows which spec/feature is being worked on

---

### Edge Cases

- What happens when ruff is not installed? The hook should fail gracefully with a warning, not block Claude's work.
- What happens when the MCP server fails to start? Claude should still function normally with standard tools.
- What happens when a developer adds custom permissions that conflict with the project allowlist? Local settings should override project settings per Claude Code's hierarchy.
- What happens when path-specific rules conflict with global CLAUDE.md instructions? More specific rules should take precedence per Claude Code's rule resolution.
- What happens when the SessionStart hook runs but git is not initialized? The hook should output what it can and skip what it can't.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Project MUST have a CLAUDE.md with build, test, lint, and run commands for the project
- **FR-002**: Project CLAUDE.md MUST document the project architecture (modules, their purposes, and relationships)
- **FR-003**: Project CLAUDE.md MUST specify code conventions (line length, import ordering, type hints, docstring style)
- **FR-004**: A PostToolUse hook MUST run the linter on Python files after Edit or Write tool actions
- **FR-005**: A Notification hook MUST send desktop notifications when Claude needs attention
- **FR-006**: Project settings MUST define a permissions allowlist for common safe commands (test runner, git, package manager, linter)
- **FR-007**: Project settings MUST deny dangerous commands (recursive force delete, privilege escalation, force push)
- **FR-008**: Path-specific rules MUST exist for test, security, and service code areas
- **FR-009**: An MCP configuration file MUST configure the project's own MCP server for development use
- **FR-010**: A SessionStart hook MUST inject current branch, recent commits, and active feature context
- **FR-011**: All hooks MUST fail gracefully — a hook failure MUST NOT block Claude's normal operation
- **FR-012**: The permissions configuration MUST replace the current blanket permission skip with a targeted allowlist

### Key Entities

- **CLAUDE.md**: Central project instruction file — contains commands, architecture, and conventions
- **Hook**: Shell command triggered by Claude Code events — configured in settings files
- **Rule**: Path-scoped instruction file in `.claude/rules/` — loaded when Claude works on matching files
- **Permission Entry**: Allowlist or denylist item controlling which tools Claude can use without prompting
- **MCP Config**: Server definition in `.mcp.json` — makes MCP tools available to Claude during sessions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new developer can start a Claude Code session and execute build, test, and lint commands correctly on the first attempt without manual guidance
- **SC-002**: 100% of Python file edits by Claude are automatically formatted by the linter before the developer sees them
- **SC-003**: Common development commands (test, lint, git operations) execute without permission prompts while dangerous operations are still blocked
- **SC-004**: Claude follows the correct conventions for each code area (tests, security, services) without being reminded by the developer
- **SC-005**: Claude can search and navigate the project's own documentation using MCP tools during development sessions
- **SC-006**: Each new session begins with Claude having awareness of the current branch and recent project activity

## Assumptions

- **A-001**: The development machine has ruff installed (it's a dev dependency in pyproject.toml)
- **A-002**: The development environment is Linux/WSL (notification hook uses notify-send)
- **A-003**: The MCP server can be started via the project's CLI command with DOCS_ROOT pointing to the local docs directory
- **A-004**: Developers use the Claude Code CLI as the primary interface
- **A-005**: The global user settings may be modified to remove the blanket permission skip — this affects all projects for this user
- **A-006**: Project settings are committed to git and shared with the team
