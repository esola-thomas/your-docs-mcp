"""Integration tests for server-rendered documentation routes."""


import pytest
from fastapi.testclient import TestClient

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.services.hierarchy import build_category_tree
from docs_mcp.web.app import DocumentationWebServer


@pytest.fixture
def docs_with_content(tmp_path):
    """Create a docs directory with sample content."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    guides = docs_root / "guides"
    guides.mkdir()
    (guides / "getting-started.md").write_text(
        "---\ntitle: Getting Started\ntags: [intro, guide]\norder: 1\n---\n"
        "# Getting Started\n\nWelcome to the docs.\n\n"
        "## Installation\n\nRun `pip install your-docs-mcp`.\n\n"
        "## Usage\n\nStart the server.\n"
    )
    (guides / "advanced.md").write_text(
        "---\ntitle: Advanced Usage\ntags: [advanced]\norder: 2\n---\n"
        "# Advanced Usage\n\nAdvanced features here.\n"
    )
    return docs_root


@pytest.fixture
def web_client(docs_with_content):
    """Create a test client with real documents loaded."""
    from docs_mcp.core.services.markdown import scan_markdown_files

    docs = scan_markdown_files(docs_with_content, docs_with_content)
    cats = build_category_tree(docs)
    config = ServerConfig(docs_root=str(docs_with_content))
    server = DocumentationWebServer(config=config, documents=docs, categories=cats)
    return TestClient(server.app, raise_server_exceptions=False)


class TestDocsHome:
    """Test the /docs/ landing page."""

    def test_returns_html(self, web_client):
        r = web_client.get("/docs/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_contains_category_info(self, web_client):
        r = web_client.get("/docs/")
        assert "Guides" in r.text or "guides" in r.text.lower()

    def test_contains_doc_count(self, web_client):
        r = web_client.get("/docs/")
        assert "2" in r.text  # 2 documents


class TestDocsCategory:
    """Test the /docs/{category}/ page."""

    def test_valid_category(self, web_client):
        r = web_client.get("/docs/guides/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_invalid_category_returns_404(self, web_client):
        r = web_client.get("/docs/nonexistent/")
        assert r.status_code == 404

    def test_category_page_renders(self, web_client):
        r = web_client.get("/docs/guides/")
        assert "Guides" in r.text


class TestDocsDocument:
    """Test the /docs/{category}/{slug} page."""

    def test_valid_document(self, web_client):
        r = web_client.get("/docs/guides/getting-started")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_document_has_title(self, web_client):
        r = web_client.get("/docs/guides/getting-started")
        assert "<title>" in r.text
        assert "Getting Started" in r.text

    def test_document_has_rendered_html(self, web_client):
        """Content should be server-rendered, not raw markdown."""
        r = web_client.get("/docs/guides/getting-started")
        assert "<h1" in r.text or "<h2" in r.text
        assert "pip install" in r.text

    def test_document_has_breadcrumbs(self, web_client):
        r = web_client.get("/docs/guides/getting-started")
        assert "/docs/" in r.text  # home link in breadcrumbs

    def test_document_has_tags(self, web_client):
        r = web_client.get("/docs/guides/getting-started")
        assert "intro" in r.text

    def test_invalid_document_returns_404(self, web_client):
        r = web_client.get("/docs/guides/nonexistent")
        assert r.status_code == 404

    def test_prev_next_navigation(self, web_client):
        """Document should have prev/next links."""
        r = web_client.get("/docs/guides/getting-started")
        # Should have a link to the next doc (Advanced Usage)
        assert "Advanced" in r.text or "advanced" in r.text


class TestDocsSearch:
    """Test the /docs/search page."""

    def test_search_returns_html(self, web_client):
        r = web_client.get("/docs/search?q=installation")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_search_shows_results(self, web_client):
        r = web_client.get("/docs/search?q=Getting")
        assert r.status_code == 200
        assert "Getting Started" in r.text

    def test_empty_search(self, web_client):
        r = web_client.get("/docs/search")
        assert r.status_code == 200

    def test_no_results_search(self, web_client):
        r = web_client.get("/docs/search?q=zzzznonexistent")
        assert r.status_code == 200


class TestDocsTags:
    """Test the /docs/tags/ pages."""

    def test_all_tags_page(self, web_client):
        r = web_client.get("/docs/tags/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_specific_tag(self, web_client):
        r = web_client.get("/docs/tags/intro")
        assert r.status_code == 200
        assert "intro" in r.text

    def test_unknown_tag_shows_empty(self, web_client):
        r = web_client.get("/docs/tags/nonexistent")
        assert r.status_code == 200


class TestSEO:
    """Test SEO-related routes and metadata."""

    def test_sitemap_xml(self, web_client):
        r = web_client.get("/sitemap.xml")
        assert r.status_code == 200
        assert "application/xml" in r.headers["content-type"]
        assert "<urlset" in r.text
        assert "/docs/" in r.text

    def test_robots_txt(self, web_client):
        r = web_client.get("/robots.txt")
        assert r.status_code == 200
        assert "User-agent" in r.text
        assert "sitemap.xml" in r.text.lower()

    def test_document_has_meta_tags(self, web_client):
        r = web_client.get("/docs/guides/getting-started")
        assert "<title>" in r.text
        assert "Getting Started" in r.text


class TestHTMXPartials:
    """Test HTMX partial endpoints."""

    def test_search_partial_returns_html(self, web_client):
        r = web_client.get("/docs/_partials/search-results?q=Getting")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_search_partial_too_short(self, web_client):
        """Queries shorter than 2 chars return empty."""
        r = web_client.get("/docs/_partials/search-results?q=a")
        assert r.status_code == 200
        assert r.text == ""

    def test_search_partial_empty_query(self, web_client):
        r = web_client.get("/docs/_partials/search-results")
        assert r.status_code == 200


class TestAPIRoutesUnchanged:
    """Verify existing API routes still work."""

    def test_health(self, web_client):
        r = web_client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["documents"] == 2

    def test_api_search(self, web_client):
        r = web_client.get("/api/search?query=getting")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data

    def test_api_toc(self, web_client):
        r = web_client.get("/api/toc")
        assert r.status_code == 200

    def test_api_tags(self, web_client):
        r = web_client.get("/api/tags?include_counts=true")
        assert r.status_code == 200
