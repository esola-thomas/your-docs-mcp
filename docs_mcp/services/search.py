"""Search functionality for documentation."""

import re
from typing import Literal, cast

from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category, SearchResult
from docs_mcp.security.sanitizer import sanitize_query
from docs_mcp.services.cache import get_cache
from docs_mcp.services.hierarchy import get_breadcrumbs
from docs_mcp.utils.logger import logger


class SearchError(Exception):
    """Raised when search operations fail."""

    pass


def search_content(
    query: str,
    documents: list[Document],
    categories: dict[str, Category],
    limit: int = 10,
    category_filter: str | None = None,
) -> list[SearchResult]:
    """Search documentation content with full-text search.

    Args:
        query: Search query string
        documents: List of documents to search
        categories: Category tree for context
        limit: Maximum number of results
        category_filter: Optional category to filter results

    Returns:
        List of SearchResult objects, sorted by relevance

    Raises:
        SearchError: If search fails
    """
    try:
        # Sanitize query
        sanitized_query = sanitize_query(query, allow_regex=False)

        if not sanitized_query:
            return []

        logger.debug(f"Searching for: {sanitized_query}")

        # Check cache
        cache = get_cache()
        cache_key = f"search:{sanitized_query}:{category_filter}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cast(list[SearchResult], cached)

        results = []

        # Compile regex for case-insensitive search
        try:
            pattern = re.compile(sanitized_query, re.IGNORECASE)
        except re.error as e:
            raise SearchError(f"Invalid search pattern: {e}") from e

        # Search through documents
        for doc in documents:
            # Apply category filter if specified
            if category_filter:
                if not doc.uri.startswith(f"docs://{category_filter}"):
                    continue

            # Calculate relevance scores
            title_score = 0.0
            content_score = 0.0
            metadata_score = 0.0

            # Search in title (highest weight)
            if pattern.search(doc.title):
                title_score = 1.0

            # Search in content
            content_matches = pattern.findall(doc.content)
            if content_matches:
                content_score = min(len(content_matches) / 10.0, 1.0)

            # Search in tags and category (metadata)
            metadata_text = " ".join(doc.tags) + " " + (doc.category or "")
            if pattern.search(metadata_text):
                metadata_score = 0.5

            # Calculate total relevance
            relevance = title_score * 0.5 + content_score * 0.3 + metadata_score * 0.2

            if relevance > 0:
                # Determine match type
                if title_score > 0:
                    match_type: Literal["full_text", "metadata", "title"] = "title"
                elif metadata_score > 0:
                    match_type = "metadata"
                else:
                    match_type = "full_text"

                # Extract excerpt with context
                excerpt = _extract_excerpt(doc.content, sanitized_query)
                highlighted = _highlight_matches(excerpt, sanitized_query)

                # Get breadcrumbs
                breadcrumbs = [crumb["name"] for crumb in get_breadcrumbs(doc.uri)]

                # Determine category
                category = breadcrumbs[0] if breadcrumbs else "docs"

                result = SearchResult(
                    document_uri=doc.uri,
                    title=doc.title,
                    excerpt=excerpt,
                    breadcrumbs=breadcrumbs,
                    category=category,
                    relevance_score=relevance,
                    match_type=match_type,
                    highlighted_excerpt=highlighted,
                )
                results.append(result)

        # Sort by relevance (highest first)
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Limit results
        results = results[:limit]

        logger.info(f"Search found {len(results)} results for: {sanitized_query}")

        # Cache results
        cache.set(cache_key, results, ttl=1800)  # 30 minutes

        return results

    except SearchError:
        raise
    except Exception as e:
        raise SearchError(f"Search failed: {e}") from e


def search_by_metadata(
    tags: list[str] | None = None,
    category: str | None = None,
    documents: list[Document] | None = None,
    limit: int = 10,
) -> list[SearchResult]:
    """Search documentation by metadata (tags, category).

    Args:
        tags: Tags to filter by (OR logic)
        category: Category to filter by
        documents: List of documents to search
        limit: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    results: list[SearchResult] = []

    if documents is None:
        return results

    for doc in documents:
        # Use AND logic: document must match ALL specified filters
        tag_match = not tags or any(tag in doc.tags for tag in tags)
        cat_match = not category or (doc.category == category or category in doc.uri)

        matches = tag_match and cat_match

        if matches:
            breadcrumbs = [crumb["name"] for crumb in get_breadcrumbs(doc.uri)]
            cat = breadcrumbs[0] if breadcrumbs else "docs"

            result = SearchResult(
                document_uri=doc.uri,
                title=doc.title,
                excerpt=doc.excerpt(200),
                breadcrumbs=breadcrumbs,
                category=cat,
                relevance_score=1.0,  # All metadata matches are equally relevant
                match_type="metadata",
                highlighted_excerpt="",
            )
            results.append(result)

    # Limit results
    results = results[:limit]

    logger.info(
        f"Metadata search found {len(results)} results (tags: {tags}, category: {category})"
    )

    return results


def _extract_excerpt(content: str, query: str, context_chars: int = 100) -> str:
    """Extract an excerpt showing the query match with context.

    Args:
        content: Document content
        query: Search query
        context_chars: Characters of context before/after match

    Returns:
        Excerpt string
    """
    try:
        # Find first match
        pattern = re.compile(query, re.IGNORECASE)
        match = pattern.search(content)

        if not match:
            # Return first N characters if no match
            return content[: context_chars * 2] + "..."

        # Extract context around match
        start = max(0, match.start() - context_chars)
        end = min(len(content), match.end() + context_chars)

        excerpt = content[start:end]

        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt.strip()

    except Exception as e:
        logger.warning(f"Failed to extract excerpt: {e}")
        return content[: context_chars * 2] + "..."


def _highlight_matches(text: str, query: str, highlight: str = "**") -> str:
    """Highlight query matches in text.

    Args:
        text: Text to highlight
        query: Query to highlight
        highlight: Marker to use for highlighting (e.g., "**" for bold)

    Returns:
        Text with matches highlighted
    """
    try:
        pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
        return pattern.sub(f"{highlight}\\1{highlight}", text)
    except Exception as e:
        logger.warning(f"Failed to highlight matches: {e}")
        return text
