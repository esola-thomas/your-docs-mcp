"""Main MCP server implementation."""

import asyncio
import json
from typing import Any, cast

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool

from docs_mcp.config import ServerConfig
from docs_mcp.handlers import resources, tools
from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category
from docs_mcp.services.hierarchy import build_category_tree
from docs_mcp.services.markdown import scan_markdown_files
from docs_mcp.services.vector import get_vector_store
from docs_mcp.utils.logger import logger


class DocumentationMCPServer:
    """Hierarchical Documentation MCP Server."""

    def __init__(self, config: ServerConfig) -> None:
        """Initialize the server.

        Args:
            config: Server configuration
        """
        self.config = config
        self.server = Server("hierarchical-docs-mcp")
        self.documents: list[Document] = []
        self.categories: dict[str, Category] = {}

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
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
                    description=(
                        "Get the complete documentation hierarchy as a table of contents tree."
                    ),
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
                    description=("Search documentation by metadata tags and category."),
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
                                "description": "Version string for the release (e.g., '2.0.0'). Defaults to current date.",
                            },
                            "confidential": {
                                "type": "boolean",
                                "description": "Add confidentiality markings (watermark, headers, footers). Default: false",
                                "default": False,
                            },
                            "owner": {
                                "type": "string",
                                "description": "Copyright owner (shown when confidential=true). Defaults to project name.",
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[Any]:
            """Handle tool calls."""
            logger.info(f"Tool call: {name}")

            if name == "search_documentation":
                results = await tools.handle_search_documentation(
                    arguments, self.documents, self.categories, self.config.search_limit
                )
                return [{"type": "text", "text": json.dumps(results, indent=2)}]

            elif name == "navigate_to":
                result = await tools.handle_navigate_to(arguments, self.documents, self.categories)
                return [{"type": "text", "text": json.dumps(result, indent=2)}]

            elif name == "get_table_of_contents":
                result = await tools.handle_get_table_of_contents(
                    arguments, self.documents, self.categories
                )
                return [{"type": "text", "text": json.dumps(result, indent=2)}]

            elif name == "search_by_tags":
                results = await tools.handle_search_by_tags(
                    arguments, self.documents, self.config.search_limit
                )
                return [{"type": "text", "text": json.dumps(results, indent=2)}]

            elif name == "get_document":
                result = await tools.handle_get_document(arguments, self.documents)
                return [{"type": "text", "text": json.dumps(result, indent=2)}]

            elif name == "get_all_tags":
                result = await tools.handle_get_all_tags(arguments, self.documents)
                return [{"type": "text", "text": json.dumps(result, indent=2)}]

            elif name == "generate_pdf_release":
                from pathlib import Path

                result = await tools.handle_generate_pdf_release(
                    arguments, Path(self.config.docs_root)
                )
                return [{"type": "text", "text": json.dumps(result, indent=2)}]

            else:
                raise ValueError(f"Unknown tool: {name}")

        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources."""
            resource_list = await resources.list_resources(self.documents, self.categories)
            return [
                Resource(
                    uri=r["uri"],
                    name=r["name"],
                    mimeType=r.get("mimeType", "text/markdown"),
                    description=r.get("description"),
                )
                for r in resource_list
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource by URI."""
            result = await resources.handle_resource_read(uri, self.documents, self.categories)

            if "error" in result:
                raise ValueError(result["error"])

            return cast(str, result.get("text", ""))

    async def initialize(self) -> None:
        """Initialize the server by loading documentation."""
        logger.info("Initializing documentation server...")

        # Load documentation from sources
        for source in self.config.sources:
            logger.info(f"Loading documentation from: {source.path}")

            try:
                docs = scan_markdown_files(
                    source_path=source.path,
                    doc_root=source.path,
                    recursive=source.recursive,
                    include_patterns=source.include_patterns,
                    exclude_patterns=source.exclude_patterns,
                    allow_hidden=self.config.allow_hidden,
                )

                self.documents.extend(docs)
                logger.info(f"Loaded {len(docs)} documents from {source.path}")

            except Exception as e:
                logger.error(f"Failed to load documentation from {source.path}: {e}")

        # Build category tree
        if self.documents:
            self.categories = build_category_tree(self.documents)
            logger.info(f"Built category tree with {len(self.categories)} categories")

            # Index documents for vector search
            try:
                get_vector_store().add_documents(self.documents)
            except Exception as e:
                logger.error(f"Failed to index documents: {e}")

        logger.info(
            f"Initialization complete: {len(self.documents)} documents, "
            f"{len(self.categories)} categories"
        )

    async def run(self) -> None:
        """Run the server with stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def serve(config: ServerConfig) -> None:
    """Create and run the MCP server.

    Args:
        config: Server configuration
    """
    server = DocumentationMCPServer(config)
    await server.initialize()
    await server.run()


async def serve_both(config: ServerConfig) -> None:
    """Create and run both MCP and web servers concurrently.

    Args:
        config: Server configuration

    Note:
        When running both servers, uvicorn logging is suppressed to prevent
        stdout pollution that could interfere with MCP stdio protocol.
        The web server starts first, then MCP stdio server runs in parallel.
    """
    import uvicorn

    from docs_mcp.web import DocumentationWebServer

    # Create and initialize MCP server (loads documents)
    mcp_server = DocumentationMCPServer(config)
    await mcp_server.initialize()

    async def run_web_server() -> None:
        """Run the web server."""
        web_server = DocumentationWebServer(
            config=config,
            documents=mcp_server.documents,
            categories=mcp_server.categories,
        )

        # Configure uvicorn to NOT output to stdout (would break MCP protocol)
        # All uvicorn logging goes to stderr via custom log config
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": False,
                },
            },
            "handlers": {
                "stderr": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["stderr"], "level": "WARNING", "propagate": False},
                "uvicorn.error": {"handlers": ["stderr"], "level": "WARNING", "propagate": False},
                "uvicorn.access": {"handlers": ["stderr"], "level": "WARNING", "propagate": False},
            },
        }

        uvicorn_config = uvicorn.Config(
            app=web_server.app,
            host=config.web_host,
            port=config.web_port,
            log_config=log_config,
            access_log=False,  # Disable access logging to prevent stdout pollution
        )

        uvicorn_server = uvicorn.Server(uvicorn_config)
        await uvicorn_server.serve()

    async def run_mcp_server() -> None:
        """Run the MCP stdio server."""
        await mcp_server.run()

    # Create tasks - web server first so it binds the port before MCP blocks on stdio
    tasks = []

    if config.enable_web_server:
        logger.info(f"Starting web server on {config.web_host}:{config.web_port}")
        tasks.append(asyncio.create_task(run_web_server()))
        # Give web server time to bind the port
        await asyncio.sleep(0.1)

    # Add MCP server task
    tasks.append(asyncio.create_task(run_mcp_server()))

    # Wait for all servers (will run until interrupted)
    await asyncio.gather(*tasks)


async def serve_web_only(config: ServerConfig) -> None:
    """Create and run web server only (no MCP stdio server).

    Args:
        config: Server configuration

    This is useful for standalone documentation browsing or REST API access
    without running the MCP protocol server.
    """
    import uvicorn

    from docs_mcp.web import DocumentationWebServer

    # Create MCP server just to initialize documents (but don't run stdio)
    mcp_server = DocumentationMCPServer(config)
    await mcp_server.initialize()

    # Create web server with shared document state
    web_server = DocumentationWebServer(
        config=config,
        documents=mcp_server.documents,
        categories=mcp_server.categories,
    )

    logger.info(f"Starting web server on {config.web_host}:{config.web_port}")

    # Standard uvicorn config for web-only mode (can use stdout normally)
    uvicorn_config = uvicorn.Config(
        app=web_server.app,
        host=config.web_host,
        port=config.web_port,
        log_level=config.log_level.lower(),
    )

    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()
