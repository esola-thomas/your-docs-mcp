"""Integration tests for the /api/generate-pdf endpoint HTTP method enforcement."""

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


class TestGeneratePDFEndpointMethods:
    """Verify HTTP method enforcement on /api/generate-pdf."""

    def test_get_returns_405(self, web_client):
        """GET /api/generate-pdf must return 405 Method Not Allowed."""
        response = web_client.get("/api/generate-pdf")
        assert response.status_code == 405

    def test_get_response_includes_allow_header(self, web_client):
        """GET 405 response should advertise POST as the allowed method."""
        response = web_client.get("/api/generate-pdf")
        allow = response.headers.get("allow", "")
        assert "POST" in allow
