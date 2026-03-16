# Data Model: Claude Code Environment Enhancements

**Feature**: 001-claude-env-enhance | **Date**: 2026-03-14

This feature produces configuration files, not runtime data structures. The "data model" is the inventory of files, their formats, and their relationships.

## File Inventory

### 1. CLAUDE.md (Project Instructions)

| Attribute | Value |
|-----------|-------|
| **Path** | `/CLAUDE.md` (repository root) |
| **Format** | Markdown |
| **Loaded** | Eagerly at session start |
| **Shared** | Yes (committed to git) |
| **Max Size** | <100 lines (to maintain adherence) |

**Sections**:
- Common Commands (build, test, lint, run, install)
- Architecture (module map with single-line descriptions)
- Code Conventions (ruff rules, type hints, async patterns, line length)
- Constitution reference

**Relationships**: References `pyproject.toml` for commands, `.specify/memory/constitution.md` for principles.

---

### 2. .claude/settings.json (Project Settings)

| Attribute | Value |
|-----------|-------|
| **Path** | `/.claude/settings.json` |
| **Format** | JSON |
| **Loaded** | At session start (merged with global settings) |
| **Shared** | Yes (committed to git) |

**Schema**:
```
{
  permissions: {
    allow: string[],    // Tool permission patterns
    deny: string[]      // Blocked tool patterns
  },
  hooks: {
    PostToolUse: HookConfig[],
    Notification: HookConfig[],
    SessionStart: HookConfig[]
  }
}

HookConfig = {
  matcher: string,        // Regex matching tool names or empty for all
  hooks: [{
    type: "command",
    command: string       // Shell command to execute
  }]
}
```

**Relationships**: Overrides `~/.claude/settings.json` for this project. References hook scripts in `.claude/hooks/`.

---

### 3. .claude/rules/*.md (Path-Specific Rules)

| Attribute | Value |
|-----------|-------|
| **Path** | `/.claude/rules/{testing,security,services}.md` |
| **Format** | Markdown with YAML frontmatter |
| **Loaded** | Lazily when Claude edits files matching `paths` patterns |
| **Shared** | Yes (committed to git) |

**Frontmatter Schema**:
```yaml
---
paths:
  - "glob/pattern/**"
---
```

**Relationships**: Complement CLAUDE.md with directory-specific guidance. More specific rules take precedence.

---

### 4. .claude/hooks/*.sh (Hook Scripts)

| Attribute | Value |
|-----------|-------|
| **Path** | `/.claude/hooks/{post-edit-lint,session-context}.sh` |
| **Format** | Bash script |
| **Loaded** | Executed by Claude Code on matching events |
| **Shared** | Yes (committed to git, executable bit set) |

**Input/Output Contract**:

| Script | Stdin | Stdout | Exit Code |
|--------|-------|--------|-----------|
| `post-edit-lint.sh` | JSON with `tool_input.file_path` | Lint output (shown to Claude) | 0 always |
| `session-context.sh` | None | Branch/commit/spec context text | 0 always |

**Relationships**: Referenced by `.claude/settings.json` hooks configuration.

---

### 5. .mcp.json (MCP Server Config)

| Attribute | Value |
|-----------|-------|
| **Path** | `/.mcp.json` (repository root) |
| **Format** | JSON |
| **Loaded** | At session start |
| **Shared** | Yes (committed to git) |

**Schema**:
```
{
  mcpServers: {
    [name: string]: {
      command: string,
      env?: Record<string, string>
    }
  }
}
```

**Relationships**: Starts the project's own MCP server, making its tools available during development.

---

## File Dependency Graph

```
CLAUDE.md
  └── references → pyproject.toml, constitution.md

.claude/settings.json
  ├── hooks.PostToolUse → .claude/hooks/post-edit-lint.sh
  ├── hooks.SessionStart → .claude/hooks/session-context.sh
  └── hooks.Notification → inline notify-send command

.claude/rules/testing.md     → scoped to tests/**
.claude/rules/security.md    → scoped to docs_mcp/security/**
.claude/rules/services.md    → scoped to docs_mcp/services/**

.mcp.json → starts your-docs-mcp with DOCS_ROOT=./docs
```

## State Transitions

N/A — configuration files are static. They are read at session start or on matching events. No runtime state changes.
