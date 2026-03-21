"""Integration tests for web server routing.

Verifies that the server routes requests correctly:
- / redirects to /docs/
- /docs/* serves server-rendered HTML pages
- /api/* returns JSON
- Unknown paths return 404
"""

import pytest
from fastapi.testclient import TestClient

from docs_mcp.core.config import ServerConfig
from docs_mcp.web.app import DocumentationWebServer


@pytest.fixture
def web_client(tmp_path):
    """Create a FastAPI TestClient backed by DocumentationWebServer."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    config = ServerConfig(docs_root=str(docs_root))
    server = DocumentationWebServer(config=config, documents=[], categories={})
    return TestClient(server.app, raise_server_exceptions=False)


class TestWebRouting:
    """Verify server routing for the new SSR architecture."""

    def test_root_redirects_to_docs(self, web_client):
        """GET / must redirect to /docs/."""
        response = web_client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/docs/"

    def test_docs_home_returns_html(self, web_client):
        """GET /docs/ must return the documentation landing page."""
        response = web_client.get("/docs/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_docs_search_returns_html(self, web_client):
        """GET /docs/search returns the search page."""
        response = web_client.get("/docs/search")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_docs_tags_returns_html(self, web_client):
        """GET /docs/tags/ returns the tags page."""
        response = web_client.get("/docs/tags/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_unknown_category_returns_404(self, web_client):
        """GET /docs/nonexistent/ returns 404."""
        response = web_client.get("/docs/nonexistent/")
        assert response.status_code == 404

    def test_api_routes_return_json(self, web_client):
        """API routes must return JSON, not HTML."""
        response = web_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_sitemap_returns_xml(self, web_client):
        """GET /sitemap.xml returns valid XML."""
        response = web_client.get("/sitemap.xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers.get("content-type", "")
        assert "<?xml" in response.text

    def test_robots_txt_returns_text(self, web_client):
        """GET /robots.txt returns a text file."""
        response = web_client.get("/robots.txt")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        assert "User-agent" in response.text
