"""MCP tool handlers for documentation queries."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.types import Tool

from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category
from docs_mcp.services.hierarchy import (
    get_table_of_contents,
    navigate_to_uri,
)
from docs_mcp.services.search import search_by_metadata, search_content
from docs_mcp.utils.logger import logger


def get_tool_definitions() -> list[Tool]:
    """Return the canonical list of MCP tool definitions.

    This is the single source of truth for tool schemas.  Both the stdio
    MCP server and the web/SSE server import this function so that tool
    names, descriptions, and input schemas are never duplicated.

    Returns:
        List of Tool objects describing every available tool.
    """
    return [
        Tool(
            name="search_documentation",
            description=(
                "Search documentation with full-text search. "
                "Returns results with hierarchical context (breadcrumbs)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category to filter results",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="navigate_to",
            description=(
                "Navigate to a specific URI in the documentation hierarchy. "
                "Returns navigation context with parent, children, and breadcrumbs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "URI to navigate to (e.g., 'docs://guides/security')",
                    },
                },
                "required": ["uri"],
            },
        ),
        Tool(
            name="get_table_of_contents",
            description=(
                "Get the complete documentation hierarchy as a table of contents tree."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to include (optional)",
                    },
                },
            },
        ),
        Tool(
            name="search_by_tags",
            description="Search documentation by metadata tags and category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to search for (OR logic)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category to filter by",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 10,
                    },
                },
                "required": ["tags"],
            },
        ),
        Tool(
            name="get_document",
            description="Get full content and metadata for a specific document by URI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "Document URI (e.g., 'docs://guides/getting-started')",
                    },
                },
                "required": ["uri"],
            },
        ),
        Tool(
            name="get_all_tags",
            description=(
                "Get a list of all unique tags defined across the documentation. "
                "Optionally filter by category and include document counts per tag."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category to filter tags from",
                    },
                    "include_counts": {
                        "type": "boolean",
                        "description": "Include document count for each tag (default: false)",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="generate_pdf_release",
            description=(
                "Generate a PDF documentation release. Creates a formatted PDF "
                "with all documentation, table of contents, and optional "
                "confidentiality markings (watermark, headers, footers)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Document title. Defaults to project name.",
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "Document subtitle (optional).",
                    },
                    "author": {
                        "type": "string",
                        "description": "Document author. Defaults to 'Documentation Team'.",
                    },
                    "version": {
                        "type": "string",
                        "description": "Version string for the release (e.g., '2.0.0'). Defaults to current date.",
                    },
                    "confidential": {
                        "type": "boolean",
                        "description": "Add confidentiality markings (watermark, headers, footers). Default: false",
                        "default": False,
                    },
                    "owner": {
                        "type": "string",
                        "description": "Copyright owner (shown when confidential=true). Defaults to project name.",
                    },
                },
            },
        ),
    ]


async def dispatch_tool_call(
    name: str,
    arguments: dict[str, Any],
    documents: list[Document],
    categories: dict[str, Category],
    search_limit: int,
    docs_root: Path,
) -> list[Any]:
    """Dispatch a tool call by name and return the MCP response payload.

    This is the single source of truth for tool call routing.  Both the
    stdio MCP server and the web/SSE server delegate to this function so
    that handler dispatch is never duplicated.

    Args:
        name: Tool name as received from the MCP client.
        arguments: Tool arguments dict from the MCP client.
        documents: All loaded documents.
        categories: Category tree built from the documents.
        search_limit: Default maximum number of search results.
        docs_root: Root directory of the documentation (used by PDF tool).

    Returns:
        A list of content items (``{"type": "text", "text": ...}`` dicts)
        ready to be returned directly by an MCP ``call_tool`` handler.

    Raises:
        ValueError: When *name* does not match any known tool.
    """
    if name == "search_documentation":
        results = await handle_search_documentation(
            arguments, documents, categories, search_limit
        )
        return [{"type": "text", "text": json.dumps(results, indent=2)}]

    elif name == "navigate_to":
        result = await handle_navigate_to(arguments, documents, categories)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "get_table_of_contents":
        result = await handle_get_table_of_contents(arguments, documents, categories)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "search_by_tags":
        results = await handle_search_by_tags(arguments, documents, search_limit)
        return [{"type": "text", "text": json.dumps(results, indent=2)}]

    elif name == "get_document":
        result = await handle_get_document(arguments, documents)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "get_all_tags":
        result = await handle_get_all_tags(arguments, documents)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "generate_pdf_release":
        result = await handle_generate_pdf_release(arguments, docs_root)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_search_documentation(
    arguments: dict[str, Any],
    documents: list[Document],
    categories: dict[str, Category],
    search_limit: int,
) -> list[dict[str, Any]]:
    """Handle search_documentation tool request.

    Args:
        arguments: Tool arguments containing 'query' and optional 'category'
        documents: All documents
        categories: Category tree
        search_limit: Maximum results to return

    Returns:
        List of search results
    """
    query = arguments.get("query", "")
    category = arguments.get("category")
    limit = arguments.get("limit", search_limit)

    logger.info(f"Search request: query='{query}', category={category}, limit={limit}")

    try:
        results = search_content(
            query=query,
            documents=documents,
            categories=categories,
            limit=limit,
            category_filter=category,
        )

        return [
            {
                "uri": result.document_uri,
                "title": result.title,
                "excerpt": result.highlighted_excerpt or result.excerpt,
                "breadcrumbs": result.breadcrumb_string,
                "category": result.category,
                "relevance": result.relevance_score,
                "match_type": result.match_type,
            }
            for result in results
        ]

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return [{"error": str(e)}]


async def handle_navigate_to(
    arguments: dict[str, Any],
    documents: list[Document],
    categories: dict[str, Category],
) -> dict[str, Any]:
    """Handle navigate_to tool request.

    Args:
        arguments: Tool arguments containing 'uri'
        documents: All documents
        categories: Category tree

    Returns:
        Navigation context
    """
    uri = arguments.get("uri", "")

    logger.info(f"Navigate request: uri='{uri}'")

    try:
        context = navigate_to_uri(uri, documents, categories)

        return {
            "current_uri": context.current_uri,
            "current_type": context.current_type,
            "parent_uri": context.parent_uri,
            "breadcrumbs": context.breadcrumbs,
            "children": context.children,
            "sibling_count": context.sibling_count,
            "navigation_options": context.navigation_options,
        }

    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        return {"error": str(e)}


async def handle_get_table_of_contents(
    arguments: dict[str, Any],
    documents: list[Document],
    categories: dict[str, Category],
) -> dict[str, Any]:
    """Handle get_table_of_contents tool request.

    Args:
        arguments: Tool arguments containing optional 'max_depth'
        documents: All documents
        categories: Category tree

    Returns:
        Table of contents tree
    """
    max_depth = arguments.get("max_depth")

    logger.info(f"Table of contents request: max_depth={max_depth}")

    try:
        toc = get_table_of_contents(categories, documents, max_depth)
        return toc

    except Exception as e:
        logger.error(f"TOC generation failed: {e}")
        return {"error": str(e)}


async def handle_search_by_tags(
    arguments: dict[str, Any],
    documents: list[Document],
    search_limit: int,
) -> list[dict[str, Any]]:
    """Handle search_by_tags tool request.

    Args:
        arguments: Tool arguments containing 'tags' list
        documents: All documents
        search_limit: Maximum results

    Returns:
        List of matching documents
    """
    tags = arguments.get("tags", [])
    category = arguments.get("category")
    limit = arguments.get("limit", search_limit)

    logger.info(f"Tag search request: tags={tags}, category={category}, limit={limit}")

    try:
        results = search_by_metadata(
            tags=tags,
            category=category,
            documents=documents,
            limit=limit,
        )

        return [
            {
                "uri": result.document_uri,
                "title": result.title,
                "excerpt": result.excerpt,
                "breadcrumbs": result.breadcrumb_string,
                "category": result.category,
                "tags": [doc.tags for doc in documents if doc.uri == result.document_uri][0],
            }
            for result in results
        ]

    except Exception as e:
        logger.error(f"Tag search failed: {e}")
        return [{"error": str(e)}]


async def handle_get_document(
    arguments: dict[str, Any],
    documents: list[Document],
) -> dict[str, Any]:
    """Handle get_document tool request.

    Args:
        arguments: Tool arguments containing 'uri'
        documents: All documents

    Returns:
        Document details
    """
    uri = arguments.get("uri", "")

    logger.info(f"Get document request: uri='{uri}'")

    try:
        doc = next((d for d in documents if d.uri == uri), None)

        if not doc:
            return {"error": f"Document not found: {uri}"}

        return {
            "uri": doc.uri,
            "title": doc.title,
            "content": doc.content,
            "tags": doc.tags,
            "category": doc.category,
            "last_modified": doc.last_modified.isoformat(),
            "breadcrumbs": [crumb for crumb in doc.breadcrumbs],
        }

    except Exception as e:
        logger.error(f"Get document failed: {e}")
        return {"error": str(e)}


async def handle_get_all_tags(
    arguments: dict[str, Any],
    documents: list[Document],
) -> dict[str, Any]:
    """Handle get_all_tags tool request.

    Collects all unique tags from documents with optional frequency counts.

    Args:
        arguments: Tool arguments containing optional 'category' filter
                   and 'include_counts' boolean
        documents: All documents

    Returns:
        Dictionary with 'tags' list, 'count' total, and optionally
        'tag_counts' with frequency information
    """
    category = arguments.get("category")
    include_counts = arguments.get("include_counts", False)

    logger.info(f"Get all tags request: category={category}, include_counts={include_counts}")

    try:
        tag_frequency: dict[str, int] = {}

        for doc in documents:
            # Apply category filter if specified
            if category and doc.category != category:
                continue

            for tag in doc.tags:
                tag_frequency[tag] = tag_frequency.get(tag, 0) + 1

        # Sort tags alphabetically
        sorted_tags = sorted(tag_frequency.keys())

        result: dict[str, Any] = {
            "tags": sorted_tags,
            "count": len(sorted_tags),
        }

        if include_counts:
            result["tag_counts"] = [
                {"tag": tag, "document_count": tag_frequency[tag]} for tag in sorted_tags
            ]

        return result

    except Exception as e:
        logger.error(f"Get all tags failed: {e}")
        return {"error": str(e)}


async def handle_generate_pdf_release(
    arguments: dict[str, Any],
    docs_root: Path,
) -> dict[str, Any]:
    """Handle generate_pdf_release tool request.

    Generates a PDF documentation release using the generate-docs-pdf.sh script.

    Args:
        arguments: Tool arguments containing optional metadata and confidential flag
        docs_root: Root directory of the documentation

    Returns:
        Dictionary with 'success' status, 'output_file', and 'manifest_file' paths
    """
    title = arguments.get("title")
    subtitle = arguments.get("subtitle")
    author = arguments.get("author")
    version = arguments.get("version")
    confidential = arguments.get("confidential", False)
    owner = arguments.get("owner")

    logger.info(
        f"Generate PDF release: version={version}, confidential={confidential}, title={title}"
    )

    try:
        # Find the generate-docs-pdf.sh script
        script_path = docs_root.parent / "scripts" / "generate-docs-pdf.sh"

        if not script_path.exists():
            # Try alternative locations
            for alt_path in [
                Path(__file__).parent.parent.parent / "scripts" / "generate-docs-pdf.sh",
                Path.cwd() / "scripts" / "generate-docs-pdf.sh",
            ]:
                if alt_path.exists():
                    script_path = alt_path
                    break

        if not script_path.exists():
            return {
                "success": False,
                "error": f"PDF generation script not found. Expected at: {script_path}",
            }

        # Build command
        cmd = [str(script_path)]
        if version:
            cmd.append(version)
        if confidential:
            cmd.append("--confidential")
        if title:
            cmd.extend(["--title", title])
        if subtitle:
            cmd.extend(["--subtitle", subtitle])
        if author:
            cmd.extend(["--author", author])
        if owner:
            cmd.extend(["--owner", owner])

        # Run the script asynchronously with DOCS_ROOT set
        env = os.environ.copy()
        env["DOCS_ROOT"] = str(docs_root)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(docs_root.parent) if docs_root.parent.exists() else str(Path.cwd()),
            env=env,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            return {
                "success": False,
                "error": f"PDF generation failed: {error_msg}",
                "stdout": stdout.decode() if stdout else "",
            }

        # Parse output to find generated files
        output_text = stdout.decode()
        output_file = None
        manifest_file = None

        for line in output_text.split("\n"):
            if line.startswith("Output:"):
                output_file = line.replace("Output:", "").strip()
            elif line.startswith("Manifest:"):
                manifest_file = line.replace("Manifest:", "").strip()

        return {
            "success": True,
            "output_file": output_file,
            "manifest_file": manifest_file,
            "version": version or "auto",
            "confidential": confidential,
            "message": "PDF documentation release generated successfully",
        }

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return {"success": False, "error": str(e)}
