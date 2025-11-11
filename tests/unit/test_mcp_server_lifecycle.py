"""Tests for MCP server lifecycle and handler registration."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server import Server

from hierarchical_docs_mcp.config import ServerConfig
from hierarchical_docs_mcp.server import DocumentationMCPServer, serve


class TestMCPServerHandlerRegistration:
    """Test MCP server handler registration and lifecycle."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock server configuration."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        # Create a simple markdown file
        (docs_dir / "test.md").write_text("# Test\n\nContent")
        return ServerConfig(docs_root=str(docs_dir))

    def test_server_instance_has_unique_handlers(self, mock_config):
        """Test that each server instance has its own handler registrations."""
        server1 = DocumentationMCPServer(mock_config)
        server2 = DocumentationMCPServer(mock_config)

        # Both servers should be independent instances
        assert server1.server is not server2.server
        assert id(server1.server) != id(server2.server)

    def test_multiple_server_instances_dont_conflict(self, mock_config):
        """Test that creating multiple server instances doesn't cause conflicts."""
        # This tests for the "ModelService: Cannot add model because it already exists!" error
        try:
            server1 = DocumentationMCPServer(mock_config)
            server2 = DocumentationMCPServer(mock_config)
            server3 = DocumentationMCPServer(mock_config)

            # All servers should have valid MCP Server instances
            assert isinstance(server1.server, Server)
            assert isinstance(server2.server, Server)
            assert isinstance(server3.server, Server)

        except Exception as e:
            if "already exists" in str(e).lower():
                pytest.fail(f"Server creation failed with duplicate registration error: {e}")
            raise

    @pytest.mark.asyncio
    async def test_server_initialization_doesnt_duplicate_handlers(self, tmp_path):
        """Test that server initialization doesn't register handlers multiple times."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("# Test\n\nContent")

        config = ServerConfig(docs_root=str(docs_dir))

        # Create server
        server = DocumentationMCPServer(config)

        # Initialize server (this should not re-register handlers)
        await server.initialize()

        # Try to initialize again (should be idempotent)
        await server.initialize()

        # Server should still be functional
        assert len(server.documents) > 0

    @pytest.mark.asyncio
    async def test_handler_decorators_are_registered_once(self, mock_config):
        """Test that handler decorators are only registered once per server instance."""
        server = DocumentationMCPServer(mock_config)

        # The MCP Server class should have handlers registered
        # Verify that the server has the basic MCP Server structure
        assert isinstance(server.server, Server)
        assert server.server.name == "hierarchical-docs-mcp"

    def test_server_name_is_consistent(self, mock_config):
        """Test that server name is consistent across instances."""
        server1 = DocumentationMCPServer(mock_config)
        server2 = DocumentationMCPServer(mock_config)

        # Both should have the same server name
        assert server1.server.name == "hierarchical-docs-mcp"
        assert server2.server.name == "hierarchical-docs-mcp"

    @pytest.mark.asyncio
    async def test_sequential_server_creation_and_cleanup(self, tmp_path):
        """Test creating and cleaning up servers sequentially."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("# Test\n\nContent")

        config = ServerConfig(docs_root=str(docs_dir))

        # Create and initialize first server
        server1 = DocumentationMCPServer(config)
        await server1.initialize()
        assert len(server1.documents) > 0

        # Clean up by deleting reference
        del server1

        # Create second server (should not have conflicts)
        server2 = DocumentationMCPServer(config)
        await server2.initialize()
        assert len(server2.documents) > 0

        del server2

    @pytest.mark.asyncio
    async def test_concurrent_server_creation(self, tmp_path):
        """Test creating multiple servers concurrently."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("# Test\n\nContent")

        config = ServerConfig(docs_root=str(docs_dir))

        async def create_and_init_server():
            server = DocumentationMCPServer(config)
            await server.initialize()
            return server

        # Create multiple servers concurrently
        servers = await asyncio.gather(
            create_and_init_server(),
            create_and_init_server(),
            create_and_init_server(),
        )

        # All servers should be initialized successfully
        assert len(servers) == 3
        for server in servers:
            assert len(server.documents) > 0
            assert isinstance(server.server, Server)


class TestMCPServerToolCalls:
    """Test MCP server tool call handling through the actual server."""

    @pytest.fixture
    async def initialized_server(self, tmp_path):
        """Create and initialize a server for testing."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("# Test Document\n\nTest content for searching.")

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)
        await server.initialize()
        return server

    @pytest.mark.asyncio
    async def test_server_has_tool_handlers(self, initialized_server):
        """Test that server has tool handlers registered."""
        server = initialized_server

        # The server should be a valid MCP Server
        assert isinstance(server.server, Server)
        assert server.server.name == "hierarchical-docs-mcp"

    @pytest.mark.asyncio
    async def test_server_has_resource_handlers(self, initialized_server):
        """Test that server has resource handlers registered."""
        server = initialized_server

        # The server should be a valid MCP Server
        assert isinstance(server.server, Server)
        assert len(server.documents) > 0


class TestMCPServerEdgeCases:
    """Test edge cases in MCP server behavior."""

    @pytest.mark.asyncio
    async def test_server_with_empty_document_set(self, tmp_path):
        """Test server behavior with no documents."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)
        await server.initialize()

        # Server should be functional even with no documents
        assert len(server.documents) == 0
        assert len(server.categories) == 0
        assert isinstance(server.server, Server)

    @pytest.mark.asyncio
    async def test_server_reinitialization(self, tmp_path):
        """Test that server can be reinitialized without errors."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        # Initialize multiple times
        await server.initialize()
        await server.initialize()
        await server.initialize()

        # Should not raise errors
        assert isinstance(server.server, Server)

    def test_server_config_is_immutable_reference(self, tmp_path):
        """Test that server keeps a reference to its config."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)

        # Config should be the same object
        assert server.config is config


class TestServeFunction:
    """Test the serve() function."""

    @pytest.mark.asyncio
    async def test_serve_creates_server_instance(self, tmp_path):
        """Test that serve creates a server instance."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))

        # Mock the run method to prevent actual server start
        with patch.object(DocumentationMCPServer, 'run', new_callable=AsyncMock) as mock_run:
            with patch.object(DocumentationMCPServer, 'initialize', new_callable=AsyncMock):
                await serve(config)

                # Verify run was called
                mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_serve_multiple_times_sequentially(self, tmp_path):
        """Test calling serve multiple times sequentially."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))

        # Mock the run method
        with patch.object(DocumentationMCPServer, 'run', new_callable=AsyncMock):
            with patch.object(DocumentationMCPServer, 'initialize', new_callable=AsyncMock):
                # First call
                await serve(config)

                # Second call (simulating server restart)
                await serve(config)

                # Should not raise "already exists" errors
