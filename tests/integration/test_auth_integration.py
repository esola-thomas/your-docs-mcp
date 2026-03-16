"""Integration tests for authentication on the DocumentationWebServer."""

import pytest
from fastapi.testclient import TestClient

from docs_mcp.config import ServerConfig
from docs_mcp.web import DocumentationWebServer

VALID_TOKEN = "integration-test-token"


@pytest.fixture
def auth_web_client(tmp_path) -> TestClient:
    """DocumentationWebServer with authentication enabled."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    config = ServerConfig(
        docs_root=str(docs_root),
        auth_enabled=True,
        auth_tokens=VALID_TOKEN,
    )
    server = DocumentationWebServer(config=config, documents=[], categories={})
    return TestClient(server.app, raise_server_exceptions=False)


@pytest.fixture
def noauth_web_client(tmp_path) -> TestClient:
    """DocumentationWebServer with authentication disabled (default)."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    config = ServerConfig(docs_root=str(docs_root))
    server = DocumentationWebServer(config=config, documents=[], categories={})
    return TestClient(server.app, raise_server_exceptions=False)


class TestAuthEnabled:
    """When auth is enabled, endpoints require a valid Bearer token."""

    def test_health_accessible_without_token(self, auth_web_client: TestClient):
        response = auth_web_client.get("/api/health")
        assert response.status_code == 200

    def test_api_toc_requires_token(self, auth_web_client: TestClient):
        response = auth_web_client.get("/api/toc")
        assert response.status_code == 401

    def test_api_toc_with_valid_token(self, auth_web_client: TestClient):
        response = auth_web_client.get(
            "/api/toc",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert response.status_code == 200

    def test_api_search_requires_token(self, auth_web_client: TestClient):
        response = auth_web_client.get("/api/search?query=test")
        assert response.status_code == 401

    def test_api_search_with_valid_token(self, auth_web_client: TestClient):
        response = auth_web_client.get(
            "/api/search?query=test",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert response.status_code == 200

    def test_invalid_token_returns_401(self, auth_web_client: TestClient):
        response = auth_web_client.get(
            "/api/toc",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401


class TestAuthDisabledByDefault:
    """When auth is disabled (default), all endpoints are open."""

    def test_health_accessible(self, noauth_web_client: TestClient):
        response = noauth_web_client.get("/api/health")
        assert response.status_code == 200

    def test_api_toc_accessible(self, noauth_web_client: TestClient):
        response = noauth_web_client.get("/api/toc")
        assert response.status_code == 200

    def test_api_search_accessible(self, noauth_web_client: TestClient):
        response = noauth_web_client.get("/api/search?query=test")
        assert response.status_code == 200


class TestAuthConfigIntegration:
    """Configuration-level auth settings integration tests."""

    def test_auth_disabled_by_default(self):
        config = ServerConfig()
        assert config.auth_enabled is False
        assert config.auth_token_list == []

    def test_auth_tokens_from_comma_string(self):
        config = ServerConfig(auth_tokens="tok1,tok2,tok3")
        assert config.auth_token_list == ["tok1", "tok2", "tok3"]

    def test_auth_tokens_empty_string(self):
        config = ServerConfig(auth_tokens="")
        assert config.auth_token_list == []

    def test_auth_tokens_strips_whitespace(self):
        config = ServerConfig(auth_tokens=" tok1 , tok2 ")
        assert config.auth_token_list == ["tok1", "tok2"]

    def test_auth_from_env_vars(self, monkeypatch):
        monkeypatch.setenv("MCP_DOCS_AUTH_ENABLED", "true")
        monkeypatch.setenv("MCP_DOCS_AUTH_TOKENS", "env-token-1,env-token-2")
        config = ServerConfig()
        assert config.auth_enabled is True
        assert config.auth_token_list == ["env-token-1", "env-token-2"]

    def test_auth_enabled_without_tokens_raises(self, tmp_path):
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        config = ServerConfig(docs_root=str(docs_root), auth_enabled=True, auth_tokens="")
        with pytest.raises(ValueError, match="no tokens are configured"):
            DocumentationWebServer(config=config, documents=[], categories={})
