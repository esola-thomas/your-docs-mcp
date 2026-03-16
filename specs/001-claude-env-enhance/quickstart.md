# Quickstart: Verifying Claude Code Environment Enhancements

**Feature**: 001-claude-env-enhance | **Date**: 2026-03-14

## Prerequisites

- Claude Code CLI installed and authenticated
- `ruff` installed (`pip install ruff` or included in dev dependencies)
- `notify-send` available (standard on Linux, install `libnotify-bin` on WSL)
- Project installed in dev mode (`pip install -e ".[dev]"`)

## Verification Steps

### Step 1: CLAUDE.md Loads Correctly

1. Start a new Claude Code session in the repository root:
   ```bash
   claude
   ```
2. Ask: "What command do I use to run the tests?"
3. **Expected**: Claude responds with `pytest` or `python -m pytest` without asking for clarification
4. Ask: "Describe the project architecture"
5. **Expected**: Claude describes the module structure (handlers, models, services, security, utils) without reading files

### Step 2: PostToolUse Hook Auto-Lints

1. In a Claude Code session, ask Claude to create a Python file with intentional style issues:
   ```
   Create a file /tmp/test_hook.py with: import os,sys\ndef foo( x ):return x
   ```
2. **Expected**: After the Write tool completes, the hook runs ruff and the file is auto-formatted
3. Check the file — it should have proper formatting (imports on separate lines, spaces fixed)

### Step 3: Permissions Work Without Prompting

1. In a session, ask Claude to run tests:
   ```
   Run the test suite
   ```
2. **Expected**: `pytest` executes without a permission prompt
3. Ask Claude to run a denied command:
   ```
   Run: sudo apt update
   ```
4. **Expected**: Claude is blocked or prompted — it should NOT execute silently

### Step 4: Path-Specific Rules Load

1. Ask Claude to write a new unit test:
   ```
   Add a test for the cache service in tests/unit/
   ```
2. **Expected**: Claude uses pytest fixtures, `@pytest.mark.asyncio`, and follows Arrange-Act-Assert pattern
3. Ask Claude to modify a security file:
   ```
   Review docs_mcp/security/path_validator.py for issues
   ```
4. **Expected**: Claude specifically checks for directory traversal and input validation

### Step 5: MCP Server Tools Available

1. Start a session and check available tools:
   ```
   What MCP tools do you have available?
   ```
2. **Expected**: Claude lists `search_documentation`, `get_table_of_contents`, `navigate_to`, etc.
3. Ask Claude to search docs:
   ```
   Search the documentation for "security"
   ```
4. **Expected**: Results from `docs/` directory via the MCP server

### Step 6: Session Start Context

1. Start a new session:
   ```bash
   claude
   ```
2. **Expected**: Claude's first response or context includes the current branch name and recent commits
3. On a feature branch, **Expected**: Claude mentions the active spec directory

## Troubleshooting

| Issue | Check |
|-------|-------|
| Hooks not running | Verify `.claude/hooks/*.sh` have executable permission (`chmod +x`) |
| MCP server not starting | Run `your-docs-mcp` manually to check for errors; verify `DOCS_ROOT=./docs` |
| Permissions still prompting | Check `.claude/settings.json` is valid JSON; verify global settings don't override |
| Rules not loading | Verify `paths` in frontmatter match actual file paths being edited |
| notify-send not found | Install: `sudo apt install libnotify-bin` |
