"""Unit tests for MCP server implementation."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from docs_mcp.config import ServerConfig
from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category
from docs_mcp.server import DocumentationMCPServer, serve, serve_both, serve_web_only


class TestDocumentationMCPServer:
    """Test DocumentationMCPServer class."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock server configuration."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        return ServerConfig(docs_root=str(docs_dir))

    @pytest.fixture
    def server(self, mock_config):
        """Create a server instance for testing."""
        return DocumentationMCPServer(mock_config)

    def test_server_initialization(self, server, mock_config):
        """Test that server initializes with correct configuration."""
        assert server.config == mock_config
        assert server.server is not None
        assert server.documents == []
        assert server.categories == {}

    def test_server_has_mcp_server_instance(self, server):
        """Test that server has an MCP Server instance."""
        from mcp.server import Server

        assert isinstance(server.server, Server)
        assert server.server.name == "hierarchical-docs-mcp"

    @pytest.mark.asyncio
    async def test_initialize_loads_documents(self, tmp_path):
        """Test that initialize loads documents from configured sources."""
        # Create test markdown files in a subdirectory to generate categories
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        guides_dir = docs_dir / "guides"
        guides_dir.mkdir()
        (guides_dir / "test.md").write_text("# Test\n\nContent")

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        await server.initialize()

        assert len(server.documents) > 0
        assert len(server.categories) > 0

    @pytest.mark.asyncio
    async def test_initialize_handles_missing_source_gracefully(self, tmp_path):
        """Test that initialize handles errors gracefully."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        # Mock scan_markdown_files to raise an exception
        with patch("docs_mcp.server.scan_markdown_files") as mock_scan:
            mock_scan.side_effect = Exception("Test error")

            # Should not raise, just log error
            await server.initialize()

            # Documents should be empty since scan failed
            assert len(server.documents) == 0

    @pytest.mark.asyncio
    async def test_initialize_builds_category_tree(self, tmp_path):
        """Test that initialize builds category tree from documents."""
        docs_dir = tmp_path / "docs"
        guides_dir = docs_dir / "guides"
        guides_dir.mkdir(parents=True)
        (guides_dir / "test.md").write_text("# Test\n\nContent")

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        await server.initialize()

        assert len(server.documents) > 0

    @pytest.mark.asyncio
    async def test_initialize_with_no_documents(self, tmp_path):
        """Test initialize with empty documentation directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        await server.initialize()

        assert server.documents == []
        assert server.categories == {}

    @pytest.mark.asyncio
    async def test_initialize_with_multiple_documents(self, tmp_path):
        """Test initialize with multiple documents."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "doc1.md").write_text("# Doc 1\n\nContent 1")
        (docs_dir / "doc2.md").write_text("# Doc 2\n\nContent 2")

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        await server.initialize()

        assert len(server.documents) == 2

    @pytest.mark.asyncio
    async def test_initialize_respects_config_settings(self, tmp_path):
        """Test that initialize respects configuration settings."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        hidden_dir = docs_dir / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "test.md").write_text("# Hidden")

        # With allow_hidden=False (default)
        config = ServerConfig(docs_root=str(docs_dir), allow_hidden=False)
        server = DocumentationMCPServer(config)
        await server.initialize()

        # Should not include hidden files
        hidden_docs = [d for d in server.documents if ".hidden" in str(d.file_path)]
        assert len(hidden_docs) == 0


