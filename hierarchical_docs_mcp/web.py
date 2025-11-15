"""Web server for documentation browsing."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from hierarchical_docs_mcp.config import ServerConfig
from hierarchical_docs_mcp.handlers import tools
from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.models.navigation import Category
from hierarchical_docs_mcp.utils.logger import logger


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

        self._register_routes()

    def _register_routes(self) -> None:
        """Register API routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def root() -> str:
            """Serve the main HTML page."""
            return self._get_html_page()

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

    def _get_html_page(self) -> str:
        """Generate the main HTML page.

        Returns:
            HTML content
        """
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown MCP Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .search-section {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }

        .search-box {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .search-input {
            flex: 1;
            padding: 0.75rem;
            font-size: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            transition: border-color 0.3s;
        }

        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 500;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }

        .btn-secondary:hover {
            background: #e0e0e0;
        }

        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #e0e0e0;
        }

        .tab {
            padding: 0.75rem 1.5rem;
            background: none;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            color: #666;
            transition: all 0.3s;
        }

        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }

        .tab:hover {
            color: #667eea;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .results-section {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            min-height: 400px;
        }

        .result-item {
            padding: 1.5rem;
            border-bottom: 1px solid #e0e0e0;
            transition: background 0.3s;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .result-item:hover {
            background: #f9f9f9;
        }

        .result-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 0.5rem;
            cursor: pointer;
        }

        .result-title:hover {
            text-decoration: underline;
        }

        .breadcrumbs {
            font-size: 0.875rem;
            color: #666;
            margin-bottom: 0.5rem;
        }

        .excerpt {
            color: #555;
            line-height: 1.6;
        }

        .relevance {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
            font-size: 0.75rem;
            margin-top: 0.5rem;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        .error {
            background: #fee;
            color: #c33;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }

        .toc-tree {
            list-style: none;
            padding-left: 1.5rem;
        }

        .toc-item {
            margin: 0.5rem 0;
        }

        .toc-category {
            font-weight: 600;
            color: #667eea;
            cursor: pointer;
            user-select: none;
        }

        .toc-category:hover {
            text-decoration: underline;
        }

        .toc-document {
            color: #555;
            cursor: pointer;
            padding: 0.25rem 0;
        }

        .toc-document:hover {
            color: #667eea;
        }

        .document-content {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            line-height: 1.8;
        }

        .document-content h1,
        .document-content h2,
        .document-content h3 {
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            color: #333;
        }

        .document-content code {
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }

        .document-content pre {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
            margin: 1rem 0;
        }

        .tag-input {
            padding: 0.5rem;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            margin-right: 0.5rem;
        }

        .stats {
            display: flex;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            flex: 1;
            text-align: center;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>Markdown MCP Documentation</h1>
            <p>Browse and search documentation with the same tools available to LLMs</p>
        </div>
    </div>

    <div class="container">
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="doc-count">-</div>
                <div class="stat-label">Documents</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="category-count">-</div>
                <div class="stat-label">Categories</div>
            </div>
        </div>

        <div class="search-section">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('search')">Search</button>
                <button class="tab" onclick="switchTab('toc')">Table of Contents</button>
                <button class="tab" onclick="switchTab('tags')">Search by Tags</button>
                <button class="tab" onclick="switchTab('document')">Get Document</button>
            </div>

            <div id="search-tab" class="tab-content active">
                <div class="search-box">
                    <input type="text" id="search-query" class="search-input"
                           placeholder="Enter search query..."
                           onkeypress="if(event.key==='Enter') performSearch()">
                    <button class="btn btn-primary" onclick="performSearch()">Search</button>
                </div>
            </div>

            <div id="toc-tab" class="tab-content">
                <button class="btn btn-primary" onclick="loadTableOfContents()">Load Table of Contents</button>
            </div>

            <div id="tags-tab" class="tab-content">
                <div class="search-box">
                    <input type="text" id="tags-input" class="search-input"
                           placeholder="Enter tags (comma-separated)..."
                           onkeypress="if(event.key==='Enter') searchByTags()">
                    <button class="btn btn-primary" onclick="searchByTags()">Search by Tags</button>
                </div>
            </div>

            <div id="document-tab" class="tab-content">
                <div class="search-box">
                    <input type="text" id="document-uri" class="search-input"
                           placeholder="Enter document URI (e.g., docs://guides/quickstart/installation)"
                           onkeypress="if(event.key==='Enter') getDocument()">
                    <button class="btn btn-primary" onclick="getDocument()">Get Document</button>
                </div>
            </div>
        </div>

        <div id="results" class="results-section">
            <p style="color: #666; text-align: center;">Enter a search query or select a tool to get started</p>
        </div>
    </div>

    <script>
        // Utility function to escape HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Load health stats on page load
        fetch('/api/health')
            .then(res => res.json())
            .then(data => {
                document.getElementById('doc-count').textContent = data.documents;
                document.getElementById('category-count').textContent = data.categories;
            })
            .catch(err => console.error('Failed to load stats:', err));

        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab content
            document.getElementById(tabName + '-tab').classList.add('active');

            // Add active class to clicked tab
            event.target.classList.add('active');
        }

        async function performSearch() {
            const query = document.getElementById('search-query').value;
            if (!query) {
                alert('Please enter a search query');
                return;
            }

            showLoading();

            try {
                const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
                const data = await response.json();

                if (data.results && data.results.length > 0) {
                    displaySearchResults(data.results);
                } else {
                    showNoResults();
                }
            } catch (err) {
                showError('Search failed: ' + err.message);
            }
        }

        async function loadTableOfContents() {
            showLoading();

            try {
                const response = await fetch('/api/toc');
                const data = await response.json();
                displayTableOfContents(data);
            } catch (err) {
                showError('Failed to load table of contents: ' + err.message);
            }
        }

        async function searchByTags() {
            const tagsInput = document.getElementById('tags-input').value;
            if (!tagsInput) {
                alert('Please enter at least one tag');
                return;
            }

            const tags = tagsInput.split(',').map(t => t.trim()).filter(t => t);

            showLoading();

            try {
                const response = await fetch('/api/search-by-tags', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ tags }),
                });
                const data = await response.json();

                if (data.results && data.results.length > 0) {
                    displaySearchResults(data.results);
                } else {
                    showNoResults();
                }
            } catch (err) {
                showError('Tag search failed: ' + err.message);
            }
        }

        async function getDocument() {
            const uri = document.getElementById('document-uri').value;
            if (!uri) {
                alert('Please enter a document URI');
                return;
            }

            showLoading();

            try {
                const response = await fetch(`/api/document?uri=${encodeURIComponent(uri)}`);
                const data = await response.json();

                if (data.error) {
                    showError(data.error);
                } else {
                    displayDocument(data);
                }
            } catch (err) {
                showError('Failed to get document: ' + err.message);
            }
        }

        async function navigateToUri(uri) {
            showLoading();

            try {
                const response = await fetch(`/api/document?uri=${encodeURIComponent(uri)}`);
                const data = await response.json();

                if (data.error) {
                    showError(data.error);
                } else {
                    displayDocument(data);
                }
            } catch (err) {
                showError('Failed to navigate: ' + err.message);
            }
        }

        function displaySearchResults(results) {
            const resultsDiv = document.getElementById('results');

            let html = '<h2 style="margin-bottom: 1.5rem;">Search Results (' + results.length + ')</h2>';

            results.forEach((result, index) => {
                if (result.error) {
                    html += '<div class="error">' + escapeHtml(result.error) + '</div>';
                    return;
                }

                html += '<div class="result-item">';
                html += '<div class="result-title" data-uri="' + escapeHtml(result.uri) +
                        '" data-result-index="' + index + '">' +
                        escapeHtml(result.title || 'Untitled') + '</div>';
                if (result.breadcrumbs) {
                    html += '<div class="breadcrumbs">' + escapeHtml(result.breadcrumbs) + '</div>';
                }
                if (result.excerpt) {
                    html += '<div class="excerpt">' + result.excerpt + '</div>';
                }
                if (result.relevance !== undefined) {
                    html += '<span class="relevance">Relevance: ' +
                            (result.relevance * 100).toFixed(0) + '%</span>';
                }
                html += '</div>';
            });

            resultsDiv.innerHTML = html;

            // Add click handlers after inserting HTML
            document.querySelectorAll('.result-title[data-uri]').forEach(el => {
                el.style.cursor = 'pointer';
                el.addEventListener('click', function() {
                    navigateToUri(this.getAttribute('data-uri'));
                });
            });
        }

        function displayTableOfContents(toc) {
            const resultsDiv = document.getElementById('results');

            let html = '<h2 style="margin-bottom: 1.5rem;">Table of Contents</h2>';
            html += '<ul class="toc-tree">';
            html += renderTocNode(toc);
            html += '</ul>';

            resultsDiv.innerHTML = html;

            // Add click handlers for documents
            document.querySelectorAll('.toc-document[data-uri]').forEach(el => {
                el.addEventListener('click', function() {
                    navigateToUri(this.getAttribute('data-uri'));
                });
            });
        }

        function renderTocNode(node) {
            let html = '';

            if (node.categories) {
                for (const [name, category] of Object.entries(node.categories)) {
                    html += '<li class="toc-item">';
                    html += '<div class="toc-category">' + escapeHtml(category.label) +
                            ' (' + category.document_count + ' docs)</div>';

                    if (category.categories || category.documents) {
                        html += '<ul class="toc-tree">';
                        html += renderTocNode(category);
                        html += '</ul>';
                    }

                    html += '</li>';
                }
            }

            if (node.documents) {
                node.documents.forEach(doc => {
                    html += '<li class="toc-item">';
                    html += '<div class="toc-document" data-uri="' + escapeHtml(doc.uri) + '">' +
                            escapeHtml(doc.title) + '</div>';
                    html += '</li>';
                });
            }

            return html;
        }

        function displayDocument(doc) {
            const resultsDiv = document.getElementById('results');

            let html = '<div class="document-content">';
            html += '<h1>' + escapeHtml(doc.title) + '</h1>';

            if (doc.breadcrumbs && Array.isArray(doc.breadcrumbs)) {
                const breadcrumbsText = doc.breadcrumbs.map(b => escapeHtml(b)).join(' &gt; ');
                html += '<div class="breadcrumbs">' + breadcrumbsText + '</div>';
            }

            if (doc.tags && doc.tags.length > 0) {
                html += '<div style="margin: 1rem 0;">';
                doc.tags.forEach(tag => {
                    html += '<span style="background: #e0e0e0; padding: 0.25rem 0.5rem; border-radius: 3px; margin-right: 0.5rem;">' +
                            escapeHtml(tag) + '</span>';
                });
                html += '</div>';
            }

            html += '<hr style="margin: 1.5rem 0; border: none; border-top: 1px solid #e0e0e0;">';

            // Render content with proper newline handling
            const rawContent = doc.content || '';

            // Split by newlines, escape each line, then join with <br>
            const lines = rawContent.split('\n');
            const escapedLines = lines.map(line => {
                let escaped = escapeHtml(line);
                // Apply basic markdown after escaping (on escaped entities)
                escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                escaped = escaped.replace(/\*(.+?)\*/g, '<em>$1</em>');
                escaped = escaped.replace(/`(.+?)`/g, '<code>$1</code>');
                return escaped;
            });

            const content = escapedLines.join('<br>');

            html += '<div>' + content + '</div>';
            html += '</div>';

            resultsDiv.innerHTML = html;
        }

        function showLoading() {
            document.getElementById('results').innerHTML =
                '<div class="loading">Loading...</div>';
        }

        function showNoResults() {
            document.getElementById('results').innerHTML =
                '<div style="text-align: center; color: #666; padding: 2rem;">No results found</div>';
        }

        function showError(message) {
            document.getElementById('results').innerHTML =
                '<div class="error">' + escapeHtml(message) + '</div>';
        }
    </script>
</body>
</html>
        """
