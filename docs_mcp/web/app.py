"""Web server for documentation browsing with MCP SSE transport support."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Resource, Tool
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.responses import Response as StarletteResponse
from starlette.routing import Mount, Route

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.core.utils.logger import logger
from docs_mcp.mcp.handlers import resources, tools
from docs_mcp.web.partials import create_partials_router
from docs_mcp.web.routes import create_docs_router


class SearchRequest(BaseModel):
    """Search request model."""

    query: str
    category: str | None = None
    limit: int = 10


class NavigateRequest(BaseModel):
    """Navigate request model."""

    uri: str


class TableOfContentsRequest(BaseModel):
    """Table of contents request model."""

    max_depth: int | None = None


class SearchByTagsRequest(BaseModel):
    """Search by tags request model."""

    tags: list[str]
    category: str | None = None
    limit: int = 10


class GetDocumentRequest(BaseModel):
    """Get document request model."""

    uri: str


class GetAllTagsRequest(BaseModel):
    """Get all tags request model."""

    category: str | None = None
    include_counts: bool = False


class GeneratePDFRequest(BaseModel):
    """Generate PDF release request model."""

    title: str | None = None
    subtitle: str | None = None
    author: str | None = None
    version: str | None = None
    confidential: bool = False
    owner: str | None = None


class DocumentationWebServer:
    """Web server for documentation browsing with MCP SSE transport support."""

    def __init__(
        self,
        config: ServerConfig,
        documents: list[Document],
        categories: dict[str, Category],
    ) -> None:
        """Initialize the web server."""
        self.config = config
        self.documents = documents
        self.categories = categories

        # Create the MCP server for SSE transport
        self.mcp_server = Server("hierarchical-docs-mcp")
        self._register_mcp_handlers()

        # Create SSE transport
        self.sse_transport = SseServerTransport("/messages/")

        self.app = FastAPI(
            title="Markdown MCP Documentation",
            description="Web interface for browsing documentation with MCP SSE support",
            version="0.1.0",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

        # Mount static files from web/static/
        static_dir = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Register routes
        self._register_routes()
        self._register_mcp_sse_routes()

        # Register HTMX partials BEFORE docs routes (more specific paths first)
        partials_router = create_partials_router(documents, categories, config)
        self.app.include_router(partials_router)

        # Register server-rendered docs routes
        docs_router = create_docs_router(documents, categories, config)
        self.app.include_router(docs_router)

    def _register_mcp_handlers(self) -> None:
        """Register MCP protocol handlers for SSE transport."""

        @self.mcp_server.list_tools()
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
                                "description": "URI to navigate to",
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
                                "description": "Document URI",
                            },
                        },
                        "required": ["uri"],
                    },
                ),
                Tool(
                    name="get_all_tags",
                    description=("Get a list of all unique tags defined across the documentation."),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Optional category to filter tags from",
                            },
                            "include_counts": {
                                "type": "boolean",
                                "description": "Include document count for each tag",
                                "default": False,
                            },
                        },
                    },
                ),
                Tool(
                    name="generate_pdf_release",
                    description=("Generate a PDF documentation release."),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Document title."},
                            "subtitle": {"type": "string", "description": "Document subtitle."},
                            "author": {"type": "string", "description": "Document author."},
                            "version": {"type": "string", "description": "Version string."},
                            "confidential": {
                                "type": "boolean",
                                "description": "Add confidentiality markings.",
                                "default": False,
                            },
                            "owner": {"type": "string", "description": "Copyright owner."},
                        },
                    },
                ),
            ]

        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[Any]:
            """Handle tool calls."""
            logger.info(f"MCP SSE Tool call: {name}")

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
                result = await tools.handle_generate_pdf_release(
                    arguments, Path(self.config.docs_root)
                )
                return [{"type": "text", "text": json.dumps(result, indent=2)}]

            else:
                raise ValueError(f"Unknown tool: {name}")

        @self.mcp_server.list_resources()
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

        @self.mcp_server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource by URI."""
            from typing import cast

            result = await resources.handle_resource_read(uri, self.documents, self.categories)

            if "error" in result:
                raise ValueError(result["error"])

            return cast(str, result.get("text", ""))

    def _register_mcp_sse_routes(self) -> None:
        """Register MCP SSE transport routes."""

        async def sse_endpoint(request: Request) -> StarletteResponse:
            """SSE endpoint for MCP clients."""
            logger.info("MCP SSE client connecting...")

            async with self.sse_transport.connect_sse(
                request.scope,
                request.receive,
                request._send,  # type: ignore[arg-type]
            ) as streams:
                await self.mcp_server.run(
                    streams[0],
                    streams[1],
                    self.mcp_server.create_initialization_options(),
                )

            return StarletteResponse()

        sse_routes_app = Starlette(
            routes=[
                Route("/sse", endpoint=sse_endpoint, methods=["GET"]),
                Mount("/messages/", app=self.sse_transport.handle_post_message),
            ]
        )

        for route in reversed(sse_routes_app.routes):
            self.app.router.routes.insert(0, route)

    def _register_routes(self) -> None:
        """Register API routes."""

        @self.app.get("/")
        async def root() -> RedirectResponse:
            """Redirect root to /docs/."""
            return RedirectResponse(url="/docs/", status_code=302)

        @self.app.get("/api/health")
        async def health() -> dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "documents": len(self.documents),
                "categories": len(self.categories),
            }

        @self.app.post("/api/search")
        async def search(request: SearchRequest) -> JSONResponse:
            """Search documentation."""
            try:
                results = await tools.handle_search_documentation(
                    arguments={
                        "query": request.query,
                        "category": request.category,
                        "limit": request.limit,
                    },
                    documents=self.documents,
                    categories=self.categories,
                    search_limit=self.config.search_limit,
                )
                return JSONResponse(content={"results": results})
            except Exception as e:
                logger.error(f"Search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/search")
        async def search_get(
            query: str = Query(..., description="Search query"),
            category: str | None = Query(None, description="Category filter"),
            limit: int = Query(10, description="Maximum results"),
        ) -> JSONResponse:
            """Search documentation via GET request."""
            try:
                results = await tools.handle_search_documentation(
                    arguments={
                        "query": query,
                        "category": category,
                        "limit": limit,
                    },
                    documents=self.documents,
                    categories=self.categories,
                    search_limit=self.config.search_limit,
                )
                return JSONResponse(content={"results": results})
            except Exception as e:
                logger.error(f"Search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/navigate")
        async def navigate(request: NavigateRequest) -> JSONResponse:
            """Navigate to a specific URI."""
            try:
                result = await tools.handle_navigate_to(
                    arguments={"uri": request.uri},
                    documents=self.documents,
                    categories=self.categories,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/navigate")
        async def navigate_get(
            uri: str = Query(..., description="URI to navigate to"),
        ) -> JSONResponse:
            """Navigate to a specific URI via GET request."""
            try:
                result = await tools.handle_navigate_to(
                    arguments={"uri": uri},
                    documents=self.documents,
                    categories=self.categories,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/toc")
        async def table_of_contents(request: TableOfContentsRequest) -> JSONResponse:
            """Get table of contents."""
            try:
                result = await tools.handle_get_table_of_contents(
                    arguments={"max_depth": request.max_depth},
                    documents=self.documents,
                    categories=self.categories,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"TOC generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/toc")
        async def table_of_contents_get(
            max_depth: int | None = Query(None, description="Maximum depth"),
        ) -> JSONResponse:
            """Get table of contents via GET request."""
            try:
                result = await tools.handle_get_table_of_contents(
                    arguments={"max_depth": max_depth},
                    documents=self.documents,
                    categories=self.categories,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"TOC generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/search-by-tags")
        async def search_by_tags(request: SearchByTagsRequest) -> JSONResponse:
            """Search by tags."""
            try:
                results = await tools.handle_search_by_tags(
                    arguments={
                        "tags": request.tags,
                        "category": request.category,
                        "limit": request.limit,
                    },
                    documents=self.documents,
                    search_limit=self.config.search_limit,
                )
                return JSONResponse(content={"results": results})
            except Exception as e:
                logger.error(f"Tag search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/document")
        async def get_document(request: GetDocumentRequest) -> JSONResponse:
            """Get document content."""
            try:
                result = await tools.handle_get_document(
                    arguments={"uri": request.uri},
                    documents=self.documents,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"Get document failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/document")
        async def get_document_get(
            uri: str = Query(..., description="Document URI"),
        ) -> JSONResponse:
            """Get document content via GET request."""
            try:
                result = await tools.handle_get_document(
                    arguments={"uri": uri},
                    documents=self.documents,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"Get document failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/tags")
        async def get_all_tags(request: GetAllTagsRequest) -> JSONResponse:
            """Get all unique tags across documentation."""
            try:
                result = await tools.handle_get_all_tags(
                    arguments={
                        "category": request.category,
                        "include_counts": request.include_counts,
                    },
                    documents=self.documents,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"Get all tags failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/tags")
        async def get_all_tags_get(
            category: str | None = Query(None, description="Category filter"),
            include_counts: bool = Query(False, description="Include document count per tag"),
        ) -> JSONResponse:
            """Get all unique tags via GET request."""
            try:
                result = await tools.handle_get_all_tags(
                    arguments={
                        "category": category,
                        "include_counts": include_counts,
                    },
                    documents=self.documents,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"Get all tags failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/generate-pdf")
        async def generate_pdf(request: GeneratePDFRequest) -> JSONResponse:
            """Generate PDF documentation release."""
            try:
                result = await tools.handle_generate_pdf_release(
                    arguments={
                        "title": request.title,
                        "subtitle": request.subtitle,
                        "author": request.author,
                        "version": request.version,
                        "confidential": request.confidential,
                        "owner": request.owner,
                    },
                    docs_root=Path(self.config.docs_root),
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

