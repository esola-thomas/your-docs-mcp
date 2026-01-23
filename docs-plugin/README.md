# Documentation Skills Plugin

Claude Code skills for managing documentation files in your-docs-mcp projects.

## Quick Start

### 1. Install the Plugin

```bash
claude --plugin-dir /path/to/your-docs-mcp/docs-plugin
```

Or add to your Claude Code plugin marketplace config to install permanently.

### 2. Use the Skills

| Skill | What it does |
|-------|--------------|
| `/docs-mcp:doc-create` | Create a new doc file |
| `/docs-mcp:doc-validate` | Check docs for issues |
| `/docs-mcp:doc-template` | Get a starter template |
| `/docs-mcp:doc-lint` | Quick check one file |
| `/docs-mcp:doc-search` | Find docs by content |
| `/docs-mcp:doc-preview` | See doc structure |
| `/docs-mcp:doc-toc` | Generate table of contents |
| `/docs-mcp:doc-frontmatter` | Fix missing metadata |

## Examples

```bash
# Create a new guide
/docs-mcp:doc-create docs/guides/deployment.md --type guide

# Validate all documentation
/docs-mcp:doc-validate docs/

# Generate an API doc template
/docs-mcp:doc-template api "search_documents"

# Search for authentication docs
/docs-mcp:doc-search authentication --tag security
```

## Documentation Format

All docs need YAML frontmatter:

```markdown
---
title: "Your Title"
category: "Guides"
tags: ["setup", "beginner"]
order: 1
---

# Your Title

Content here...
```

## Related

- [Main MCP Server](https://github.com/esola-thomas/your-docs-mcp) - The documentation MCP server
- [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills) - Learn more about skills
