"""Unit tests for the web server (DocumentationWebServer and request models)."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from docs_mcp.config import ServerConfig
from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category
from docs_mcp.web import (
    DocumentationWebServer,
    GeneratePDFRequest,
    GetAllTagsRequest,
    GetDocumentRequest,
    NavigateRequest,
    SearchByTagsRequest,
    SearchRequest,
    TableOfContentsRequest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_document(
    uri: str,
    title: str,
    content: str = "Some content",
    category: str = "guides",
    tags: list[str] | None = None,
) -> Document:
    return Document(
        uri=uri,
        title=title,
        content=content,
        category=category,
        tags=tags or [],
        file_path=Path(f"/docs/{uri.replace('docs://', '')}.md"),
        relative_path=Path(f"{uri.replace('docs://', '')}.md"),
        size_bytes=len(content),
        last_modified=datetime.now(timezone.utc),
    )


def _make_category(name: str, uri: str, child_docs: list[str] | None = None) -> Category:
    return Category(
        name=name,
        uri=uri,
        label=name.title(),
        depth=0,
        source_category=name,
        child_documents=child_docs or [],
        child_categories=[],
        document_count=len(child_docs or []),
    )


@pytest.fixture
def docs_config(tmp_path: Path) -> ServerConfig:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    return ServerConfig(docs_root=str(docs_dir))


@pytest.fixture
def sample_documents() -> list[Document]:
    return [
        _make_document(
            "docs://guides/intro", "Intro", "Introduction to the system", tags=["beginner"]
        ),
        _make_document(
            "docs://api/auth", "Auth API", "Authentication details", category="api", tags=["security"]
        ),
    ]


@pytest.fixture
def sample_categories() -> dict[str, Category]:
    return {
        "docs://guides": _make_category("guides", "docs://guides", ["docs://guides/intro"]),
        "docs://api": _make_category("api", "docs://api", ["docs://api/auth"]),
    }


@pytest.fixture
def web_server(
    docs_config: ServerConfig,
    sample_documents: list[Document],
    sample_categories: dict[str, Category],
) -> DocumentationWebServer:
    return DocumentationWebServer(
        config=docs_config,
        documents=sample_documents,
        categories=sample_categories,
    )


@pytest.fixture
def client(web_server: DocumentationWebServer) -> TestClient:
    return TestClient(web_server.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Request model validation tests
# ---------------------------------------------------------------------------


class TestRequestModels:
    """Test Pydantic request models."""

    def test_search_request_defaults(self):
        r = SearchRequest(query="hello")
        assert r.query == "hello"
        assert r.category is None
        assert r.limit == 10

    def test_search_request_with_all_fields(self):
        r = SearchRequest(query="hello", category="guides", limit=5)
        assert r.category == "guides"
        assert r.limit == 5

    def test_navigate_request(self):
        r = NavigateRequest(uri="docs://guides/intro")
        assert r.uri == "docs://guides/intro"

    def test_table_of_contents_request_defaults(self):
        r = TableOfContentsRequest()
        assert r.max_depth is None

    def test_table_of_contents_request_with_depth(self):
        r = TableOfContentsRequest(max_depth=3)
        assert r.max_depth == 3

    def test_search_by_tags_request_defaults(self):
        r = SearchByTagsRequest(tags=["security"])
        assert r.tags == ["security"]
        assert r.category is None
        assert r.limit == 10

    def test_get_document_request(self):
        r = GetDocumentRequest(uri="docs://api/auth")
        assert r.uri == "docs://api/auth"

    def test_get_all_tags_request_defaults(self):
        r = GetAllTagsRequest()
        assert r.category is None
        assert r.include_counts is False

    def test_get_all_tags_request_with_counts(self):
        r = GetAllTagsRequest(include_counts=True)
        assert r.include_counts is True

    def test_generate_pdf_request_defaults(self):
        r = GeneratePDFRequest()
        assert r.title is None
        assert r.confidential is False

    def test_generate_pdf_request_with_fields(self):
        r = GeneratePDFRequest(title="My Doc", confidential=True, owner="Acme Corp")
        assert r.title == "My Doc"
        assert r.confidential is True
        assert r.owner == "Acme Corp"


# ---------------------------------------------------------------------------
# DocumentationWebServer initialization tests
# ---------------------------------------------------------------------------


class TestDocumentationWebServerInit:
    """Test DocumentationWebServer initialisation."""

    def test_server_stores_config(self, web_server, docs_config):
        assert web_server.config is docs_config

    def test_server_stores_documents(self, web_server, sample_documents):
        assert web_server.documents is sample_documents

    def test_server_stores_categories(self, web_server, sample_categories):
        assert web_server.categories is sample_categories

    def test_server_creates_fastapi_app(self, web_server):
        from fastapi import FastAPI

        assert isinstance(web_server.app, FastAPI)

    def test_server_creates_mcp_server(self, web_server):
        from mcp.server import Server

        assert isinstance(web_server.mcp_server, Server)
        assert web_server.mcp_server.name == "hierarchical-docs-mcp"

    def test_server_creates_sse_transport(self, web_server):
        from mcp.server.sse import SseServerTransport

        assert isinstance(web_server.sse_transport, SseServerTransport)

    def test_server_works_with_empty_data(self, docs_config):
        server = DocumentationWebServer(config=docs_config, documents=[], categories={})
        assert server.documents == []
        assert server.categories == {}


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Test GET /api/health."""

    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_returns_healthy_status(self, client):
        data = client.get("/api/health").json()
        assert data["status"] == "healthy"

    def test_health_returns_document_count(self, client, sample_documents):
        data = client.get("/api/health").json()
        assert data["documents"] == len(sample_documents)

    def test_health_returns_category_count(self, client, sample_categories):
        data = client.get("/api/health").json()
        assert data["categories"] == len(sample_categories)


