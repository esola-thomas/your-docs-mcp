"""MCP tool handlers for documentation queries."""

import asyncio
import os
from pathlib import Path
from typing import Any

from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.core.services.hierarchy import (
    get_table_of_contents,
    navigate_to_uri,
)
from docs_mcp.core.services.search import search_by_metadata, search_content
from docs_mcp.core.utils.logger import logger


async def handle_search_documentation(
    arguments: dict[str, Any],
    documents: list[Document],
    categories: dict[str, Category],
    search_limit: int,
) -> list[dict[str, Any]]:
    """Handle search_documentation tool request."""
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
    """Handle navigate_to tool request."""
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
    """Handle get_table_of_contents tool request."""
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
    """Handle search_by_tags tool request."""
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
    """Handle get_document tool request."""
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
    """Handle get_all_tags tool request."""
    category = arguments.get("category")
    include_counts = arguments.get("include_counts", False)

    logger.info(f"Get all tags request: category={category}, include_counts={include_counts}")

    try:
        tag_frequency: dict[str, int] = {}

        for doc in documents:
            if category and doc.category != category:
                continue

            for tag in doc.tags:
                tag_frequency[tag] = tag_frequency.get(tag, 0) + 1

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
    """Handle generate_pdf_release tool request."""
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
        script_path = docs_root.parent / "scripts" / "generate-docs-pdf.sh"

        if not script_path.exists():
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
