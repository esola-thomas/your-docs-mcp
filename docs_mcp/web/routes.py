"""Server-rendered documentation routes (/docs/*)."""

from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.core.services.hierarchy import get_breadcrumbs, get_table_of_contents
from docs_mcp.core.services.search import search_content
from docs_mcp.core.utils.logger import logger
from docs_mcp.web.markdown_renderer import render_markdown

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def create_docs_router(
    documents: list[Document],
    categories: dict[str, Category],
    config: ServerConfig,
) -> APIRouter:
    """Create the /docs/* router for server-rendered pages.

    Args:
        documents: All loaded documents
        categories: Category tree
        config: Server configuration

    Returns:
        FastAPI APIRouter
    """
    router = APIRouter()

    # Build ordered document list for prev/next navigation
    doc_map = {d.uri: d for d in documents}
    ordered_docs = sorted(documents, key=lambda d: (str(d.relative_path.parent), d.order, d.title))

    def _get_nav_tree() -> list[dict[str, Any]]:
        """Build navigation tree for sidebar."""
        toc = get_table_of_contents(categories, documents)
        return toc.get("children", [])

    def _get_prev_next(doc: Document) -> tuple[Document | None, Document | None]:
        """Get previous and next documents in order."""
        try:
            idx = ordered_docs.index(doc)
        except ValueError:
            return None, None
        prev_doc = ordered_docs[idx - 1] if idx > 0 else None
        next_doc = ordered_docs[idx + 1] if idx < len(ordered_docs) - 1 else None
        return prev_doc, next_doc

    def _uri_to_url(uri: str) -> str:
        """Convert a docs:// URI to a /docs/ URL path."""
        path = uri.replace("docs://", "")
        if not path:
            return "/docs/"
        return f"/docs/{path}"

    def _base_context(request: Request) -> dict[str, Any]:
        """Common template context."""
        return {
            "request": request,
            "config": config,
            "nav_tree": _get_nav_tree(),
            "uri_to_url": _uri_to_url,
            "base_url": config.base_url.rstrip("/") if config.base_url else "",
        }

    @router.get("/docs/", response_class=HTMLResponse)
    async def docs_home(request: Request) -> Response:
        """Documentation landing page."""
        root_categories = [c for c in categories.values() if c.depth == 0]

        ctx = _base_context(request)
        ctx.update(
            {
                "doc_count": len(documents),
                "category_count": len(categories),
                "categories": root_categories,
            }
        )
        return templates.TemplateResponse("home.html", ctx)

    @router.get("/docs/search", response_class=HTMLResponse)
    async def docs_search(request: Request, q: str = "") -> Response:
        """Search results page."""
        results = []
        if q:
            try:
                search_results = search_content(
                    query=q,
                    documents=documents,
                    categories=categories,
                    limit=20,
                )
                results = [
                    {
                        "title": r.title,
                        "url": _uri_to_url(r.document_uri),
                        "excerpt": r.highlighted_excerpt or r.excerpt,
                        "breadcrumbs": r.breadcrumb_string,
                        "match_type": r.match_type,
                        "relevance": r.relevance_score,
                    }
                    for r in search_results
                ]
            except Exception as e:
                logger.error(f"Search failed: {e}")

        ctx = _base_context(request)
        ctx.update({"query": q, "results": results})
        return templates.TemplateResponse("search.html", ctx)

    @router.get("/docs/tags/", response_class=HTMLResponse)
    async def docs_all_tags(request: Request) -> Response:
        """All tags page."""
        tag_counts: dict[str, int] = {}
        for doc in documents:
            for tag in doc.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        ctx = _base_context(request)
        ctx.update({"tag": None, "tag_counts": tag_counts, "documents_for_tag": []})
        return templates.TemplateResponse("tags.html", ctx)

    @router.get("/docs/tags/{tag}", response_class=HTMLResponse)
    async def docs_tag(request: Request, tag: str) -> Response:
        """Documents filtered by tag."""
        matching_docs = [d for d in documents if tag in d.tags]

        tag_counts: dict[str, int] = {}
        for doc in documents:
            for t in doc.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1

        ctx = _base_context(request)
        ctx.update(
            {
                "tag": tag,
                "tag_counts": tag_counts,
                "documents_for_tag": matching_docs,
                "uri_to_url": _uri_to_url,
            }
        )
        return templates.TemplateResponse("tags.html", ctx)

    @router.get("/docs/{category}/", response_class=HTMLResponse)
    async def docs_category(request: Request, category: str) -> Response:
        """Category listing page."""
        category_uri = f"docs://{category}"

        if category_uri not in categories:
            ctx = _base_context(request)
            return templates.TemplateResponse("404.html", ctx, status_code=404)

        cat = categories[category_uri]

        # Get child categories
        child_cats = [categories[uri] for uri in cat.child_categories if uri in categories]

        # Get child documents
        child_docs = [doc_map[uri] for uri in cat.child_documents if uri in doc_map]

        breadcrumbs = [{"name": "Home", "url": "/docs/"}]
        for crumb in cat.breadcrumbs:
            breadcrumbs.append({"name": crumb["name"], "url": _uri_to_url(crumb["uri"]) + "/"})

        ctx = _base_context(request)
        ctx.update(
            {
                "category": cat,
                "child_categories": child_cats,
                "child_docs": child_docs,
                "breadcrumbs": breadcrumbs,
            }
        )
        return templates.TemplateResponse("category.html", ctx)

    @router.get("/docs/{category}/{slug}", response_class=HTMLResponse)
    async def docs_document(request: Request, category: str, slug: str) -> Response:
        """Individual document page."""
        doc_uri = f"docs://{category}/{slug}"
        doc = doc_map.get(doc_uri)

        if not doc:
            ctx = _base_context(request)
            return templates.TemplateResponse("404.html", ctx, status_code=404)

        # Render markdown to HTML
        rendered = render_markdown(doc.content)

        # Build breadcrumbs
        breadcrumbs = [{"name": "Home", "url": "/docs/"}]
        for crumb in get_breadcrumbs(doc.uri):
            breadcrumbs.append({"name": crumb["name"], "url": _uri_to_url(crumb["uri"]) + "/"})
        breadcrumbs.append({"name": doc.title, "url": ""})

        # Get prev/next
        prev_doc, next_doc = _get_prev_next(doc)

        # GitHub edit URL
        github_url = ""
        if config.github_repo:
            repo = config.github_repo.rstrip("/")
            github_url = f"{repo}/edit/main/{doc.relative_path}"

        ctx = _base_context(request)
        ctx.update(
            {
                "doc": doc,
                "content_html": rendered["html"],
                "headings": rendered["toc"],
                "breadcrumbs": breadcrumbs,
                "prev_doc": prev_doc,
                "next_doc": next_doc,
                "github_url": github_url,
                "current_uri": doc.uri,
            }
        )
        return templates.TemplateResponse("doc.html", ctx)

    @router.get("/sitemap.xml", response_class=Response)
    async def sitemap(request: Request) -> Response:
        """Auto-generated sitemap."""
        base = config.base_url.rstrip("/") if config.base_url else str(request.base_url).rstrip("/")

        urlset = Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        # Add home
        url_el = SubElement(urlset, "url")
        SubElement(url_el, "loc").text = f"{base}/docs/"
        SubElement(url_el, "changefreq").text = "daily"
        SubElement(url_el, "priority").text = "1.0"

        # Add categories
        for cat in categories.values():
            url_el = SubElement(urlset, "url")
            SubElement(url_el, "loc").text = f"{base}{_uri_to_url(cat.uri)}/"
            SubElement(url_el, "changefreq").text = "weekly"
            SubElement(url_el, "priority").text = "0.8"

        # Add documents
        for doc in documents:
            url_el = SubElement(urlset, "url")
            SubElement(url_el, "loc").text = f"{base}{_uri_to_url(doc.uri)}"
            SubElement(url_el, "lastmod").text = doc.last_modified.strftime("%Y-%m-%d")
            SubElement(url_el, "changefreq").text = "weekly"
            SubElement(url_el, "priority").text = "0.6"

        xml_bytes = tostring(urlset, encoding="unicode", xml_declaration=False)
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes

        return Response(content=xml_str, media_type="application/xml")

    @router.get("/robots.txt", response_class=Response)
    async def robots(request: Request) -> Response:
        """Robots.txt file."""
        base = config.base_url.rstrip("/") if config.base_url else str(request.base_url).rstrip("/")

        content = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
        return Response(content=content, media_type="text/plain")

    return router