# ---------------------------------------------------------------------------
# Search endpoints (GET and POST)
# ---------------------------------------------------------------------------


class TestSearchEndpoints:
    """Test GET /api/search and POST /api/search."""

    @pytest.fixture(autouse=True)
    def _mock_search(self):
        with patch("docs_mcp.web.tools.handle_search_documentation", new_callable=AsyncMock) as m:
            m.return_value = [{"uri": "docs://guides/intro", "title": "Intro"}]
            self._mock = m
            yield

    def test_post_search_returns_200(self, client):
        resp = client.post("/api/search", json={"query": "hello"})
        assert resp.status_code == 200

    def test_post_search_returns_results(self, client):
        data = client.post("/api/search", json={"query": "hello"}).json()
        assert "results" in data
        assert len(data["results"]) == 1

    def test_post_search_passes_query(self, client):
        client.post("/api/search", json={"query": "hello", "category": "guides", "limit": 5})
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["query"] == "hello"
        assert call_args["arguments"]["category"] == "guides"
        assert call_args["arguments"]["limit"] == 5

    def test_get_search_returns_200(self, client):
        resp = client.get("/api/search?query=hello")
        assert resp.status_code == 200

    def test_get_search_returns_results(self, client):
        data = client.get("/api/search?query=hello").json()
        assert "results" in data
        assert len(data["results"]) == 1

    def test_get_search_accepts_optional_params(self, client):
        client.get("/api/search?query=hello&category=guides&limit=3")
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["category"] == "guides"
        assert call_args["arguments"]["limit"] == 3

    def test_post_search_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.post("/api/search", json={"query": "hello"})
        assert resp.status_code == 500

    def test_get_search_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.get("/api/search?query=hello")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Navigate endpoints (GET and POST)
# ---------------------------------------------------------------------------


