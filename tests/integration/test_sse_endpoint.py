"""Integration test for the SSE transport endpoints."""

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
async def running_sse_server(tmp_path):
    """Start the documentation web server with SSE support on a free port."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()

    config = ServerConfig(docs_root=docs_root)
    from docs_mcp.core.services.hierarchy import build_category_tree
    from docs_mcp.core.services.markdown import scan_markdown_files

    (docs_root / "guides").mkdir()
    (docs_root / "guides" / "hello.md").write_text("# Hello world\n\nWelcome.")
    documents = scan_markdown_files(docs_root, docs_root)
    web_server = DocumentationWebServer(
        config=config, documents=documents, categories=build_category_tree(documents)
    )

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


@pytest.mark.asyncio
async def test_sse_protocol_round_trip_and_reconnect(running_sse_server: str):
    """Test initialization and request dispatch, including a fresh second session."""
    import json

    import anyio
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client

    with anyio.fail_after(15):
        for _ in range(2):
            async with sse_client(f"{running_sse_server}/sse") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    # Session clients use the same wire path as external SSE hosts.
                    assert len((await session.list_tools()).tools) == 6
                    result = await session.call_tool("get_table_of_contents", {})
                    assert not result.is_error
                    assert isinstance(json.loads(result.content[0].text), dict)
                    assert any(
                        r.uri == "docs://guides/hello"
                        for r in (await session.list_resources()).resources
                    )
                    resource = await session.read_resource("docs://guides/hello")
                    assert "Welcome" in resource.contents[0].text
                    assert "guides" in result.content[0].text
                    invalid = await session.call_tool("search_documentation", {"query": 42})
                    assert invalid.is_error
