---
title: Architecture Overview
tags: [architecture, design, system, mcp]
category: Architecture
order: 1
---

# Architecture Overview

The Hierarchical Documentation MCP server is designed as a modular, extensible system for serving documentation to AI assistants via the Model Context Protocol (MCP).

## Core Design Principles

### 1. Library-First Architecture

The system is built as a collection of self-contained, independently testable modules:

- **Models**: Data structures for documents, navigation, and OpenAPI specs
- **Services**: Business logic for caching, hierarchy, markdown parsing, search, and vector storage
- **Handlers**: MCP protocol handlers for tools and resources
- **Security**: Path validation, input sanitization, and audit logging

### 2. Protocol Compliance

Strict adherence to the MCP specification ensures compatibility with any MCP-compliant client:

- Tools for search, navigation, and document retrieval
- Resources for browsing the documentation hierarchy
- SSE transport for web-based clients

### 3. Performance & Observability

- Intelligent caching with configurable TTL
- Vector-based semantic search using ChromaDB
- Structured logging for debugging and monitoring

## System Components

```text
┌─────────────────────────────────────────────────────────┐
│                    MCP Clients                          │
│         (Claude Desktop, VS Code, Web UI)               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   MCP Server                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Tools     │  │  Resources  │  │  SSE Transport  │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          ▼                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │                   Services                        │  │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐  │  │
│  │  │ Search  │ │ Hierarchy│ │ Cache  │ │ Vector │  │  │
│  │  └─────────┘ └──────────┘ └────────┘ └────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                          │                              │
│                          ▼                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │                   Models                          │  │
│  │      Document  │  Navigation  │  OpenAPI         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  File System                            │
│              (DOCS_ROOT directory)                      │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Document Loading

1. Server starts and scans `DOCS_ROOT` for markdown files and OpenAPI specs
2. Files are parsed, extracting frontmatter metadata and content
3. Documents are indexed for full-text and semantic search
4. Category hierarchy is built from directory structure

### Search Flow

1. Client sends search query via MCP tool
2. Hybrid search combines keyword and vector similarity
3. Results are ranked by relevance score
4. Cached results returned for repeated queries

### Navigation Flow

1. Client navigates to a URI (e.g., `docs://guides/getting-started`)
2. Server resolves URI to document or category
3. Context (parent, children, breadcrumbs) is assembled
4. Response includes navigation aids and content

## Configuration

The server is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCS_ROOT` | Documentation directory | Required |
| `MCP_DOCS_CACHE_TTL` | Cache TTL in seconds | 3600 |
| `MCP_DOCS_SEARCH_LIMIT` | Max search results | 10 |
| `LOG_LEVEL` | Logging level | INFO |

## Next Steps

- [MCP Protocol](mcp-protocol.md) - Protocol details and tool specifications
- [Vector Database](vector-db.md) - Semantic search implementation
- [Getting Started](../guides/getting-started.md) - Quick setup guide