class TestNavigateEndpoints:
    """Test GET /api/navigate and POST /api/navigate."""

    @pytest.fixture(autouse=True)
    def _mock_navigate(self):
        with patch("docs_mcp.web.tools.handle_navigate_to", new_callable=AsyncMock) as m:
            m.return_value = {"current": {"uri": "docs://guides"}, "children": []}
            self._mock = m
            yield

    def test_post_navigate_returns_200(self, client):
        resp = client.post("/api/navigate", json={"uri": "docs://guides"})
        assert resp.status_code == 200

    def test_post_navigate_result_structure(self, client):
        data = client.post("/api/navigate", json={"uri": "docs://guides"}).json()
        assert "current" in data

    def test_get_navigate_returns_200(self, client):
        resp = client.get("/api/navigate?uri=docs://guides")
        assert resp.status_code == 200

    def test_post_navigate_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.post("/api/navigate", json={"uri": "docs://guides"})
        assert resp.status_code == 500

    def test_get_navigate_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.get("/api/navigate?uri=docs://guides")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Table of Contents endpoints (GET and POST)
# ---------------------------------------------------------------------------


class TestTocEndpoints:
    """Test GET /api/toc and POST /api/toc."""

    @pytest.fixture(autouse=True)
    def _mock_toc(self):
        with patch("docs_mcp.web.tools.handle_get_table_of_contents", new_callable=AsyncMock) as m:
            m.return_value = {"name": "root", "children": []}
            self._mock = m
            yield

    def test_post_toc_returns_200(self, client):
        resp = client.post("/api/toc", json={})
        assert resp.status_code == 200

    def test_post_toc_with_max_depth(self, client):
        client.post("/api/toc", json={"max_depth": 2})
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["max_depth"] == 2

    def test_get_toc_returns_200(self, client):
        resp = client.get("/api/toc")
        assert resp.status_code == 200

    def test_get_toc_with_max_depth_param(self, client):
        client.get("/api/toc?max_depth=3")
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["max_depth"] == 3

    def test_post_toc_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.post("/api/toc", json={})
        assert resp.status_code == 500

    def test_get_toc_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.get("/api/toc")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Search by tags endpoints (POST only)
# ---------------------------------------------------------------------------


class TestSearchByTagsEndpoints:
    """Test POST /api/search-by-tags."""

    @pytest.fixture(autouse=True)
    def _mock_tags_search(self):
        with patch("docs_mcp.web.tools.handle_search_by_tags", new_callable=AsyncMock) as m:
            m.return_value = [{"uri": "docs://guides/intro", "title": "Intro"}]
            self._mock = m
            yield

    def test_post_search_by_tags_returns_200(self, client):
        resp = client.post("/api/search-by-tags", json={"tags": ["security"]})
        assert resp.status_code == 200

    def test_post_search_by_tags_returns_results(self, client):
        data = client.post("/api/search-by-tags", json={"tags": ["security"]}).json()
        assert "results" in data
        assert len(data["results"]) == 1

    def test_post_search_by_tags_passes_tags(self, client):
        client.post("/api/search-by-tags", json={"tags": ["security", "api"], "category": "api"})
        call_args = self._mock.call_args[1]
        assert "security" in call_args["arguments"]["tags"]
        assert call_args["arguments"]["category"] == "api"

    def test_post_search_by_tags_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.post("/api/search-by-tags", json={"tags": ["x"]})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Document endpoints (GET and POST)
# ---------------------------------------------------------------------------


