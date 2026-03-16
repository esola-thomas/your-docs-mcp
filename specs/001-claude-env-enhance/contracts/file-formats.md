# File Format Contracts

**Feature**: 001-claude-env-enhance | **Date**: 2026-03-14

This feature produces configuration files consumed by Claude Code. These contracts define the expected format and content of each file.

## Contract 1: CLAUDE.md

**Location**: Repository root (`/CLAUDE.md`)
**Consumer**: Claude Code CLI (loaded at session start)

```markdown
# Project Name

## Commands
- `command`: description
...

## Architecture
module/ — purpose
...

## Conventions
- convention description
...
```

**Constraints**:
- Must be valid Markdown
- Should be under 100 lines for optimal adherence
- No HTML or complex formatting
- Imperative instructions ("Use X", "Run Y") preferred over descriptions

---

## Contract 2: .claude/settings.json

**Location**: `/.claude/settings.json`
**Consumer**: Claude Code CLI (merged with global settings at session start)

```json
{
  "permissions": {
    "allow": [
      "ToolName",
      "Bash(pattern *)"
    ],
    "deny": [
      "Bash(dangerous *)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "path/to/script.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "path/to/script.sh"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'title' 'message'"
          }
        ]
      }
    ]
  }
}
```

**Constraints**:
- Must be valid JSON (no comments, no trailing commas)
- Permission patterns use glob syntax
- Hook matchers use regex syntax
- Hook commands run in the project root directory

---

## Contract 3: .claude/rules/*.md

**Location**: `/.claude/rules/{name}.md`
**Consumer**: Claude Code CLI (loaded when editing files matching paths)

```markdown
---
paths:
  - "glob/pattern/**/*.ext"
---

# Rule Title

- Instruction 1
- Instruction 2
...
```

**Constraints**:
- Must have valid YAML frontmatter with `paths` array
- Paths use glob syntax relative to repository root
- Content should be concise instructions (not documentation)
- No `---` in the body content (conflicts with frontmatter delimiter)

---

## Contract 4: .claude/hooks/*.sh

**Location**: `/.claude/hooks/{name}.sh`
**Consumer**: Claude Code CLI (executed on matching events)

**Input**: Depends on hook event type
- PostToolUse: JSON object on stdin with `tool_input` field
- SessionStart: No stdin
- Notification: JSON object on stdin

**Output**:
- stdout: Displayed in Claude's context (keep concise)
- stderr: Logged in verbose mode only
- Exit 0: Success (action proceeds)
- Exit 2: Block action (stderr becomes feedback to Claude)
- Other: Logged, action proceeds

**Constraints**:
- Must have executable permission (`chmod +x`)
- Must use `#!/usr/bin/env bash` shebang
- Must exit 0 for non-blocking hooks (lint, context)
- Should complete in <2 seconds
- Must handle missing dependencies gracefully (e.g., ruff not installed)

---

## Contract 5: .mcp.json

**Location**: Repository root (`/.mcp.json`)
**Consumer**: Claude Code CLI (MCP servers started at session init)

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable-name",
      "env": {
        "KEY": "value"
      }
    }
  }
}
```

**Constraints**:
- Must be valid JSON
- `command` must be an installed executable on the PATH
- `env` values support relative paths (resolved from project root)
- Server failures should not prevent Claude Code from starting
