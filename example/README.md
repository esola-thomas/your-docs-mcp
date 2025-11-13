---
title: "Example Documentation Structure"
category: "Documentation"
tags: ["example", "template", "structure"]
order: 1
description: "Complete example showing how to structure documentation for the MCP server"
---

# Example Documentation Structure

This folder demonstrates how to structure your documentation for use with the
Hierarchical Documentation MCP server.

## Overview

This is a complete, working example that you can use as a template for your
own documentation. You can:

- Copy this entire folder to use as a starting point
- Point your DOCS_ROOT environment variable to this folder to test the MCP
  server
- Modify the structure to match your project's needs

## Directory Structure

```text
example/
├── README.md                    # This file - explains the structure
├── guides/                      # User guides and tutorials
│   ├── quickstart/             # Nested category for quickstart guides
│   │   └── installation.md     # Installation guide
│   ├── configuration.md        # Configuration guide
│   └── advanced/               # Advanced guides
│       └── performance.md      # Performance optimization guide
├── api/                        # API documentation
│   ├── authentication.md       # API authentication docs
│   ├── endpoints.md            # API endpoints reference
│   └── openapi.yaml           # Optional: OpenAPI 3.x specification
└── reference/                  # Reference documentation
    └── cli-commands.md         # CLI reference
```

## Markdown File Format

Each markdown file should include YAML frontmatter with metadata:

```markdown
---
title: Your Document Title
tags: [tag1, tag2, tag3]
category: category-name
order: 1
---

# Your Document Title

Your content here...
```

## Frontmatter Fields

- **title** (required): The display title for the document
- **tags** (optional): Array of tags for searchability and filtering
- **category** (optional): Category for grouping related documents
- **order** (optional): Number to control ordering within a category (lower = earlier)

## Categories and Hierarchy

Categories are automatically created based on:
1. Directory structure (e.g., `guides/`, `api/`, `reference/`)
2. Nested directories (e.g., `guides/advanced/` creates a subcategory)
3. The `category` field in frontmatter

Documents are organized hierarchically using the `docs://` URI scheme:
- Root: `docs://`
- Category: `docs://guides`
- Nested category: `docs://guides/advanced`
- Document: `docs://guides/configuration`

## OpenAPI Support

You can include OpenAPI 3.x specifications (`.yaml` or `.json` files) in any
directory. These will be automatically parsed and made available through the
MCP server.

## Testing This Example

To test this example with the MCP server:

1. Set the DOCS_ROOT to this folder:
   ```bash
   export DOCS_ROOT=/path/to/Markdown-MCP/example
   ```

2. Start the MCP server:
   ```bash
   hierarchical-docs-mcp
   ```

3. Ask your AI assistant:
  - "List all available documentation"
  - "Show me the getting started guide"
  - "Search for authentication"
  - "What API endpoints are available?"

## Customizing for Your Project

1. **Keep the structure**: Use the category/subcategory pattern shown here
2. **Add frontmatter**: Include title, tags, and category in all markdown files
3. **Order documents**: Use the `order` field to control document sequence
4. **Nest logically**: Group related documents in subdirectories
5. **Tag consistently**: Use consistent tags across documents for better searchability

## Tips

- Use descriptive file names (they become part of the URI)
- Keep category names short and clear
- Add plenty of tags for discoverability
- Use the `order` field to create guided learning paths
- Include code examples in markdown files
- Link between documents using relative paths or docs:// URIs
