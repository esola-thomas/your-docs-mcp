---
title: MCP Protocol Integration
tags: [architecture, mcp, protocol, tools, resources]
category: Architecture
order: 2
---

# MCP Protocol Integration

The Model Context Protocol (MCP) is a standardized way for AI assistants to interact with external tools and data sources. This document explains how the documentation server implements MCP.

## Protocol Overview

MCP defines three main concepts:

1. **Tools**: Actions the AI can perform (search, navigate, etc.)
2. **Resources**: Data the AI can read (documents, categories)
3. **Transports**: Communication channels (stdio, SSE)

## Available Tools

### search_documentation

Full-text and semantic search across all documentation.

**Parameters:**
- `query` (string, required): Search query
- `category` (string, optional): Filter by category
- `limit` (integer, optional): Max results (default: 10)

**Example:**
```json
{
  "name": "search_documentation",
  "arguments": {
    "query": "authentication",
    "category": "api",
    "limit": 5
  }
}
```

### navigate_to

Navigate to a specific URI in the documentation hierarchy.

**Parameters:**
- `uri` (string, required): URI to navigate to (e.g., `docs://guides/security`)

**Returns:**
- Document content and metadata
- Navigation context (parent, children, siblings)
- Breadcrumb trail

### get_table_of_contents

Get the complete documentation hierarchy as a tree.

**Parameters:**
- `max_depth` (integer, optional): Maximum depth to include

**Returns:**
- Nested tree structure with categories and documents
- Document counts per category

### search_by_tags

Search documentation by metadata tags.

**Parameters:**
- `tags` (array, required): Tags to search for (OR logic)
- `category` (string, optional): Filter by category
- `limit` (integer, optional): Max results

### get_document

Get full content and metadata for a specific document.

**Parameters:**
- `uri` (string, required): Document URI

### get_all_tags

List all unique tags across the documentation.

**Parameters:**
- `category` (string, optional): Filter by category
- `include_counts` (boolean, optional): Include document counts per tag

## Resources

Resources are browsable via their URI scheme:

- `docs://` - Root of documentation
- `docs://guides` - Guides category
- `docs://guides/getting-started` - Specific document
- `docs://api/openapi.yaml` - OpenAPI specification

### Resource Listing

Clients can list available resources at any level:

```python
# List root categories
resources = await client.list_resources()

# Read specific resource
content = await client.read_resource("docs://guides/getting-started")
```

## Transport Mechanisms

### stdio Transport

Default for desktop clients like Claude Desktop:

```json
{
  "mcpServers": {
    "docs": {
      "command": "hierarchical-docs-mcp",
      "env": {
        "DOCS_ROOT": "/path/to/docs"
      }
    }
  }
}
```

### SSE Transport

HTTP-based transport for web clients:

- **Connect**: `GET /sse` - Establish SSE connection
- **Messages**: `POST /messages/?session_id=...` - Send messages

The SSE transport enables the web UI to use the same MCP protocol as desktop clients.

## Error Handling

All tools return consistent error responses:

```json
{
  "error": "document_not_found",
  "message": "No document found at URI: docs://invalid/path",
  "code": 404
}
```

## Security Considerations

1. **Path Validation**: All URIs are validated against path traversal attacks
2. **Input Sanitization**: Query inputs are sanitized before processing
3. **Audit Logging**: All tool calls are logged for debugging

## Implementation Details

The server uses the official MCP Python SDK:

The shared factory in `docs_mcp/mcp/handlers/registry.py` constructs the SDK 2.x low-level
`Server` for stdio and SSE. It registers `on_list_tools`, `on_call_tool`,
`on_list_resources`, and `on_read_resource` constructor callbacks. Callbacks accept
request context and typed parameters, and return explicit MCP result objects.

Tool input schemas are validated with `jsonschema` before dispatch. Raised tool
failures become `CallToolResult(is_error=True)`; missing resources produce a
protocol error. Existing tool payloads remain JSON text and resource content
remains Markdown. SDK fields use snake_case in Python; MCP JSON keeps camelCase.

Documents and categories are shared mutable collections populated during startup.
The category dictionary must be updated in place so registered callbacks see it.

See [MCP SDK 2 migration](../guides/mcp-sdk-v2.md) for installation compatibility.

## Next Steps

- [Vector Database](vector-db.md) - How semantic search works
- [Architecture Overview](overview.md) - System design
- [REST API](../api/rest.md) - Web API reference
