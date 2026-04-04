"""Web server for documentation browsing with MCP SSE transport support."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.responses import Response as StarletteResponse
from starlette.routing import Mount, Route

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.core.utils.logger import logger
from docs_mcp.mcp.handlers import tools
from docs_mcp.mcp.handlers.registry import register_mcp_handlers
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

        # Create the MCP server for SSE transport (only if MCP transport is enabled)
        if self.config.enable_mcp_transport:
            self.mcp_server = Server("hierarchical-docs-mcp")
            register_mcp_handlers(self.mcp_server, self.documents, self.categories, self.config)
            self.sse_transport = SseServerTransport("/messages/")
        else:
            self.mcp_server = None
            self.sse_transport = None

        self.app = FastAPI(
            title=config.branding.site_name,
            description=f"Web interface for {config.branding.site_name} with MCP SSE support",
            version="1.0.0",
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

        # Mount custom static files BEFORE default (checked first by FastAPI)
        if config.custom_static_dir and config.custom_static_dir.is_dir():
            self.app.mount(
                "/static/custom",
                StaticFiles(directory=str(config.custom_static_dir)),
                name="custom-static",
            )

        # Mount default static files from web/static/
        static_dir = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Register routes
        self._register_routes()
        if self.config.enable_mcp_transport:
            self._register_mcp_sse_routes()

        # Register HTMX partials BEFORE docs routes (more specific paths first)
        partials_router = create_partials_router(documents, categories, config)
        self.app.include_router(partials_router)

        # Register server-rendered docs routes
        docs_router = create_docs_router(documents, categories, config)
        self.app.include_router(docs_router)

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

        if self.config.enable_pdf_generation:

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
