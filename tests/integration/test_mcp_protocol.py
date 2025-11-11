"""End-to-end test of MCP server via stdio protocol."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestMCPProtocolEndToEnd:
    """Test actual MCP protocol communication via stdio."""

    @pytest.mark.asyncio
    async def test_server_via_mcp_client(self, tmp_path):
        """Test server using actual MCP client via stdio."""
        # Create test documentation
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("""---
title: Test Document
tags: [test, example]
---

# Test Document

This is a test document for MCP protocol testing.

## Content

Some content here.
""")

        # We'll use the mcp package's client to connect to our server
        # This simulates what Claude Code does
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[
                "-m",
                "hierarchical_docs_mcp",
            ],
            env={
                "DOCS_ROOT": str(docs_dir),
                "LOG_LEVEL": "DEBUG",
            },
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()

                # Test list_tools
                tools_result = await session.list_tools()
                assert len(tools_result.tools) > 0
                tool_names = [tool.name for tool in tools_result.tools]
                assert "get_table_of_contents" in tool_names
                assert "get_document" in tool_names

                # Test get_table_of_contents (this works according to the user)
                print("\n=== Testing get_table_of_contents ===")
                try:
                    toc_result = await session.call_tool("get_table_of_contents", {})
                    print(f"TOC result: {toc_result}")
                    assert toc_result.content is not None
                    print("✓ get_table_of_contents succeeded")
                except Exception as e:
                    print(f"✗ get_table_of_contents failed: {e}")
                    raise

                # Test get_document (this fails according to the user)
                print("\n=== Testing get_document ===")
                try:
                    doc_result = await session.call_tool(
                        "get_document", {"uri": "docs://test"}
                    )
                    print(f"Document result: {doc_result}")
                    assert doc_result.content is not None
                    print("✓ get_document succeeded")
                except Exception as e:
                    print(f"✗ get_document failed: {e}")
                    print(f"  Error type: {type(e).__name__}")
                    print(f"  Error details: {str(e)}")
                    # Check if this is the ModelService error
                    if "ModelService" in str(e) or "already exists" in str(e):
                        pytest.fail(
                            f"Reproduced ModelService error: {e}"
                        )
                    raise

    @pytest.mark.asyncio
    async def test_all_tools_via_protocol(self, tmp_path):
        """Test all tools through the MCP protocol."""
        # Create test documentation
        docs_dir = tmp_path / "docs"
        guides_dir = docs_dir / "guides"
        guides_dir.mkdir(parents=True)
        (guides_dir / "getting-started.md").write_text("""---
title: Getting Started
tags: [beginner, tutorial]
category: guides
---

# Getting Started

Welcome to our documentation!
""")

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "hierarchical_docs_mcp"],
            env={"DOCS_ROOT": str(docs_dir), "LOG_LEVEL": "ERROR"},
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Test each tool
                tools_to_test = [
                    ("get_table_of_contents", {}),
                    ("search_documentation", {"query": "getting", "limit": 5}),
                    ("navigate_to", {"uri": "docs://"}),
                    ("search_by_tags", {"tags": ["tutorial"], "limit": 5}),
                    ("get_document", {"uri": "docs://guides/getting-started"}),
                ]

                results = {}
                for tool_name, args in tools_to_test:
                    print(f"\nTesting {tool_name}...")
                    try:
                        result = await session.call_tool(tool_name, args)
                        results[tool_name] = {"success": True, "result": result}
                        print(f"  ✓ {tool_name} succeeded")
                    except Exception as e:
                        results[tool_name] = {"success": False, "error": str(e)}
                        print(f"  ✗ {tool_name} failed: {e}")

                # Report summary
                print("\n=== Test Summary ===")
                for tool_name, result in results.items():
                    status = "✓ PASS" if result["success"] else "✗ FAIL"
                    print(f"{status}: {tool_name}")
                    if not result["success"]:
                        print(f"    Error: {result['error']}")

                # Assert all tools succeeded
                failed_tools = [
                    name for name, result in results.items() if not result["success"]
                ]
                if failed_tools:
                    pytest.fail(
                        f"The following tools failed: {', '.join(failed_tools)}\n"
                        + "\n".join(
                            [
                                f"  {name}: {results[name]['error']}"
                                for name in failed_tools
                            ]
                        )
                    )


class TestMCPProtocolErrorHandling:
    """Test error handling in MCP protocol communication."""

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, tmp_path):
        """Test calling an invalid tool name."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "hierarchical_docs_mcp"],
            env={"DOCS_ROOT": str(docs_dir)},
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Try to call a non-existent tool
                with pytest.raises(Exception) as exc_info:
                    await session.call_tool("nonexistent_tool", {})

                # Should get an error about unknown tool
                assert "Unknown tool" in str(exc_info.value) or "not found" in str(
                    exc_info.value
                ).lower()

    @pytest.mark.asyncio
    async def test_missing_required_argument(self, tmp_path):
        """Test calling a tool without required arguments."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "hierarchical_docs_mcp"],
            env={"DOCS_ROOT": str(docs_dir)},
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Try search_documentation without query - should handle gracefully
                result = await session.call_tool("search_documentation", {})
                # Should return empty results or handle missing query gracefully
                assert result.content is not None
