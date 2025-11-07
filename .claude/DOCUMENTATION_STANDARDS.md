# Documentation Standards

This guide defines the standards and best practices for creating and maintaining documentation in the Hierarchical Documentation MCP Server project.

## Table of Contents

1. [File Structure](#file-structure)
2. [YAML Frontmatter](#yaml-frontmatter)
3. [Markdown Formatting](#markdown-formatting)
4. [Content Guidelines](#content-guidelines)
5. [Code Examples](#code-examples)
6. [Links and References](#links-and-references)
7. [Validation](#validation)

## File Structure

### Directory Organization

```
docs/
├── guides/                    # User guides and tutorials
│   ├── getting-started.md
│   ├── security/             # Security-related guides
│   └── configuration/        # Configuration guides
├── api/                      # API documentation
├── architecture/             # Architecture documentation
└── config-examples/          # Configuration file examples
```

### Naming Conventions

- **File names**: Use lowercase with hyphens (kebab-case)
  - ✅ `getting-started.md`
  - ✅ `authentication.md`
  - ❌ `GettingStarted.md`
  - ❌ `getting_started.md`

- **Directory names**: Use lowercase with hyphens
  - ✅ `security/`
  - ✅ `api-reference/`
  - ❌ `Security/`

## YAML Frontmatter

All documentation files **MUST** include YAML frontmatter at the beginning of the file.

### Required Format

```markdown
---
title: "Document Title"
category: "Category Name"
tags: ["tag1", "tag2", "tag3"]
order: 1
---
```

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Human-readable title | `"Getting Started"` |
| `category` | string | Primary category | `"Guides"` |
| `tags` | array | Searchable tags | `["beginner", "setup"]` |
| `order` | integer | Display order (0-based) | `1` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `parent` | string | Parent document path | `"guides/index"` |
| `description` | string | Brief description | `"Learn how to install and configure"` |
| `author` | string | Document author | `"Engineering Team"` |
| `updated` | date | Last update date | `2024-03-15` |
| `version` | string | Applies to version | `"0.1.0"` |

### Example Frontmatter

```yaml
---
title: "Authentication Guide"
category: "Security"
tags: ["security", "authentication", "api"]
order: 2
parent: "guides/security/index"
description: "Learn how to implement authentication for the MCP server"
author: "Security Team"
updated: 2024-03-15
version: "0.1.0"
---
```

## Markdown Formatting

### Headers

- Use ATX-style headers (`#` syntax)
- Include a space after the `#`
- Use title case for level 1 and 2 headers
- Use sentence case for level 3+ headers

```markdown
# Main Title (H1)

## Section Title (H2)

### Subsection title (H3)

#### Detail subsection (H4)
```

### Line Length

- Maximum line length: **100 characters**
- Break lines at logical points (after punctuation, before conjunctions)
- Exception: URLs, code blocks, and tables can exceed this limit

### Lists

**Unordered Lists:**
- Use `-` for bullet points
- Use 2-space indentation for nested items
- Add blank line before and after lists

```markdown
Some text here.

- First item
- Second item
  - Nested item
  - Another nested item
- Third item

More text here.
```

**Ordered Lists:**
- Use `1.` for all items (auto-numbering)
- Maintain consistency in formatting

```markdown
1. First step
1. Second step
1. Third step
```

### Emphasis

- **Bold**: Use `**text**` for strong emphasis
- *Italic*: Use `*text*` for emphasis
- `Code`: Use backticks for inline code, commands, file names, and variable names
- ~~Strikethrough~~: Use `~~text~~` sparingly

### Tables

- Use pipes (`|`) to create tables
- Include header separator row
- Align columns for readability in source

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

## Content Guidelines

### Writing Style

1. **Clarity**: Write clear, concise sentences
2. **Active Voice**: Prefer active over passive voice
3. **Present Tense**: Use present tense for descriptions
4. **Second Person**: Address readers as "you"
5. **Consistency**: Maintain consistent terminology

### Structure

Every documentation page should include:

1. **Title** (H1): One per document
2. **Introduction**: Brief overview (2-3 sentences)
3. **Table of Contents**: For documents longer than 3 sections
4. **Body**: Organized into logical sections
5. **Examples**: Practical code examples where applicable
6. **Related Resources**: Links to related documentation

### Examples Structure

```markdown
# Document Title

Brief introduction explaining what this document covers and who should read it.

## Table of Contents

1. [Section 1](#section-1)
2. [Section 2](#section-2)
3. [Examples](#examples)

## Section 1

Content here...

## Section 2

Content here...

## Examples

Practical examples here...

## Related Resources

- [Related Doc 1](./related-doc-1.md)
- [Related Doc 2](./related-doc-2.md)
```

## Code Examples

### Code Blocks

- **Always** specify the language for syntax highlighting
- Include descriptive comments
- Show both input and expected output when applicable
- Use complete, runnable examples when possible

```markdown
​```python
# Example: Loading configuration
from hierarchical_docs_mcp.config import ServerConfig

config = ServerConfig(
    docs_root="/path/to/docs",
    cache_enabled=True
)
​```
```

### Inline Code

Use inline code for:
- File paths: `config.py`
- Environment variables: `DOCS_ROOT`
- Command names: `pytest`
- Function/class names: `ServerConfig`
- Configuration keys: `cache_enabled`

### Configuration Examples

For configuration files, show complete working examples:

```markdown
​```json
{
  "mcpServers": {
    "hierarchical-docs": {
      "command": "hierarchical-docs-mcp",
      "args": ["--docs-root", "/path/to/docs"]
    }
  }
}
​```
```

### Shell Commands

Show commands with prompt prefix `$`:

```markdown
​```bash
$ pip install hierarchical-docs-mcp
$ hierarchical-docs-mcp --help
​```
```

## Links and References

### Internal Links

- Use relative paths for internal documentation
- Include `.md` extension
- Verify links are valid

```markdown
See [Getting Started](./getting-started.md) for installation instructions.
See [Authentication](./security/authentication.md) for security details.
```

### External Links

- Use descriptive link text (not "click here")
- Open external links are handled by the reader

```markdown
✅ See the [MCP Protocol documentation](https://modelcontextprotocol.io/) for details.
❌ Click [here](https://modelcontextprotocol.io/) for MCP docs.
```

### Reference-Style Links

For multiple references to the same URL:

```markdown
See the [official docs][mcp-docs] and the [protocol spec][mcp-docs].

[mcp-docs]: https://modelcontextprotocol.io/
```

## Validation

### Pre-Commit Checks

Before committing documentation:

1. **Frontmatter**: Verify YAML frontmatter is valid and complete
2. **Markdown**: Check markdown syntax
3. **Links**: Verify all internal links resolve
4. **Code**: Test code examples compile/run
5. **Spelling**: Run spell check
6. **Line Length**: Ensure lines ≤ 100 characters

### Validation Script

Run the validation script:

```bash
$ python scripts/validate_docs.py
```

This checks:
- ✅ YAML frontmatter validity
- ✅ Required fields present
- ✅ Markdown syntax
- ✅ Internal link validity
- ✅ Code block language tags
- ✅ Line length limits

### CI/CD Integration

Documentation validation runs automatically on:
- Pull requests to main/master
- Pushes to documentation branches

Fix any validation errors before requesting review.

## Common Patterns

### API Documentation

```markdown
---
title: "search_documents Tool"
category: "API Reference"
tags: ["api", "tools", "search"]
order: 1
---

# search_documents

Search through documentation using full-text search with metadata filtering.

## Signature

​```python
async def search_documents(
    query: str,
    tags: Optional[List[str]] = None,
    category: Optional[str] = None,
    limit: int = 10
) -> List[Document]
​```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | Yes | Search query string |
| `tags` | List[str] | No | Filter by tags |
| `category` | str | No | Filter by category |
| `limit` | int | No | Max results (default: 10) |

## Returns

List of `Document` objects matching the search criteria.

## Example

​```python
results = await search_documents(
    query="authentication",
    tags=["security"],
    limit=5
)
​```
```

### Tutorial Documentation

```markdown
---
title: "Getting Started with Hierarchical Docs MCP"
category: "Guides"
tags: ["tutorial", "beginner", "setup"]
order: 1
---

# Getting Started

This guide walks you through installing and configuring the Hierarchical Docs MCP Server.

## Prerequisites

Before you begin, ensure you have:

- Python 3.11 or 3.12
- pip package manager
- A Claude Desktop or MCP-compatible client

## Installation

### Step 1: Install the package

​```bash
$ pip install hierarchical-docs-mcp
​```

### Step 2: Verify installation

​```bash
$ hierarchical-docs-mcp --version
​```

## Configuration

[Continue with detailed steps...]
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-03-15 | Initial documentation standards |

## Questions?

If you have questions about these standards, please:

1. Check existing documentation for examples
2. Review the [Contributing Guide](../.github/CONTRIBUTING.md)
3. Ask in pull request reviews
