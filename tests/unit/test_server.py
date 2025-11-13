"""Unit tests for MCP server implementation."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

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



