# Research: Claude Code Environment Enhancements

**Feature**: 001-claude-env-enhance | **Date**: 2026-03-14

## R1: CLAUDE.md Content and Structure

**Decision**: Create a root-level `CLAUDE.md` (not `.claude/CLAUDE.md`) with project commands, architecture overview, and conventions.

**Rationale**: Root-level CLAUDE.md is loaded eagerly at session start and is the most visible location. The `.claude/CLAUDE.md` is lazy-loaded. Since this contains essential context (commands, architecture), it should load immediately.

**Alternatives considered**:
- `.claude/CLAUDE.md` — rejected because it lazy-loads, meaning Claude may not have commands available at session start
- Splitting across multiple files — rejected because the content is concise enough for a single file (<100 lines target)

**Content structure**:
1. Common commands (build, test, lint, run)
2. Project architecture (module map with purposes)
3. Code conventions (ruff config, type hints, async patterns)
4. Constitution reference (link to `.specify/memory/constitution.md`)

---

## R2: Hook Configuration Patterns

**Decision**: Use `command` type hooks in `.claude/settings.json` with shell scripts in `.claude/hooks/`.

**Rationale**: Shell scripts are reusable, testable independently, and keep settings.json clean. The `command` type is the simplest hook type and sufficient for our needs (linting and context injection).

**Alternatives considered**:
- Inline commands in settings.json — rejected because multi-step logic (file extension checking, graceful failure) is unwieldy in a single JSON string
- Prompt/agent hooks — rejected because our hooks are deterministic (no LLM reasoning needed)

**Hook patterns**:

### PostToolUse (auto-lint)
- Matcher: `Edit|Write` (only fire after file modifications)
- Script receives tool input via stdin as JSON
- Extract `file_path` from JSON, check if `.py` extension
- Run `ruff check --fix` then `ruff format` on the file
- Exit 0 always (never block Claude)

### Notification
- Matcher: empty string (fire on all notifications)
- Use `notify-send` on Linux/WSL
- Exit 0 always

### SessionStart
- Matcher: empty string (fire on all session starts)
- Output git branch, last 5 commits (oneline), and active spec directory
- All git commands wrapped in conditionals for graceful failure

---

## R3: Permissions Allowlist Syntax

**Decision**: Use project-level `.claude/settings.json` with explicit `permissions.allow` and `permissions.deny` arrays.

**Rationale**: Project-level settings are shared with the team via git. The allowlist syntax supports glob patterns for flexible matching while the denylist provides a safety net.

**Alternatives considered**:
- Keep `skipDangerousModePermissionPrompt: true` — rejected because it provides no protection against genuinely dangerous commands
- User-level permissions only — rejected because project-specific safe commands should be shared with all developers

**Allowlist entries** (from Claude Code permission syntax):
```
Bash(pytest *)           # Test runner
Bash(python -m pytest *) # Alternative test invocation
Bash(ruff *)             # Linter
Bash(pip *)              # Package manager
Bash(git *)              # Version control
Bash(gh *)               # GitHub CLI
Bash(your-docs-*)        # Project CLI commands
Bash(ls *)               # Directory listing
Bash(cat *)              # File reading (fallback)
Edit                     # File editing
Read                     # File reading
Glob                     # File search
Grep                     # Content search
Write                    # File creation
```

**Denylist entries**:
```
Bash(rm -rf *)           # Recursive force delete
Bash(sudo *)             # Privilege escalation
Bash(git push --force *) # Force push
Bash(git push -f *)      # Force push (short form)
Bash(git reset --hard *) # Hard reset
```

---

## R4: Path-Specific Rules Format

**Decision**: Use `.claude/rules/*.md` files with YAML frontmatter `paths` field for scoping.

**Rationale**: Path-specific rules auto-load when Claude works on matching files. This is the standard Claude Code mechanism for contextual instructions.

**Alternatives considered**:
- Putting all rules in CLAUDE.md — rejected because it bloats the main file and loads rules unconditionally
- Using subdirectory-specific CLAUDE.md files — rejected because rules/ is the official mechanism for path-scoped instructions

**Rule files**:

### testing.md (paths: `tests/**`)
- Use pytest with pytest-asyncio
- Follow existing fixture patterns
- Test structure: Arrange-Act-Assert
- Use `@pytest.mark.asyncio` for async tests
- Reference test tiers: contract, integration, unit

### security.md (paths: `docs_mcp/security/**`)
- Validate all inputs at boundaries
- Test for directory traversal patterns
- Use `pathlib.Path.resolve()` for path operations
- Include attack pattern tests

### services.md (paths: `docs_mcp/services/**`)
- Follow async/await patterns
- Use proper error handling with specific exception types
- Services must be independently testable
- Use dependency injection for testability

---

## R5: MCP Server Dogfooding Configuration

**Decision**: Use `.mcp.json` at project root with `stdio` transport pointing to `your-docs-mcp` command.

**Rationale**: `.mcp.json` is the standard project-level MCP config file. Using stdio transport keeps it simple — no HTTP server to manage separately.

**Alternatives considered**:
- HTTP transport via `your-docs-web` — rejected because it requires a running web server, adding complexity
- User-level MCP config (`~/.claude.json`) — rejected because this should be shared with all project developers

**Configuration**:
```json
{
  "mcpServers": {
    "your-docs": {
      "command": "your-docs-mcp",
      "env": {
        "DOCS_ROOT": "./docs"
      }
    }
  }
}
```

---

## R6: SessionStart Hook Context

**Decision**: Shell script that outputs branch info, recent commits, and active feature spec as formatted text to stdout.

**Rationale**: SessionStart hooks can inject context by writing to stdout. The output becomes part of Claude's initial context. Keep it concise to minimize context consumption.

**Alternatives considered**:
- Using a prompt hook (LLM-evaluated) — rejected because we just need deterministic git output
- Reading from a status file — rejected because git commands give live data

**Output format**:
```
📌 Branch: 001-claude-env-enhance
📋 Recent commits:
  d46ca21 Remove outdated guides and enhance documentation structure
  b31edf0 Bump version from 0.0.3 to 0.0.4
  e5e952b feat: add vector search capabilities with ChromaDB integration
📂 Active spec: specs/001-claude-env-enhance/
```

---

## R7: Global Settings Migration

**Decision**: Remove `skipDangerousModePermissionPrompt: true` from `~/.claude/settings.json` after project permissions are in place.

**Rationale**: The project-level allowlist provides equivalent convenience for this project while maintaining safety. Other projects will start prompting again, which is the desired default behavior.

**Alternatives considered**:
- Keep both — rejected because the global skip undermines the project denylist
- Move to project-local only — the global setting should be removed to restore safe defaults across all projects

**Migration**: Manual one-time change to `~/.claude/settings.json`.
