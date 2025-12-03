"""Integration test for the SSE transport endpoints."""

import asyncio
import socket

import httpx
import pytest
import pytest_asyncio
import uvicorn

from docs_mcp.config import ServerConfig
from docs_mcp.web import DocumentationWebServer


def _get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest_asyncio.fixture
async def running_sse_server(tmp_path):
    """Start the documentation web server with SSE support on a free port."""
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
            raise RuntimeError("SSE test server failed to start in time")

        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await server_task


@pytest.mark.asyncio
async def test_sse_endpoint_returns_event_stream(running_sse_server: str):
    """Ensure the SSE endpoint emits the expected endpoint event."""
    async with httpx.AsyncClient(base_url=running_sse_server) as client:
        async with client.stream("GET", "/sse") as response:
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type

            lines: list[str] = []

            async def read_lines() -> None:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    lines.append(line)
                    if len(lines) >= 2:
                        break

            await asyncio.wait_for(read_lines(), timeout=3)

            assert lines[0] == "event: endpoint"
            assert lines[1].startswith("data: /messages/?session_id=")
