"""Unit tests for MCP server implementation."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hierarchical_docs_mcp.config import ServerConfig
from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.models.navigation import Category
from hierarchical_docs_mcp.server import DocumentationMCPServer, serve


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
        with patch("hierarchical_docs_mcp.server.scan_markdown_files") as mock_scan:
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


class TestServerHandlers:
    """Test server handler registration and functionality."""

    @pytest.fixture
    def server_with_data(self, tmp_path):
        """Create a server with sample data."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        # Add sample documents
        server.documents = [
            Document(
                uri="docs://test/doc1",
                title="Test Doc 1",
                content="Content 1",
                category="test",
                tags=["tag1"],
                file_path="/test/doc1.md",
                last_modified=datetime.now(timezone.utc),
            )
        ]

        # Add sample categories
        server.categories = {
            "docs://test": Category(
                uri="docs://test",
                label="Test",
                child_documents=["docs://test/doc1"],
                child_categories=[],
                document_count=1,
            )
        }

        return server

    @pytest.mark.asyncio
    async def test_list_tools_handler(self, server_with_data):
        """Test that list_tools handler returns all tools."""
        # Get the list_tools handler
        handlers = server_with_data.server._list_tools_handlers
        assert len(handlers) > 0

        # Call the handler
        tools = await handlers[0]()

        assert len(tools) == 5
        tool_names = [t.name for t in tools]
        assert "search_documentation" in tool_names
        assert "navigate_to" in tool_names
        assert "get_table_of_contents" in tool_names
        assert "search_by_tags" in tool_names
        assert "get_document" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_search_documentation(self, server_with_data):
        """Test call_tool handler for search_documentation."""
        with patch("hierarchical_docs_mcp.handlers.tools.handle_search_documentation") as mock:
            mock.return_value = [{"uri": "docs://test", "title": "Test"}]

            handlers = server_with_data.server._call_tool_handlers
            result = await handlers[0]("search_documentation", {"query": "test"})

            assert len(result) > 0
            assert result[0]["type"] == "text"
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_navigate_to(self, server_with_data):
        """Test call_tool handler for navigate_to."""
        with patch("hierarchical_docs_mcp.handlers.tools.handle_navigate_to") as mock:
            mock.return_value = {"current_uri": "docs://test"}

            handlers = server_with_data.server._call_tool_handlers
            result = await handlers[0]("navigate_to", {"uri": "docs://test"})

            assert len(result) > 0
            assert result[0]["type"] == "text"
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_get_table_of_contents(self, server_with_data):
        """Test call_tool handler for get_table_of_contents."""
        with patch("hierarchical_docs_mcp.handlers.tools.handle_get_table_of_contents") as mock:
            mock.return_value = {"root": []}

            handlers = server_with_data.server._call_tool_handlers
            result = await handlers[0]("get_table_of_contents", {})

            assert len(result) > 0
            assert result[0]["type"] == "text"
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_search_by_tags(self, server_with_data):
        """Test call_tool handler for search_by_tags."""
        with patch("hierarchical_docs_mcp.handlers.tools.handle_search_by_tags") as mock:
            mock.return_value = [{"uri": "docs://test"}]

            handlers = server_with_data.server._call_tool_handlers
            result = await handlers[0]("search_by_tags", {"tags": ["tag1"]})

            assert len(result) > 0
            assert result[0]["type"] == "text"
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_get_document(self, server_with_data):
        """Test call_tool handler for get_document."""
        with patch("hierarchical_docs_mcp.handlers.tools.handle_get_document") as mock:
            mock.return_value = {"uri": "docs://test", "content": "Test"}

            handlers = server_with_data.server._call_tool_handlers
            result = await handlers[0]("get_document", {"uri": "docs://test"})

            assert len(result) > 0
            assert result[0]["type"] == "text"
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self, server_with_data):
        """Test call_tool handler raises error for unknown tool."""
        handlers = server_with_data.server._call_tool_handlers

        with pytest.raises(ValueError, match="Unknown tool"):
            await handlers[0]("unknown_tool", {})

    @pytest.mark.asyncio
    async def test_list_resources_handler(self, server_with_data):
        """Test that list_resources handler works."""
        handlers = server_with_data.server._list_resources_handlers
        assert len(handlers) > 0

        resources = await handlers[0]()

        assert len(resources) > 0
        # Should have at least root + categories + documents
        assert any(r.uri == "docs://" for r in resources)

    @pytest.mark.asyncio
    async def test_read_resource_handler(self, server_with_data):
        """Test that read_resource handler works."""
        handlers = server_with_data.server._read_resource_handlers
        assert len(handlers) > 0

        # Read a document
        content = await handlers[0]("docs://test/doc1")

        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_read_resource_handler_error(self, server_with_data):
        """Test that read_resource handler raises error for invalid resource."""
        handlers = server_with_data.server._read_resource_handlers

        with pytest.raises(ValueError):
            await handlers[0]("docs://nonexistent")
