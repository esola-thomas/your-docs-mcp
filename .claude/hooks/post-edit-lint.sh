#!/usr/bin/env bash
# PostToolUse hook: auto-lint Python files after Edit or Write
# Reads tool input JSON from stdin, extracts file_path, runs ruff if .py file
# Always exits 0 — never blocks Claude's workflow

set -o pipefail

# Read JSON from stdin
INPUT=$(cat 2>/dev/null || echo '{}')

# Extract file_path from tool_input (try jq first, fall back to python)
if command -v jq &>/dev/null; then
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
    FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    pass
" 2>/dev/null)
fi

# Skip if no file path or not a Python file
if [[ -z "$FILE_PATH" ]] || [[ "$FILE_PATH" != *.py ]]; then
    exit 0
fi

# Skip if file doesn't exist (may have been a failed write)
if [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Check if ruff is available
if ! command -v ruff &>/dev/null; then
    echo "Warning: ruff not found — skipping auto-lint" >&2
    exit 0
fi

# Run ruff check with auto-fix, then format
ruff check --fix --quiet "$FILE_PATH" 2>/dev/null || true
ruff format --quiet "$FILE_PATH" 2>/dev/null || true

exit 0
