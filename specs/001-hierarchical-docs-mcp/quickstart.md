# Quickstart Guide: Hierarchical Documentation MCP Server

**Feature**: Hierarchical Documentation MCP Server  
**Date**: November 4, 2025  
**Audience**: Developers integrating the MCP server with AI assistants

## Overview

The Hierarchical Documentation MCP Server enables AI assistants (Claude Desktop, GitHub Copilot) to navigate and query documentation through a structured, hierarchical interface. It supports markdown files with YAML frontmatter and OpenAPI 3.x specifications.

**Key Capabilities**:
- 📁 Hierarchical navigation with breadcrumb context
- 🔍 Full-text and metadata-based search
- 📖 Markdown parsing with frontmatter support
- 🔌 OpenAPI 3.x integration
- 🔒 Security validation (path traversal prevention)
- 💨 Intelligent caching with file watching
- 🌐 Cross-platform (Claude Desktop, VS Code/Copilot)

---

## Prerequisites

- **Python**: 3.11 or higher
- **AI Assistant**: Claude Desktop or VS Code with GitHub Copilot
- **Documentation**: Markdown files or OpenAPI specs to serve

---

## Installation

### Option 1: Install from PyPI (when published)

```bash
pip install hierarchical-docs-mcp
```

### Option 2: Install from source

```bash
git clone https://github.com/your-org/hierarchical-docs-mcp
cd hierarchical-docs-mcp
pip install -e .
```

### Option 3: Use with pipx (isolated environment)

```bash
pipx install hierarchical-docs-mcp
```

---

## Quick Start (5 minutes)

### Step 1: Prepare Your Documentation

Create a simple documentation structure:

```bash
mkdir -p ~/my-docs/guides
mkdir -p ~/my-docs/api

# Create sample markdown file
cat > ~/my-docs/guides/getting-started.md <<EOF
---
title: Getting Started
tags: [tutorial, beginner]
category: guides
---

# Getting Started

Welcome to the documentation!
EOF
```

### Step 2: Configure for Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "hierarchical-docs": {
      "command": "python",
      "args": ["-m", "hierarchical_docs_mcp"],
      "env": {
        "DOCS_ROOT": "/Users/yourname/my-docs"
      }
    }
  }
}
```

**Linux**: `~/.config/Claude/claude_desktop_config.json`

### Step 3: Configure for VS Code/Copilot

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "hierarchical-docs": {
      "command": "python",
      "args": ["-m", "hierarchical_docs_mcp"],
      "env": {
        "DOCS_ROOT": "${workspaceFolder}/docs"
      }
    }
  }
}
```

### Step 4: Restart Your AI Assistant

- **Claude Desktop**: Quit and relaunch the application
- **VS Code**: Reload window (`Cmd/Ctrl + Shift + P` → "Reload Window")

### Step 5: Test the Connection

Ask your AI assistant:

```
"List all available documentation"
```

Expected response: AI will use the MCP to list your documentation categories.

```
"Show me the getting started guide"
```

Expected response: AI will navigate to and present the guide content.

---

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DOCS_ROOT` | Path to documentation root | `./docs` | ✅ Yes |
| `MCP_DOCS_CACHE_TTL` | Cache TTL in seconds | `3600` | No |
| `MCP_DOCS_MAX_DEPTH` | Max hierarchy depth | `10` | No |
| `MCP_DOCS_ENABLE_FILE_WATCHING` | Auto-invalidate cache on changes | `true` | No |

### Configuration File (Advanced)

Create `.mcp-docs.yaml` in your documentation root:

```yaml
sources:
  - path: ./guides
    category: guides
    label: User Guides
    recursive: true
    include_patterns:
      - "*.md"
      - "*.mdx"
    exclude_patterns:
      - "node_modules"
      - ".git"
      - "_*"

  - path: ./api-reference
    category: api-reference
    label: API Reference
    recursive: true

openapi_specs:
  - ./specs/api-v1.yaml
  - ./specs/api-v2.yaml

cache_ttl: 3600  # 1 hour
max_depth: 10
enable_file_watching: true
```

---

## Usage Examples

### Example 1: Basic Navigation

**User asks Claude/Copilot:**
> "What documentation is available?"

**AI uses MCP to:**
1. Call `get_table_of_contents()` tool
2. Present hierarchical structure with categories

**Response:**
```
I can see the following documentation:

📁 Guides (5 documents)
  - Getting Started
  - Security → Authentication
  - Security → Authorization
  - Deployment
  
📁 API Reference (12 endpoints)
  - Users API
  - Authentication API
```

---

### Example 2: Searching Documentation

**User asks:**
> "How do I authenticate users?"

**AI uses MCP to:**
1. Call `search_documentation(query="authenticate users")`
2. Get results with hierarchical context

**Response:**
```
I found authentication information in:

1. Guides > Security > Authentication
   "Learn how to authenticate users using OAuth2..."
   
2. API Reference > Auth Endpoints
   "POST /auth/login - Authenticate a user and receive tokens"
```

---

### Example 3: API Discovery

**User asks:**
> "What endpoints are available for user management?"

**AI uses MCP to:**
1. Call `list_api_endpoints(tag="users")`
2. Present structured endpoint list

**Response:**
```
User Management API endpoints:

GET    /users          - List all users
GET    /users/{id}     - Get user details
POST   /users          - Create new user
PUT    /users/{id}     - Update user
DELETE /users/{id}     - Delete user
```

---

### Example 4: Metadata-Based Search

**User asks:**
> "Show me all beginner tutorials"

**AI uses MCP to:**
1. Call `search_by_metadata(tags=["beginner", "tutorial"])`
2. Return matching documents

**Response:**
```
Beginner tutorials:

