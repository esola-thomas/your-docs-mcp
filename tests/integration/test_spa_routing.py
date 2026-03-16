"""Integration tests for client-side SPA routing (History API deep-linking).

The server must return index.html for any path that is not an API endpoint or
a static-file path so that the JavaScript router can handle navigation.
"""

import pytest
from fastapi.testclient import TestClient

from docs_mcp.config import ServerConfig
from docs_mcp.web import DocumentationWebServer


@pytest.fixture
def web_client(tmp_path):
    """Create a FastAPI TestClient backed by DocumentationWebServer."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    config = ServerConfig(docs_root=str(docs_root))
    server = DocumentationWebServer(config=config, documents=[], categories={})
    return TestClient(server.app, raise_server_exceptions=False)


class TestSPACatchAllRoute:
    """Verify the catch-all route serves index.html for SPA deep-links."""

    def test_root_path_returns_index(self, web_client):
        """GET / must return the SPA index page."""
        response = web_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_known_view_path_returns_index(self, web_client):
        """GET /toc (a named SPA view) must return the SPA index page."""
        response = web_client.get("/toc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_search_view_path_returns_index(self, web_client):
        """GET /search must return the SPA index page."""
        response = web_client.get("/search")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_tags_view_path_returns_index(self, web_client):
        """GET /tags must return the SPA index page."""
        response = web_client.get("/tags")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_release_view_path_returns_index(self, web_client):
        """GET /release must return the SPA index page."""
        response = web_client.get("/release")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_doc_path_returns_index(self, web_client):
        """GET /doc/guides/getting-started must return the SPA index page."""
        response = web_client.get("/doc/guides/getting-started")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_deep_doc_path_returns_index(self, web_client):
        """GET /doc/api/v2/endpoints/users must return the SPA index page."""
        response = web_client.get("/doc/api/v2/endpoints/users")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_unknown_path_returns_index(self, web_client):
        """GET /some/arbitrary/path must return the SPA index page."""
        response = web_client.get("/some/arbitrary/path")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_api_routes_not_intercepted(self, web_client):
        """API routes must NOT be intercepted by the catch-all route."""
        response = web_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_index_html_content_served(self, web_client):
        """The catch-all response body must contain the SPA HTML."""
        response = web_client.get("/doc/guides/intro")
        assert response.status_code == 200
        # The SPA HTML must load the JavaScript bundle
        assert "app.js" in response.text
