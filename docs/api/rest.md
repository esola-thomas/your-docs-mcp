---
title: REST API Reference
tags: [api, rest, endpoints, reference]
category: API
order: 1
---

# REST API Reference

Complete reference for the web server REST API endpoints.

## Base URL

When running the web server locally:

```text
http://localhost:8080/api
```

## Authentication

The REST API does not require authentication by default. For production deployments, place the server behind a reverse proxy with authentication.

## Endpoints

### Health Check

Check server status.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "documents": 15,
  "categories": 4
}
```

### Search Documentation

Full-text and semantic search across all documentation.

**Endpoint:** `GET /api/search`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `category` | string | No | Filter by category |
| `limit` | integer | No | Max results (default: 10) |

**Example Request:**
```bash
curl "http://localhost:8080/api/search?query=authentication&limit=5"
```

**Example Response:**
```json
{
  "results": [
    {
      "uri": "docs://api/authentication",
      "title": "API Authentication",
      "excerpt": "Learn how to authenticate with the API...",
      "breadcrumbs": ["API", "Authentication"],
      "relevance": 0.95,
      "tags": ["api", "authentication", "security"]
    }
  ]
}
```

### Get Table of Contents

Get the complete documentation hierarchy.

**Endpoint:** `GET /api/toc`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `max_depth` | integer | No | Maximum depth to include |

**Example Request:**
```bash
curl "http://localhost:8080/api/toc"
```

**Example Response:**
```json
{
  "name": "Documentation",
  "type": "root",
  "children": [
    {
      "name": "Guides",
      "type": "category",
      "document_count": 5,
      "children": [
        {
          "name": "Getting Started",
          "type": "document",
          "uri": "docs://guides/getting-started"
        }
      ]
    }
  ]
}
```

### Get Document

Retrieve a specific document by URI.

**Endpoint:** `GET /api/document`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `uri` | string | Yes | Document URI |

**Example Request:**
```bash
curl "http://localhost:8080/api/document?uri=docs://guides/getting-started"
```

**Example Response:**
```json
{
  "uri": "docs://guides/getting-started",
  "title": "Getting Started Guide",
  "content": "# Getting Started...",
  "category": "Guides",
  "tags": ["guide", "quickstart"],
  "breadcrumbs": ["Guides", "Getting Started"]
}
```

### Navigate

Navigate to a URI and get navigation context.

**Endpoint:** `GET /api/navigate`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `uri` | string | Yes | URI to navigate to |

**Example Response:**
```json
{
  "current": {
    "uri": "docs://guides",
    "name": "Guides",
    "type": "category"
  },
  "parent": {
    "uri": "docs://",
    "name": "Documentation"
  },
  "children": [
    {
      "uri": "docs://guides/getting-started",
      "name": "Getting Started",
      "type": "document"
    }
  ],
  "breadcrumbs": ["Documentation", "Guides"]
}
```

### Get All Tags

List all unique tags in the documentation.

**Endpoint:** `GET /api/tags`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `category` | string | No | Filter by category |
| `include_counts` | boolean | No | Include document counts |

**Example Request:**
```bash
curl "http://localhost:8080/api/tags?include_counts=true"
```

**Example Response:**
```json
{
  "tags": ["api", "authentication", "guide", "setup"],
  "count": 4,
  "tag_counts": [
    {"tag": "api", "document_count": 3},
    {"tag": "authentication", "document_count": 2},
    {"tag": "guide", "document_count": 5},
    {"tag": "setup", "document_count": 2}
  ]
}
```

### Search by Tags

Search documentation by metadata tags.

**Endpoint:** `POST /api/search-by-tags`

**Request Body:**
```json
{
  "tags": ["api", "authentication"],
  "category": "API",
  "limit": 10
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8080/api/search-by-tags" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["api", "authentication"]}'
```

**Example Response:**
```json
{
  "results": [
    {
      "uri": "docs://api/authentication",
      "title": "API Authentication",
      "tags": ["api", "authentication", "security"],
      "relevance": 1.0
    }
  ]
}
```

## MCP SSE Transport

The server also provides MCP protocol access via Server-Sent Events.

### Connect

**Endpoint:** `GET /sse`

Establishes an SSE connection for MCP communication. The server sends an `endpoint` event with the URL for posting messages.

### Send Messages

**Endpoint:** `POST /messages/?session_id=<session_id>`

Send MCP protocol messages. The session_id is provided in the initial SSE connection.

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "detail": "Additional details"
}
```

### Common Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| 400 | `bad_request` | Invalid parameters |
| 404 | `not_found` | Resource not found |
| 500 | `internal_error` | Server error |

## Rate Limiting

The server does not impose rate limits by default. For production deployments, configure rate limiting in your reverse proxy.

## CORS

Cross-Origin Resource Sharing (CORS) is enabled for all origins to support web-based MCP clients.

## Next Steps

- [MCP Protocol](../architecture/mcp-protocol.md) - MCP tool specifications
- [Configuration](../guides/quickstart/configuration.md) - Server configuration
- [CLI Reference](../reference/cli-commands.md) - Command line options
