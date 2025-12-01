"""MCP tool handlers for documentation queries."""

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
