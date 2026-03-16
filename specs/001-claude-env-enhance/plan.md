# Implementation Plan: Claude Code Environment Enhancements

**Branch**: `001-claude-env-enhance` | **Date**: 2026-03-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-claude-env-enhance/spec.md`

## Summary

Enhance the Claude Code development environment for the your-docs-mcp project by creating a project-level CLAUDE.md with build/test/lint commands and architecture docs, configuring PostToolUse hooks for auto-linting and notifications, replacing the blanket `skipDangerousModePermissionPrompt` with a targeted permissions allowlist, adding path-specific rules for tests/security/services directories, setting up `.mcp.json` for dogfooding the project's own MCP server, and adding a SessionStart hook for branch/commit context injection.

## Technical Context

**Language/Version**: Python 3.10+ (target 3.11)
**Primary Dependencies**: Claude Code CLI (configuration files only — no runtime code changes)
**Storage**: N/A (configuration files only)
**Testing**: Manual validation — start Claude Code sessions and verify behavior
**Target Platform**: Linux/WSL2 (developer workstation)
**Project Type**: Configuration enhancement (no source code changes)
**Performance Goals**: Hooks must complete in <2s to avoid disrupting Claude's flow
**Constraints**: All config files must be valid JSON/Markdown per Claude Code schemas; hooks must exit 0 on success, fail gracefully
**Scale/Scope**: 6 configuration files, 3 rule files, 2 hook scripts, 1 CLAUDE.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First Architecture | **N/A** | No runtime code — configuration files only |
| II. Protocol Compliance | **PASS** | `.mcp.json` uses standard MCP server config format |
| III. Test-First Development | **PASS** | Manual validation plan defined; no testable code being written |
| IV. Security-By-Design | **PASS** | Permissions denylist blocks dangerous commands; hooks validate inputs |
| V. Performance & Observability | **PASS** | Hooks use `|| true` for graceful failure; <2s execution target |

**Gate Result**: PASS — no violations. Proceeding to Phase 0.

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First Architecture | **N/A** | No new modules — config files only |
| II. Protocol Compliance | **PASS** | `.mcp.json` uses standard MCP server config; stdio transport |
| III. Test-First Development | **PASS** | Manual verification plan in quickstart.md; no testable code |
| IV. Security-By-Design | **PASS** | Denylist blocks rm -rf, sudo, force push; hooks validate file extensions |
| V. Performance & Observability | **PASS** | Hook scripts target <2s; graceful failure with `|| true` |

**Post-Design Gate Result**: PASS — design is configuration-only, no constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-claude-env-enhance/
├── plan.md              # This file
├── research.md          # Phase 0: hook patterns, permissions syntax, MCP config
├── data-model.md        # Phase 1: file inventory and content contracts
├── quickstart.md        # Phase 1: verification steps
├── contracts/           # Phase 1: file format contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# New files to create (configuration only — no runtime code)
CLAUDE.md                              # Project instructions for Claude Code
.claude/
├── settings.json                      # Project permissions + hooks (team-shared)
├── settings.local.json                # Local overrides template (gitignored)
├── rules/
│   ├── testing.md                     # Rules for tests/ directory
│   ├── security.md                    # Rules for docs_mcp/security/
│   └── services.md                    # Rules for docs_mcp/services/
└── hooks/
    ├── post-edit-lint.sh              # PostToolUse: run ruff on edited Python files
    └── session-context.sh            # SessionStart: inject branch/commit context

.mcp.json                              # MCP server dogfooding config

# Existing files to modify
# ~/.claude/settings.json              # Remove skipDangerousModePermissionPrompt
```

**Structure Decision**: Configuration-only feature. All new files are Claude Code config files (markdown rules, JSON settings, shell hook scripts, MCP config). No changes to `docs_mcp/` source code or `tests/`.

## Complexity Tracking

> No constitution violations — this section is intentionally empty.
