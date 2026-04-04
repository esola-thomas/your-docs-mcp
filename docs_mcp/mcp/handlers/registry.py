"""Shared MCP handler registration for both stdio and SSE transports.

Provides a single source of truth for tool definitions, tool dispatch,
resource listing, and resource reading — used by both DocumentationMCPServer
(stdio) and DocumentationWebServer (SSE).
"""

import json
from pathlib import Path
from typing import Any, cast

from mcp.server import Server
from mcp.types import Resource, Tool

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.core.utils.logger import logger
from docs_mcp.mcp.handlers import resources, tools


def get_tool_definitions(*, enable_pdf: bool = False) -> list[Tool]:
    """Return the canonical list of MCP tool definitions.

    These definitions are shared across all transports (stdio, SSE).

    Args:
        enable_pdf: Whether to include the generate_pdf_release tool.
    """
    tools_list = [
        Tool(
            name="search_documentation",
            description=(
                "Search documentation with full-text search. "
                "Returns results with hierarchical context (breadcrumbs)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category to filter results",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="navigate_to",
            description=(
                "Navigate to a specific URI in the documentation hierarchy. "
                "Returns navigation context with parent, children, and breadcrumbs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "URI to navigate to (e.g., 'docs://guides/security')",
                    },
                },
                "required": ["uri"],
            },
        ),
        Tool(
            name="get_table_of_contents",
            description=("Get the complete documentation hierarchy as a table of contents tree."),
            inputSchema={
                "type": "object",
                "properties": {
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to include (optional)",
                    },
                },
            },
        ),
        Tool(
            name="search_by_tags",
            description="Search documentation by metadata tags and category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to search for (OR logic)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category to filter by",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 10,
                    },
                },
                "required": ["tags"],
            },
        ),
        Tool(
            name="get_document",
            description="Get full content and metadata for a specific document by URI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "Document URI (e.g., 'docs://guides/getting-started')",
                    },
                },
                "required": ["uri"],
            },
        ),
        Tool(
            name="get_all_tags",
            description=(
                "Get a list of all unique tags defined across the documentation. "
                "Optionally filter by category and include document counts per tag."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category to filter tags from",
                    },
                    "include_counts": {
                        "type": "boolean",
                        "description": "Include document count for each tag (default: false)",
                        "default": False,
                    },
                },
            },
        ),
    ]

    if enable_pdf:
        tools_list.append(
            Tool(
                name="generate_pdf_release",
                description=(
                    "Generate a PDF documentation release. Creates a formatted PDF "
                    "with all documentation, table of contents, and optional "
                    "confidentiality markings (watermark, headers, footers)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Document title. Defaults to project name.",
                        },
                        "subtitle": {
                            "type": "string",
                            "description": "Document subtitle (optional).",
                        },
                        "author": {
                            "type": "string",
                            "description": "Document author. Defaults to 'Documentation Team'.",
                        },
                        "version": {
                            "type": "string",
                            "description": (
                                "Version string for the release (e.g., '2.0.0'). "
                                "Defaults to current date."
                            ),
                        },
                        "confidential": {
                            "type": "boolean",
                            "description": (
                                "Add confidentiality markings (watermark, headers, footers). "
                                "Default: false"
                            ),
                            "default": False,
                        },
                        "owner": {
                            "type": "string",
                            "description": (
                                "Copyright owner (shown when confidential=true). "
                                "Defaults to project name."
                            ),
                        },
                    },
                },
            )
        )

    return tools_list


def register_mcp_handlers(
    server: Server,
    documents: list[Document],
    categories: dict[str, Category],
    config: ServerConfig,
) -> None:
    """Register all MCP protocol handlers on a Server instance.

    Closures capture documents/categories by reference so they see
    data populated later by initialize().

    Args:
        server: MCP Server instance (stdio or SSE transport)
        documents: Mutable list of loaded documents
        categories: Mutable dict of category tree
        config: Server configuration
    """

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return get_tool_definitions(enable_pdf=config.enable_pdf_generation)

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[Any]:
        logger.info(f"Tool call: {name}")

        if name == "search_documentation":
            results = await tools.handle_search_documentation(
                arguments, documents, categories, config.search_limit
            )
            return [{"type": "text", "text": json.dumps(results, indent=2)}]

        elif name == "navigate_to":
            result = await tools.handle_navigate_to(arguments, documents, categories)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        elif name == "get_table_of_contents":
            result = await tools.handle_get_table_of_contents(arguments, documents, categories)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        elif name == "search_by_tags":
            results = await tools.handle_search_by_tags(arguments, documents, config.search_limit)
            return [{"type": "text", "text": json.dumps(results, indent=2)}]

        elif name == "get_document":
            result = await tools.handle_get_document(arguments, documents)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        elif name == "get_all_tags":
            result = await tools.handle_get_all_tags(arguments, documents)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        elif name == "generate_pdf_release":
            if not config.enable_pdf_generation:
                raise ValueError(
                    "PDF generation is disabled. Set MCP_DOCS_ENABLE_PDF_GENERATION=true to enable."
                )
            result = await tools.handle_generate_pdf_release(arguments, Path(config.docs_root))
            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        else:
            raise ValueError(f"Unknown tool: {name}")

    @server.list_resources()
    async def list_resources_handler() -> list[Resource]:
        resource_list = await resources.list_resources(documents, categories)
        return [
            Resource(
                uri=r["uri"],
                name=r["name"],
                mimeType=r.get("mimeType", "text/markdown"),
                description=r.get("description"),
            )
            for r in resource_list
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        result = await resources.handle_resource_read(uri, documents, categories)
        if "error" in result:
            raise ValueError(result["error"])
        return cast(str, result.get("text", ""))
