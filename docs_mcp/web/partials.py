"""HTMX partial HTML endpoints for dynamic content."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.core.services.search import search_content
from docs_mcp.core.utils.logger import logger

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def create_partials_router(
    documents: list[Document],
    categories: dict[str, Category],
    config: ServerConfig,
) -> APIRouter:
    """Create the /docs/_partials/* router for HTMX fragments.

    Args:
        documents: All loaded documents
        categories: Category tree
        config: Server configuration

    Returns:
        FastAPI APIRouter
    """
    router = APIRouter()

    def _uri_to_url(uri: str) -> str:
        """Convert a docs:// URI to a /docs/ URL path."""
        path = uri.replace("docs://", "")
        if not path:
            return "/docs/"
        return f"/docs/{path}"

    @router.get("/docs/_partials/search-results", response_class=HTMLResponse)
    async def search_results_partial(request: Request, q: str = "") -> HTMLResponse:
        """Return search results as an HTML fragment for HTMX."""
        if not q or len(q) < 2:
            return HTMLResponse(content="")

        try:
            search_results = search_content(
                query=q,
                documents=documents,
                categories=categories,
                limit=10,
            )
        except Exception as e:
            logger.error(f"Partial search failed: {e}")
            return HTMLResponse(
                content='<p class="text-muted">Search failed. Please try again.</p>'
            )

        if not search_results:
            return HTMLResponse(
                content=f'<p class="text-muted">No results found for &quot;{q}&quot;</p>'
            )

        # Build HTML fragment
        html_parts = []
        for r in search_results:
            url = _uri_to_url(r.document_uri)
            excerpt = r.highlighted_excerpt or r.excerpt
            # Convert **bold** markers to <mark> tags for highlighting
            excerpt = excerpt.replace("**", "<mark>", 1)
            if "<mark>" in excerpt:
                excerpt = excerpt.replace("**", "</mark>", 1)

            html_parts.append(
                f'<a href="{url}" class="search-result">'
                f"<h3>{_escape(r.title)}</h3>"
                f'<p class="breadcrumbs-text">{_escape(r.breadcrumb_string)}</p>'
                f'<p class="excerpt">{excerpt}</p>'
                f'<span class="match-badge">{r.match_type}</span>'
                f"</a>"
            )

        return HTMLResponse(content="\n".join(html_parts))

    return router


def _escape(text: str) -> str:
    """HTML-escape a string."""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )
