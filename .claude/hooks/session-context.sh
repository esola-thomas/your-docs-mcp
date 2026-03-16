#!/usr/bin/env bash
# SessionStart hook: inject project context at session start
# Outputs current branch, recent commits, and active feature spec
# Always exits 0 — never blocks session initialization

# Check if we're in a git repository
if ! git rev-parse --git-dir &>/dev/null 2>&1; then
    echo "Not a git repository — skipping session context"
    exit 0
fi

# Current branch
BRANCH=$(git branch --show-current 2>/dev/null || echo "detached HEAD")
echo "Branch: $BRANCH"

# Recent commits (last 5)
echo "Recent commits:"
git log --oneline -5 2>/dev/null | sed 's/^/  /' || echo "  (no commits)"

# Detect active feature spec from branch name
if [[ "$BRANCH" =~ ^[0-9]+-.*$ ]]; then
    SPEC_DIR=$(find specs/ -maxdepth 1 -name "${BRANCH}" -type d 2>/dev/null | head -1)
    if [[ -n "$SPEC_DIR" ]]; then
        echo "Active spec: $SPEC_DIR/"
        # Show spec status if tasks.md exists
        if [[ -f "$SPEC_DIR/tasks.md" ]]; then
            TOTAL=$(grep -cE '^\- \[[ xX]\]' "$SPEC_DIR/tasks.md" 2>/dev/null || echo 0)
            DONE=$(grep -ciE '^\- \[x\]' "$SPEC_DIR/tasks.md" 2>/dev/null || echo 0)
            echo "Task progress: $DONE/$TOTAL completed"
        fi
    fi
fi

exit 0
