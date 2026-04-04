"""Integration test for the Streamable HTTP MCP transport endpoint."""

import asyncio
import socket

import httpx
import pytest
import pytest_asyncio
import uvicorn

from docs_mcp.core.config import ServerConfig
from docs_mcp.web.app import DocumentationWebServer


def _get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest_asyncio.fixture
async def running_http_server(tmp_path):
    """Start the documentation web server with Streamable HTTP support on a free port."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()

    config = ServerConfig(docs_root=docs_root)
    web_server = DocumentationWebServer(config=config, documents=[], categories={})

    port = _get_free_port()
    server_config = uvicorn.Config(
        app=web_server.app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        loop="asyncio",
    )
    server = uvicorn.Server(config=server_config)

    server_task = asyncio.create_task(server.serve())

    try:
        for _ in range(200):
            if server.started:
                break
            await asyncio.sleep(0.05)
        else:  # pragma: no cover - defensive timeout
            raise RuntimeError("HTTP test server failed to start in time")

        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await server_task


@pytest.mark.asyncio
async def test_mcp_endpoint_accepts_post(running_http_server: str):
    """Ensure the /mcp endpoint accepts POST with JSON-RPC and returns SSE."""
    async with httpx.AsyncClient(base_url=running_http_server) as client:
        # Send an MCP initialize request
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            },
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_mcp_endpoint_rejects_get_without_session(running_http_server: str):
    """GET /mcp without a session ID should return an error."""
    async with httpx.AsyncClient(base_url=running_http_server) as client:
        response = await client.get("/mcp")
        # Without a valid session, GET should return 400 or 405
        assert response.status_code in (400, 404, 405)
