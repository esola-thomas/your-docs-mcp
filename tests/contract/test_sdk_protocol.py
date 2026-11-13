"""Exercise registered SDK handlers with a real protocol client."""

import json
from unittest.mock import patch

import pytest
from mcp import Client, MCPError

from docs_mcp.core.config import ServerConfig
from docs_mcp.mcp.server import DocumentationMCPServer


@pytest.fixture
async def loaded_server(tmp_path):
    (tmp_path / "guides").mkdir()
    (tmp_path / "guides" / "hello.md").write_text("# Hello world\n\nWelcome to the guide.")
    server = DocumentationMCPServer(ServerConfig(docs_root=tmp_path))
    with patch("docs_mcp.mcp.server._get_vector_store", return_value=None):
        await server.initialize()
    return server


async def test_registered_tools_see_loaded_categories(loaded_server):
    async with Client(loaded_server.server) as client:
        listed = await client.list_tools()
        assert len(listed.tools) == 6
        search = next(t for t in listed.tools if t.name == "search_documentation")
        assert search.input_schema["required"] == ["query"]
        assert "inputSchema" in search.model_dump(by_alias=True)
        toc = await client.call_tool("get_table_of_contents", {})
        assert not toc.is_error
        assert "guides" in toc.content[0].text
        nav = await client.call_tool("navigate_to", {"uri": "docs://guides"})
        data = json.loads(nav.content[0].text)
        assert data["current_type"] == "category"
        assert data["children"]


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("search_documentation", {}),
        ("search_documentation", {"query": 42}),
        ("search_documentation", {"query": "hello", "limit": "ten"}),
        ("navigate_to", {}),
        ("unknown_tool", {}),
        ("generate_pdf_release", {}),
    ],
)
async def test_bad_calls_are_tool_errors(loaded_server, name, arguments):
    async with Client(loaded_server.server) as client:
        result = await client.call_tool(name, arguments)
        assert result.is_error
        assert result.content[0].text


async def test_resources_round_trip(loaded_server):
    async with Client(loaded_server.server) as client:
        listed = await client.list_resources()
        assert any(r.uri == "docs://guides/hello" for r in listed.resources)
        result = await client.read_resource("docs://guides/hello")
        assert result.contents[0].uri == "docs://guides/hello"
        assert "Hello world" in result.contents[0].text
        assert result.contents[0].mime_type == "text/markdown"
        with pytest.raises(MCPError):
            await client.read_resource("docs://missing")


async def test_pdf_advertised_only_when_enabled(tmp_path):
    server = DocumentationMCPServer(ServerConfig(docs_root=tmp_path, enable_pdf_generation=True))
    async with Client(server.server) as client:
        listed = await client.list_tools()
        assert len(listed.tools) == 7
        assert any(t.name == "generate_pdf_release" for t in listed.tools)


async def test_raised_tool_failure_is_error_result(loaded_server):
    with patch(
        "docs_mcp.mcp.handlers.tools.handle_get_all_tags", side_effect=RuntimeError("failure")
    ):
        async with Client(loaded_server.server) as client:
            result = await client.call_tool("get_all_tags", {})
            assert result.is_error
            assert "failure" in result.content[0].text


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("search_documentation", {"query": "Hello"}),
        ("search_by_tags", {"tags": []}),
        ("get_document", {"uri": "docs://guides/hello"}),
        ("get_all_tags", {}),
    ],
)
async def test_all_data_tools_return_json_text(loaded_server, name, arguments):
    with patch("docs_mcp.core.services.search._get_vector_store", return_value=None):
        async with Client(loaded_server.server) as client:
            result = await client.call_tool(name, arguments)
            assert not result.is_error
            assert isinstance(json.loads(result.content[0].text), (dict, list))


async def test_pdf_call_uses_adapter(tmp_path):
    from unittest.mock import AsyncMock

    server = DocumentationMCPServer(ServerConfig(docs_root=tmp_path, enable_pdf_generation=True))
    with patch(
        "docs_mcp.mcp.handlers.tools.handle_generate_pdf_release",
        new_callable=AsyncMock,
        return_value={"path": "release.pdf"},
    ) as generate:
        async with Client(server.server) as client:
            result = await client.call_tool("generate_pdf_release", {})
            assert not result.is_error
            assert json.loads(result.content[0].text) == {"path": "release.pdf"}
            generate.assert_awaited_once_with({}, tmp_path)
