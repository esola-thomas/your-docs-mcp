"""Verify the real CLI process speaks MCP over stdio."""

import json
import os
import sys

import anyio
import pytest
from mcp import Client, StdioServerParameters


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_stdio_cli_round_trip(tmp_path, mode):
    (tmp_path / "guides").mkdir()
    (tmp_path / "guides" / "hello.md").write_text("# Hello world\n\nWelcome.")
    params = StdioServerParameters(
        command=sys.executable,
        args=["-c", "from docs_mcp.__main__ import mcp_main; mcp_main()"],
        env={**os.environ, "DOCS_ROOT": str(tmp_path)},
    )
    with anyio.fail_after(15):
        async with Client(params, mode=mode) as client:
            assert len((await client.list_tools()).tools) == 6
            toc = await client.call_tool("get_table_of_contents", {})
            assert "guides" in toc.content[0].text
            result = await client.call_tool("get_document", {"uri": "docs://guides/hello"})
            assert json.loads(result.content[0].text)["title"] == "Hello world"
            resource = await client.read_resource("docs://guides/hello")
            assert "Welcome" in resource.contents[0].text