class TestDocumentEndpoints:
    """Test GET /api/document and POST /api/document."""

    @pytest.fixture(autouse=True)
    def _mock_get_doc(self):
        with patch("docs_mcp.web.tools.handle_get_document", new_callable=AsyncMock) as m:
            m.return_value = {
                "uri": "docs://guides/intro",
                "title": "Intro",
                "content": "Hello world",
            }
            self._mock = m
            yield

    def test_post_document_returns_200(self, client):
        resp = client.post("/api/document", json={"uri": "docs://guides/intro"})
        assert resp.status_code == 200

    def test_post_document_returns_content(self, client):
        data = client.post("/api/document", json={"uri": "docs://guides/intro"}).json()
        assert data["title"] == "Intro"
        assert data["content"] == "Hello world"

    def test_get_document_returns_200(self, client):
        resp = client.get("/api/document?uri=docs://guides/intro")
        assert resp.status_code == 200

    def test_post_document_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.post("/api/document", json={"uri": "docs://guides/intro"})
        assert resp.status_code == 500

    def test_get_document_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.get("/api/document?uri=docs://guides/intro")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Tags endpoints (GET and POST)
# ---------------------------------------------------------------------------


class TestTagsEndpoints:
    """Test GET /api/tags and POST /api/tags."""

    @pytest.fixture(autouse=True)
    def _mock_get_tags(self):
        with patch("docs_mcp.web.tools.handle_get_all_tags", new_callable=AsyncMock) as m:
            m.return_value = {"tags": ["security", "beginner"]}
            self._mock = m
            yield

    def test_post_tags_returns_200(self, client):
        resp = client.post("/api/tags", json={})
        assert resp.status_code == 200

    def test_post_tags_with_include_counts(self, client):
        client.post("/api/tags", json={"include_counts": True})
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["include_counts"] is True

    def test_get_tags_returns_200(self, client):
        resp = client.get("/api/tags")
        assert resp.status_code == 200

    def test_get_tags_with_params(self, client):
        client.get("/api/tags?category=guides&include_counts=true")
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["category"] == "guides"
        assert call_args["arguments"]["include_counts"] is True

    def test_post_tags_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.post("/api/tags", json={})
        assert resp.status_code == 500

    def test_get_tags_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.get("/api/tags")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Generate PDF endpoints (GET and POST)
# ---------------------------------------------------------------------------


class TestGeneratePdfEndpoints:
    """Test GET /api/generate-pdf and POST /api/generate-pdf."""

    @pytest.fixture(autouse=True)
    def _mock_pdf(self):
        with patch("docs_mcp.web.tools.handle_generate_pdf_release", new_callable=AsyncMock) as m:
            m.return_value = {"success": True, "path": "/tmp/docs.pdf"}
            self._mock = m
            yield

    def test_post_pdf_returns_200(self, client):
        resp = client.post("/api/generate-pdf", json={})
        assert resp.status_code == 200

    def test_post_pdf_returns_result(self, client):
        data = client.post("/api/generate-pdf", json={}).json()
        assert data["success"] is True

    def test_post_pdf_passes_args(self, client):
        client.post(
            "/api/generate-pdf",
            json={"title": "My Doc", "confidential": True, "owner": "Acme"},
        )
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["title"] == "My Doc"
        assert call_args["arguments"]["confidential"] is True
        assert call_args["arguments"]["owner"] == "Acme"

    def test_get_pdf_returns_200(self, client):
        resp = client.get("/api/generate-pdf")
        assert resp.status_code == 200

    def test_get_pdf_passes_args(self, client):
        client.get("/api/generate-pdf?title=MyDoc&confidential=true&owner=Acme")
        call_args = self._mock.call_args[1]
        assert call_args["arguments"]["title"] == "MyDoc"
        assert call_args["arguments"]["confidential"] is True
        assert call_args["arguments"]["owner"] == "Acme"

    def test_post_pdf_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.post("/api/generate-pdf", json={})
        assert resp.status_code == 500

    def test_get_pdf_error_returns_500(self, client):
        self._mock.side_effect = RuntimeError("boom")
        resp = client.get("/api/generate-pdf")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Root (HTML) endpoint
# ---------------------------------------------------------------------------


class TestRootEndpoint:
    """Test GET / (static HTML file serving)."""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_returns_html_content_type(self, client):
        resp = client.get("/")
        assert "text/html" in resp.headers.get("content-type", "")
