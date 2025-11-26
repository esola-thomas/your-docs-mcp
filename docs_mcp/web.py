"""Web server for documentation browsing."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from docs_mcp.config import ServerConfig
from docs_mcp.handlers import tools
from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category
from docs_mcp.utils.logger import logger


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


class DocumentationWebServer:
    """Web server for documentation browsing."""

    def __init__(
        self,
        config: ServerConfig,
        documents: list[Document],
        categories: dict[str, Category],
    ) -> None:
        """Initialize the web server.

        Args:
            config: Server configuration
            documents: List of all documents
            categories: Category tree
        """
        self.config = config
        self.documents = documents
        self.categories = categories
        self.app = FastAPI(
            title="Markdown MCP Documentation",
            description="Web interface for browsing documentation",
            version="0.1.0",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount static files
        static_dir = Path(__file__).parent / "static"
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        self._register_routes()

    def _register_routes(self) -> None:
        """Register API routes."""

        @self.app.get("/")
        async def root() -> FileResponse:
            """Serve the main HTML page."""
            static_dir = Path(__file__).parent / "static"
            return FileResponse(str(static_dir / "index.html"))

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
            """Search documentation.

            Args:
                request: Search parameters

            Returns:
                Search results
            """
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
            """Search documentation via GET request.

            Args:
                query: Search query string
                category: Optional category filter
                limit: Maximum number of results

            Returns:
                Search results
            """
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
            """Navigate to a specific URI.

            Args:
                request: Navigation parameters

            Returns:
                Navigation context
            """
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
            """Navigate to a specific URI via GET request.

            Args:
                uri: URI to navigate to

            Returns:
                Navigation context
            """
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
            """Get table of contents.

            Args:
                request: TOC parameters

            Returns:
                Table of contents tree
            """
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
            """Get table of contents via GET request.

            Args:
                max_depth: Optional maximum depth

            Returns:
                Table of contents tree
            """
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
            """Search by tags.

            Args:
                request: Tag search parameters

            Returns:
                Search results
            """
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
            """Get document content.

            Args:
                request: Document request parameters

            Returns:
                Document details
            """
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
            """Get document content via GET request.

            Args:
                uri: Document URI

            Returns:
                Document details
            """
            try:
                result = await tools.handle_get_document(
                    arguments={"uri": uri},
                    documents=self.documents,
                )
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"Get document failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
