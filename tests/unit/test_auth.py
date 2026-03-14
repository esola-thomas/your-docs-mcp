"""Unit tests for Bearer authentication middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from docs_mcp.security.auth import BearerAuthMiddleware

VALID_TOKEN = "test-secret-token-abc123"
VALID_TOKEN_2 = "another-valid-token-xyz"


def _make_app(tokens: list[str] | None = None) -> FastAPI:
    """Build a minimal FastAPI app with the auth middleware."""
    app = FastAPI()
    app.add_middleware(
        BearerAuthMiddleware,
        auth_tokens=tokens or [VALID_TOKEN],
    )

    @app.get("/api/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/api/toc")
    async def toc():
        return {"toc": []}

    @app.post("/api/search")
    async def search():
        return {"results": []}

    return app


@pytest.fixture
def auth_client() -> TestClient:
    """TestClient with auth middleware configured with a single token."""
    return TestClient(_make_app([VALID_TOKEN]))


@pytest.fixture
def multi_token_client() -> TestClient:
    """TestClient with auth middleware configured with multiple tokens."""
    return TestClient(_make_app([VALID_TOKEN, VALID_TOKEN_2]))


class TestHealthEndpointBypassesAuth:
    """Health check must remain accessible without authentication."""

    def test_health_no_header(self, auth_client: TestClient):
        response = auth_client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_with_invalid_token(self, auth_client: TestClient):
        response = auth_client.get(
            "/api/health",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 200


class TestMissingOrMalformedToken:
    """Requests without a valid Bearer header must receive 401."""

    def test_no_auth_header_returns_401(self, auth_client: TestClient):
        response = auth_client.get("/api/toc")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_empty_auth_header_returns_401(self, auth_client: TestClient):
        response = auth_client.get("/api/toc", headers={"Authorization": ""})
        assert response.status_code == 401

    def test_basic_auth_header_returns_401(self, auth_client: TestClient):
        response = auth_client.get(
            "/api/toc",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert response.status_code == 401

    def test_bearer_without_token_returns_401(self, auth_client: TestClient):
        response = auth_client.get(
            "/api/toc",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, auth_client: TestClient):
        response = auth_client.get(
            "/api/toc",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


class TestValidToken:
    """Requests with a valid Bearer token must be forwarded."""

    def test_valid_token_allows_get(self, auth_client: TestClient):
        response = auth_client.get(
            "/api/toc",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert response.status_code == 200

    def test_valid_token_allows_post(self, auth_client: TestClient):
        response = auth_client.post(
            "/api/search",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert response.status_code == 200

    def test_multiple_tokens_first(self, multi_token_client: TestClient):
        response = multi_token_client.get(
            "/api/toc",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert response.status_code == 200

    def test_multiple_tokens_second(self, multi_token_client: TestClient):
        response = multi_token_client.get(
            "/api/toc",
            headers={"Authorization": f"Bearer {VALID_TOKEN_2}"},
        )
        assert response.status_code == 200


class TestResponseBody:
    """Verify 401 response bodies contain helpful messages."""

    def test_missing_header_message(self, auth_client: TestClient):
        response = auth_client.get("/api/toc")
        body = response.json()
        assert "detail" in body
        assert "authorization" in body["detail"].lower()

    def test_invalid_token_message(self, auth_client: TestClient):
        response = auth_client.get(
            "/api/toc",
            headers={"Authorization": "Bearer bad"},
        )
        body = response.json()
        assert "detail" in body
        assert "token" in body["detail"].lower() or "invalid" in body["detail"].lower()
