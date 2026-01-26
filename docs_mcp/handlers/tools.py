"""MCP tool handlers for documentation queries."""

import asyncio
import os
from pathlib import Path
from typing import Any

from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category
from docs_mcp.services.hierarchy import (
    get_table_of_contents,
    navigate_to_uri,
)
from docs_mcp.services.search import search_by_metadata, search_content
from docs_mcp.utils.logger import logger


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