class TestServeFunction:
    """Test serve function."""

    @pytest.mark.asyncio
    async def test_serve_creates_and_initializes_server(self, tmp_path):
        """Test that serve creates and initializes a server."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("# Test")

        config = ServerConfig(docs_root=str(docs_dir))

        # Mock the server's run method to avoid actually starting it
        with patch.object(DocumentationMCPServer, "run", new_callable=AsyncMock):
            with patch.object(
                DocumentationMCPServer, "initialize", new_callable=AsyncMock
            ) as mock_init:
                await serve(config)

                # Verify initialize was called
                mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_serve_runs_server(self, tmp_path):
        """Test that serve runs the server."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))

        # Mock the server methods
        with patch.object(DocumentationMCPServer, "run", new_callable=AsyncMock) as mock_run:
            with patch.object(DocumentationMCPServer, "initialize", new_callable=AsyncMock):
                await serve(config)

                # Verify run was called
                mock_run.assert_called_once()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_document(
    uri: str,
    title: str,
    content: str = "Content",
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


def _make_category(name: str, uri: str) -> Category:
    return Category(
        name=name,
        uri=uri,
        label=name.title(),
        depth=0,
        source_category=name,
        child_documents=[],
        child_categories=[],
        document_count=0,
    )


# ---------------------------------------------------------------------------
# serve_both tests
# ---------------------------------------------------------------------------


class TestServeBoth:
    """Test serve_both function."""

    @pytest.mark.asyncio
    async def test_serve_both_initializes_and_runs(self, tmp_path):
        """serve_both initializes the MCP server and calls both web and MCP servers."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        config = ServerConfig(docs_root=str(docs_dir))

        mock_uvicorn_server = AsyncMock()
        mock_uvicorn_server.serve = AsyncMock()
        mock_uvicorn_config = MagicMock()

        with patch.object(
            DocumentationMCPServer, "initialize", new_callable=AsyncMock
        ) as mock_init:
            with patch.object(
                DocumentationMCPServer, "run", new_callable=AsyncMock
            ) as mock_run:
                with patch("docs_mcp.web.DocumentationWebServer") as mock_web_cls:
                    mock_web_instance = MagicMock()
                    mock_web_instance.app = MagicMock()
                    mock_web_cls.return_value = mock_web_instance

                    with patch("uvicorn.Config", return_value=mock_uvicorn_config):
                        with patch("uvicorn.Server", return_value=mock_uvicorn_server):
                            await serve_both(config)

                mock_init.assert_called_once()
                mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_serve_both_creates_web_server(self, tmp_path):
        """serve_both creates a DocumentationWebServer with the loaded documents."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        config = ServerConfig(docs_root=str(docs_dir), enable_web_server=True)

        with patch.object(DocumentationMCPServer, "initialize", new_callable=AsyncMock):
            with patch.object(DocumentationMCPServer, "run", new_callable=AsyncMock):
                with patch("docs_mcp.web.DocumentationWebServer") as mock_web_cls:
                    mock_web_instance = MagicMock()
                    mock_web_instance.app = MagicMock()
                    mock_web_cls.return_value = mock_web_instance

                    with patch("uvicorn.Config", return_value=MagicMock()):
                        with patch(
                            "uvicorn.Server",
                            return_value=AsyncMock(serve=AsyncMock()),
                        ):
                            await serve_both(config)

                    mock_web_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_serve_both_with_web_disabled(self, tmp_path):
        """serve_both with enable_web_server=False skips web server creation."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        config = ServerConfig(docs_root=str(docs_dir), enable_web_server=False)

        with patch.object(DocumentationMCPServer, "initialize", new_callable=AsyncMock):
            with patch.object(DocumentationMCPServer, "run", new_callable=AsyncMock):
                with patch("docs_mcp.web.DocumentationWebServer") as mock_web_cls:
                    await serve_both(config)

                # Web server should not be created since enable_web_server=False
                mock_web_cls.assert_not_called()


# ---------------------------------------------------------------------------
# serve_web_only tests
# ---------------------------------------------------------------------------


class TestServeWebOnly:
    """Test serve_web_only function."""

    @pytest.mark.asyncio
    async def test_serve_web_only_initializes_and_runs_web_server(self, tmp_path):
        """serve_web_only initializes MCP server and starts web-only uvicorn."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        config = ServerConfig(docs_root=str(docs_dir))

        mock_uvicorn_server = AsyncMock()
        mock_uvicorn_server.serve = AsyncMock()

        with patch.object(
            DocumentationMCPServer, "initialize", new_callable=AsyncMock
        ) as mock_init:
            with patch("docs_mcp.web.DocumentationWebServer") as mock_web_cls:
                mock_web_instance = MagicMock()
                mock_web_instance.app = MagicMock()
                mock_web_cls.return_value = mock_web_instance

                with patch("uvicorn.Config", return_value=MagicMock()):
                    with patch("uvicorn.Server", return_value=mock_uvicorn_server):
                        await serve_web_only(config)

            mock_init.assert_called_once()
            mock_uvicorn_server.serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_serve_web_only_creates_web_server(self, tmp_path):
        """serve_web_only creates a DocumentationWebServer."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        config = ServerConfig(docs_root=str(docs_dir))

        with patch.object(DocumentationMCPServer, "initialize", new_callable=AsyncMock):
            with patch("docs_mcp.web.DocumentationWebServer") as mock_web_cls:
                mock_web_instance = MagicMock()
                mock_web_instance.app = MagicMock()
                mock_web_cls.return_value = mock_web_instance

                with patch("uvicorn.Config", return_value=MagicMock()):
                    with patch(
                        "uvicorn.Server",
                        return_value=AsyncMock(serve=AsyncMock()),
                    ):
                        await serve_web_only(config)

                mock_web_cls.assert_called_once()


# ---------------------------------------------------------------------------
# MCP handler dispatch tests
# ---------------------------------------------------------------------------


class TestMCPHandlerDispatch:
    """Test that MCP tool handlers are correctly registered and dispatch to tools."""

    @pytest.fixture
    def server_with_docs(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        config = ServerConfig(docs_root=str(docs_dir))
        srv = DocumentationMCPServer(config)
        srv.documents = [
            _make_document("docs://guides/intro", "Intro", "Introduction content", tags=["tutorial"]),
            _make_document("docs://api/auth", "Auth", "Authentication details", category="api"),
        ]
        srv.categories = {
            "docs://guides": _make_category("guides", "docs://guides"),
            "docs://api": _make_category("api", "docs://api"),
        }
        return srv

    @pytest.mark.asyncio
    async def test_call_tool_search_documentation(self, server_with_docs):
        """call_tool routes 'search_documentation' to the correct handler."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        with patch("docs_mcp.server.tools.handle_search_documentation", new_callable=AsyncMock) as m:
            m.return_value = [{"uri": "docs://guides/intro"}]
            req = CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="search_documentation", arguments={"query": "intro"}),
            )
            handler = server_with_docs.server.request_handlers[CallToolRequest]
            result = await handler(req)
            assert result.root.isError is False
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_navigate_to(self, server_with_docs):
        """call_tool routes 'navigate_to' to the correct handler."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        with patch("docs_mcp.server.tools.handle_navigate_to", new_callable=AsyncMock) as m:
            m.return_value = {"current": {"uri": "docs://guides"}}
            req = CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="navigate_to", arguments={"uri": "docs://guides"}),
            )
            result = await server_with_docs.server.request_handlers[CallToolRequest](req)
            assert result.root.isError is False
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_get_table_of_contents(self, server_with_docs):
        """call_tool routes 'get_table_of_contents' to the correct handler."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        with patch("docs_mcp.server.tools.handle_get_table_of_contents", new_callable=AsyncMock) as m:
            m.return_value = {"name": "root", "children": []}
            req = CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="get_table_of_contents", arguments={}),
            )
            result = await server_with_docs.server.request_handlers[CallToolRequest](req)
            assert result.root.isError is False
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_search_by_tags(self, server_with_docs):
        """call_tool routes 'search_by_tags' to the correct handler."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        with patch("docs_mcp.server.tools.handle_search_by_tags", new_callable=AsyncMock) as m:
            m.return_value = []
            req = CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="search_by_tags", arguments={"tags": ["tutorial"]}),
            )
            result = await server_with_docs.server.request_handlers[CallToolRequest](req)
            assert result.root.isError is False
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_get_document(self, server_with_docs):
        """call_tool routes 'get_document' to the correct handler."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        with patch("docs_mcp.server.tools.handle_get_document", new_callable=AsyncMock) as m:
            m.return_value = {"title": "Intro", "content": "..."}
            req = CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="get_document", arguments={"uri": "docs://guides/intro"}
                ),
            )
            result = await server_with_docs.server.request_handlers[CallToolRequest](req)
            assert result.root.isError is False
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_get_all_tags(self, server_with_docs):
        """call_tool routes 'get_all_tags' to the correct handler."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        with patch("docs_mcp.server.tools.handle_get_all_tags", new_callable=AsyncMock) as m:
            m.return_value = {"tags": ["tutorial"]}
            req = CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="get_all_tags", arguments={}),
            )
            result = await server_with_docs.server.request_handlers[CallToolRequest](req)
            assert result.root.isError is False
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_generate_pdf_release(self, server_with_docs):
        """call_tool routes 'generate_pdf_release' to the correct handler."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        with patch("docs_mcp.server.tools.handle_generate_pdf_release", new_callable=AsyncMock) as m:
            m.return_value = {"success": True}
            req = CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="generate_pdf_release", arguments={}),
            )
            result = await server_with_docs.server.request_handlers[CallToolRequest](req)
            assert result.root.isError is False
            m.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self, server_with_docs):
        """call_tool returns an error result for unknown tool names."""
        from mcp.types import CallToolRequest, CallToolRequestParams

        req = CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="unknown_tool_xyz", arguments={}),
        )
        result = await server_with_docs.server.request_handlers[CallToolRequest](req)
        # The MCP server catches the ValueError and returns isError=True
        assert result.root.isError is True

    @pytest.mark.asyncio
    async def test_list_resources_handler(self, server_with_docs):
        """list_resources handler returns a list of Resource objects."""
        from mcp.types import ListResourcesRequest, Resource

        with patch("docs_mcp.server.resources.list_resources", new_callable=AsyncMock) as m:
            m.return_value = [
                {"uri": "docs://guides/intro", "name": "Intro", "mimeType": "text/markdown"}
            ]
            req = ListResourcesRequest(method="resources/list", params=None)
            handler = server_with_docs.server.request_handlers[ListResourcesRequest]
            result = await handler(req)
            assert len(result.root.resources) == 1
            assert str(result.root.resources[0].uri) == "docs://guides/intro"

    @pytest.mark.asyncio
    async def test_read_resource_handler(self, server_with_docs):
        """read_resource handler returns document text."""
        from mcp.types import ReadResourceRequest, ReadResourceRequestParams

        with patch("docs_mcp.server.resources.handle_resource_read", new_callable=AsyncMock) as m:
            m.return_value = {"text": "# Intro\n\nIntroduction content"}
            req = ReadResourceRequest(
                method="resources/read",
                params=ReadResourceRequestParams(uri="docs://guides/intro"),
            )
            handler = server_with_docs.server.request_handlers[ReadResourceRequest]
            result = await handler(req)
            assert result.root.contents[0].text == "# Intro\n\nIntroduction content"

    @pytest.mark.asyncio
    async def test_read_resource_handler_with_error(self, server_with_docs):
        """read_resource handler propagates error when result contains an error key."""
        from mcp.types import ReadResourceRequest, ReadResourceRequestParams

        with patch("docs_mcp.server.resources.handle_resource_read", new_callable=AsyncMock) as m:
            m.return_value = {"error": "Document not found"}
            req = ReadResourceRequest(
                method="resources/read",
                params=ReadResourceRequestParams(uri="docs://nonexistent/doc"),
            )
            handler = server_with_docs.server.request_handlers[ReadResourceRequest]
            # The MCP server wraps the ValueError in an error response or re-raises it
            with pytest.raises(Exception):
                await handler(req)

    @pytest.mark.asyncio
    async def test_initialize_indexes_documents_in_vector_store(self, tmp_path):
        """initialize calls get_vector_store().add_documents when docs are loaded."""
        docs_dir = tmp_path / "docs"
        guides = docs_dir / "guides"
        guides.mkdir(parents=True)
        (guides / "intro.md").write_text("# Intro\n\nContent here")

        config = ServerConfig(docs_root=str(docs_dir))
        srv = DocumentationMCPServer(config)

        mock_store = MagicMock()
        with patch("docs_mcp.server.get_vector_store", return_value=mock_store):
            await srv.initialize()

        mock_store.add_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_handles_vector_store_exception(self, tmp_path):
        """initialize logs and continues when vector store indexing fails."""
        docs_dir = tmp_path / "docs"
        guides = docs_dir / "guides"
        guides.mkdir(parents=True)
        (guides / "intro.md").write_text("# Intro\n\nContent here")

        config = ServerConfig(docs_root=str(docs_dir))
        srv = DocumentationMCPServer(config)

        mock_store = MagicMock()
        mock_store.add_documents.side_effect = RuntimeError("vector store error")

        with patch("docs_mcp.server.get_vector_store", return_value=mock_store):
            # Should not raise; error is caught and logged
            await srv.initialize()

        assert len(srv.documents) > 0