1. Getting Started (guides)
2. Your First API Call (api-reference)
3. Basic Configuration (guides/setup)
```

---

## Testing Your Setup

### Test 1: Verify Server Running

Check MCP server logs in Claude Desktop:
- **View → Developer → Developer Tools → Console**
- Look for `[hierarchical-docs] Server initialized`

### Test 2: Manual Tool Invocation

Use MCP Inspector for debugging:

```bash
npx @modelcontextprotocol/inspector python -m hierarchical_docs_mcp
```

Opens web UI to test tools interactively.

### Test 3: Query Performance

Ask AI to search large documentation set:
```
"Search for 'authentication' across all docs"
```

Should complete in <3 seconds (per success criteria SC-002).

---

## Troubleshooting

### Issue: "MCP server not found"

**Symptoms**: AI doesn't recognize documentation queries

**Solutions**:
1. Verify configuration file path is correct
2. Check `command` points to correct Python executable
3. Restart AI assistant after configuration changes
4. Check Claude Desktop Developer Console for errors

---

### Issue: "Path not found" errors

**Symptoms**: AI can't access documentation files

**Solutions**:
1. Verify `DOCS_ROOT` path is absolute
2. Check file permissions (must be readable)
3. Ensure no typos in path (case-sensitive on Linux/macOS)
4. Test path in terminal: `ls "$DOCS_ROOT"`

---

### Issue: Search returns no results

**Symptoms**: AI says "No documentation found"

**Solutions**:
1. Verify markdown files have `.md` or `.mdx` extension
2. Check files aren't hidden (don't start with `.`)
3. Verify files aren't excluded by patterns
4. Try: `"List all available documentation"` to see what's indexed

---

### Issue: OpenAPI endpoints not showing

**Symptoms**: API documentation not accessible

**Solutions**:
1. Verify OpenAPI spec is valid (use validator: `openapi-spec-validator spec.yaml`)
2. Check spec version is 3.0.x or 3.1.x (not Swagger 2.0)
3. Ensure spec path in config is correct
4. Check spec has `operationId` for each operation

---

### Issue: Slow performance

**Symptoms**: Queries take >3 seconds

**Solutions**:
1. Check documentation set size (>10GB may exceed specs)
2. Verify cache is enabled (`MCP_DOCS_ENABLE_FILE_WATCHING=true`)
3. Increase cache TTL: `MCP_DOCS_CACHE_TTL=7200`
4. Check for file watching errors in logs

---

## Security Best Practices

### ✅ DO:
- Use absolute paths for `DOCS_ROOT`
- Keep documentation in dedicated directories
- Use `.mcp-docs.yaml` for complex configurations
- Review OpenAPI descriptions before loading
- Monitor audit logs for suspicious access patterns

### ❌ DON'T:
- Point `DOCS_ROOT` at system directories (`/`, `/etc`, `/home`)
- Include sensitive files in documentation directories
- Disable file watching in production (cache staleness)
- Load untrusted OpenAPI specifications
- Ignore security violation warnings in logs

---

## Next Steps

### Add More Documentation Sources

```yaml
# .mcp-docs.yaml
sources:
  - path: ./guides
    category: guides
    label: User Guides
    
  - path: ../other-repo/docs
    category: external
    label: External Documentation
```

### Integrate OpenAPI Specs

```yaml
openapi_specs:
  - ./specs/rest-api.yaml
  - ./specs/graphql-api.yaml
```

### Customize Frontmatter

```markdown
---
title: Advanced Security
tags: [security, advanced, oauth]
category: guides
order: 10
parent: security-overview
custom_field: value
---

# Your content here
```

### Add to CI/CD

Test MCP integration in CI:

```bash
# .github/workflows/docs-mcp.yml
- name: Test MCP Server
  run: |
    pip install hierarchical-docs-mcp pytest
    pytest tests/integration/test_mcp_protocol.py
```

---

## Support & Resources

- **Documentation**: https://github.com/your-org/hierarchical-docs-mcp/docs
- **Issues**: https://github.com/your-org/hierarchical-docs-mcp/issues
- **Examples**: https://github.com/your-org/hierarchical-docs-mcp/examples
- **MCP Specification**: https://spec.modelcontextprotocol.io

---

## FAQ

**Q: Can I use with other AI assistants?**  
A: Yes, any AI assistant supporting MCP can use this server (Anthropic Claude, GitHub Copilot, etc.)

**Q: Does it work with remote documentation?**  
A: Yes, configure HTTP transport for remote server deployment (see advanced configuration)

**Q: Can AI modify documentation?**  
A: No, this MCP is read-only for security. Use separate tools for documentation editing.

**Q: What markdown features are supported?**  
A: All standard markdown, code blocks, tables, and YAML frontmatter metadata.

**Q: How big can documentation sets be?**  
A: Tested up to 10GB with 10,000+ files. Performance optimized for <5,000 documents.

**Q: Does it work offline?**  
A: Yes, fully offline capable when using local documentation with stdio transport.

---

## Quickstart Summary

1. ✅ Install: `pip install hierarchical-docs-mcp`
2. ✅ Configure: Add to Claude Desktop or VS Code config
3. ✅ Set `DOCS_ROOT` environment variable
4. ✅ Restart AI assistant
5. ✅ Test: "List all available documentation"

**Time to first query: ~5 minutes** ⚡

---

**Ready for Production?** See [Security Guide](./security.md) and [Performance Tuning](./performance.md) for production deployment best practices.
