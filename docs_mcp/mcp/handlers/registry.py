"""Shared MCP handler registration for both stdio and SSE transports.

Provides a single source of truth for tool definitions, tool dispatch,
resource listing, and resource reading — used by both DocumentationMCPServer
(stdio) and DocumentationWebServer (SSE).
"""

import json
from typing import Any

from jsonschema import Draft202012Validator
from mcp import MCPError
from mcp.server import Server, ServerRequestContext
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    PaginatedRequestParams,
    ReadResourceRequestParams,
    ReadResourceResult,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)

from docs_mcp import __version__
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
            input_schema={
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
            input_schema={
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
            input_schema={
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
            input_schema={
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
            input_schema={
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
            input_schema={
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
                input_schema={
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


def create_mcp_server(
    documents: list[Document],
    categories: dict[str, Category],
    config: ServerConfig,
) -> Server:
    """Construct a v2 SDK server with shared tool and resource adapters.

    Closures capture documents/categories by reference so they see
    data populated later by initialize().

    Args:
        documents: Mutable list of loaded documents
        categories: Mutable dict of category tree
        config: Server configuration
    """

    definitions = {
        tool.name: tool for tool in get_tool_definitions(enable_pdf=config.enable_pdf_generation)
    }
    validators = {
        name: Draft202012Validator(tool.input_schema) for name, tool in definitions.items()
    }

    async def list_tools(
        ctx: ServerRequestContext,
        params: PaginatedRequestParams | None,
    ) -> ListToolsResult:
        return ListToolsResult(tools=list(definitions.values()))

    async def dispatch_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
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
            if config.docs_root is None:
                raise ValueError("PDF generation requires a configured docs_root")
            result = await tools.handle_generate_pdf_release(arguments, config.docs_root)
            return [{"type": "text", "text": json.dumps(result, indent=2)}]

        else:
            raise ValueError(f"Unknown tool: {name}")

    async def call_tool(
        ctx: ServerRequestContext,
        params: CallToolRequestParams,
    ) -> CallToolResult:
        # v2's low-level server no longer validates or wraps tool calls.
        try:
            if params.name not in definitions:
                raise ValueError(f"Unknown or disabled tool: {params.name}")
            arguments = params.arguments or {}
            validators[params.name].validate(arguments)
            content = await dispatch_tool(params.name, arguments)
            return CallToolResult(content=[TextContent(**item) for item in content])
        except Exception as exc:
            logger.warning(f"Tool {params.name} failed: {exc}")
            return CallToolResult(
                content=[TextContent(type="text", text=str(exc))],
                is_error=True,
            )

    async def list_resources_handler(
        ctx: ServerRequestContext,
        params: PaginatedRequestParams | None,
    ) -> ListResourcesResult:
        resource_list = await resources.list_resources(documents, categories)
        return ListResourcesResult(
            resources=[
                Resource(
                    uri=r["uri"],
                    name=r["name"],
                    mime_type=r.get("mimeType", "text/markdown"),
                    description=r.get("description"),
                )
                for r in resource_list
            ]
        )

    async def read_resource(
        ctx: ServerRequestContext,
        params: ReadResourceRequestParams,
    ) -> ReadResourceResult:
        result = await resources.handle_resource_read(params.uri, documents, categories)
        if "error" in result:
            raise MCPError(-32602, result["error"])
        return ReadResourceResult(
            contents=[
                TextResourceContents(
                    uri=params.uri,
                    text=result.get("text", ""),
                    mime_type=result.get("mimeType", "text/markdown"),
                )
            ]
        )

    return Server(
        "hierarchical-docs-mcp",
        version=__version__,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
        on_list_resources=list_resources_handler,
        on_read_resource=read_resource,
    )
