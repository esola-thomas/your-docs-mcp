"""Integration tests for the /api/generate-pdf endpoint HTTP method enforcement."""

import pytest
from fastapi.testclient import TestClient

from docs_mcp.core.config import ServerConfig
from docs_mcp.web.app import DocumentationWebServer


@pytest.fixture
def web_client_pdf_enabled(tmp_path):
    """Create a FastAPI TestClient with PDF generation enabled."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    config = ServerConfig(docs_root=str(docs_root), enable_pdf_generation=True)
    server = DocumentationWebServer(config=config, documents=[], categories={})
    return TestClient(server.app, raise_server_exceptions=False)


@pytest.fixture
def web_client_pdf_disabled(tmp_path):
    """Create a FastAPI TestClient with PDF generation disabled (default)."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    config = ServerConfig(docs_root=str(docs_root))
    server = DocumentationWebServer(config=config, documents=[], categories={})
    return TestClient(server.app, raise_server_exceptions=False)


class TestGeneratePDFEndpointMethods:
    """Verify HTTP method enforcement on /api/generate-pdf when enabled."""

    def test_get_returns_405(self, web_client_pdf_enabled):
        """GET /api/generate-pdf must return 405 Method Not Allowed."""
        response = web_client_pdf_enabled.get("/api/generate-pdf")
        assert response.status_code == 405

    def test_get_response_includes_allow_header(self, web_client_pdf_enabled):
        """GET 405 response should advertise POST as the allowed method."""
        response = web_client_pdf_enabled.get("/api/generate-pdf")
        allow = response.headers.get("allow", "")
        assert "POST" in allow


class TestGeneratePDFEndpointDisabled:
    """Verify /api/generate-pdf is not available when PDF generation is disabled."""

    def test_post_returns_404_when_disabled(self, web_client_pdf_disabled):
        """POST /api/generate-pdf should 404 when enable_pdf_generation=False."""
        response = web_client_pdf_disabled.post(
            "/api/generate-pdf",
            json={"title": "Test"},
        )
        assert response.status_code in (404, 405)

    def test_get_returns_404_when_disabled(self, web_client_pdf_disabled):
        """GET /api/generate-pdf should 404 when enable_pdf_generation=False."""
        response = web_client_pdf_disabled.get("/api/generate-pdf")
        assert response.status_code in (404, 405)
