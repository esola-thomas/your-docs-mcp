"""Hierarchical navigation and category tree building."""

from typing import Any, cast

from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category, NavigationContext
from docs_mcp.services.cache import get_cache
from docs_mcp.utils.logger import logger


class HierarchyError(Exception):
    """Raised when hierarchy operations fail."""

    pass


def build_category_tree(
    documents: list[Document],
    source_category: str = "docs",
) -> dict[str, Category]:
    """Build category tree from list of documents.

    Args:
        documents: List of parsed documents
        source_category: Source category identifier

    Returns:
        Dictionary mapping URIs to Category objects
    """
    categories: dict[str, Category] = {}

    # Create categories from document paths
    for doc in documents:
        # Get all ancestor paths
        parts = list(doc.relative_path.parts[:-1])  # Exclude filename

        for depth in range(len(parts)):
            # Build category URI for this level
            category_parts = parts[: depth + 1]
            category_uri = "docs://" + "/".join(category_parts)

            if category_uri not in categories:
                # Determine parent URI
                parent_uri = None
                if depth > 0:
                    parent_parts = category_parts[:-1]
                    parent_uri = "docs://" + "/".join(parent_parts)

                # Create category
                category = Category(
                    name=category_parts[-1],
                    label=category_parts[-1].replace("-", " ").replace("_", " ").title(),
                    uri=category_uri,
                    parent_uri=parent_uri,
                    depth=depth,
                    source_category=source_category,
                )
                categories[category_uri] = category

        # Add document to its parent category
        if len(parts) > 0:
            parent_uri = "docs://" + "/".join(parts)
            if parent_uri in categories:
                categories[parent_uri].child_documents.append(doc.uri)

    # Build parent-child relationships for categories
    for uri, category in categories.items():
        if category.parent_uri and category.parent_uri in categories:
            parent = categories[category.parent_uri]
            if uri not in parent.child_categories:
                parent.child_categories.append(uri)

    # Calculate document counts (including descendants)
    for category in categories.values():
        category.document_count = _count_documents_recursive(category, categories)

    logger.info(f"Built category tree with {len(categories)} categories")
    return categories


def _count_documents_recursive(
    category: Category,
    categories: dict[str, Category],
) -> int:
    """Count documents in category and all descendants.

    Args:
        category: Category to count
        categories: All categories

    Returns:
        Total document count
    """
    count = len(category.child_documents)

    for child_uri in category.child_categories:
        if child_uri in categories:
            count += _count_documents_recursive(categories[child_uri], categories)

    return count


def get_breadcrumbs(uri: str) -> list[dict[str, str]]:
    """Generate breadcrumb navigation for a URI.

    Args:
        uri: Resource URI (e.g., "docs://guides/security/authentication")

    Returns:
        List of breadcrumb items with name and URI
    """
    if not uri.startswith("docs://") and not uri.startswith("api://"):
        return []

    scheme = uri.split("://")[0]
    path = uri.replace(f"{scheme}://", "")

    if not path:
        return []

    parts = path.split("/")
    breadcrumbs = []

    for i, part in enumerate(parts):
        crumb_uri = f"{scheme}://" + "/".join(parts[: i + 1])
        breadcrumbs.append(
            {
                "name": part.replace("-", " ").replace("_", " ").title(),
                "uri": crumb_uri,
            }
        )

    return breadcrumbs


def navigate_to_uri(
    uri: str,
    documents: list[Document],
    categories: dict[str, Category],
) -> NavigationContext:
    """Navigate to a URI and get context.

    Args:
        uri: Target URI
        documents: All documents
        categories: All categories

    Returns:
        NavigationContext with current position and options

    Raises:
        HierarchyError: If URI is invalid or not found
    """
    # Check if it's root
    if uri in ("docs://", "docs", ""):
        return _get_root_context(categories)

    # Check if it's a category
    if uri in categories:
        return _get_category_context(uri, categories)

    # Check if it's a document
    doc = next((d for d in documents if d.uri == uri), None)
    if doc:
        return _get_document_context(doc, categories)

    raise HierarchyError(f"URI not found: {uri}")


def _get_root_context(categories: dict[str, Category]) -> NavigationContext:
    """Get navigation context for root.

    Args:
        categories: All categories

    Returns:
        NavigationContext for root
    """
    # Find root categories (depth == 0)
    root_categories = [
        {
            "type": "category",
            "uri": cat.uri,
            "name": cat.label,
            "document_count": cat.document_count,
        }
        for cat in categories.values()
        if cat.depth == 0
    ]

    return NavigationContext(
        current_uri="docs://",
        current_type="root",
        parent_uri=None,
        breadcrumbs=[],
        children=root_categories,
        sibling_count=len(root_categories),
        navigation_options={
            "down": "Navigate to a category by URI",
        },
    )


def _get_category_context(
    uri: str,
    categories: dict[str, Category],
) -> NavigationContext:
    """Get navigation context for a category.

    Args:
        uri: Category URI
        categories: All categories

    Returns:
        NavigationContext for category
    """
    category = categories[uri]

    # Build children list
    children = []

    # Add child categories
    for child_uri in category.child_categories:
        if child_uri in categories:
            child_cat = categories[child_uri]
            children.append(
                {
                    "type": "category",
                    "uri": child_cat.uri,
                    "name": child_cat.label,
                    "document_count": child_cat.document_count,
                }
            )

    # Add child documents (without loading full content)
    for doc_uri in category.child_documents:
        # Extract name from URI
        name = doc_uri.split("/")[-1].replace("-", " ").replace("_", " ").title()
        children.append(
            {
                "type": "document",
                "uri": doc_uri,
                "name": name,
            }
        )

    # Determine parent URI
    parent_uri = category.parent_uri or "docs://"

    # Navigation options
    options = {}
    # Always provide "up" option since we can go to parent or root
    options["up"] = f"Navigate to parent: {parent_uri}"
    if children:
        options["down"] = "Navigate to a child item"

    return NavigationContext(
        current_uri=uri,
        current_type="category",
        parent_uri=parent_uri,
        breadcrumbs=category.breadcrumbs,
        children=children,
        sibling_count=len([c for c in categories.values() if c.parent_uri == category.parent_uri]),
        navigation_options=options,
    )


def _get_document_context(
    doc: Document,
    categories: dict[str, Category],
) -> NavigationContext:
    """Get navigation context for a document.

    Args:
        doc: Document
        categories: All categories

    Returns:
        NavigationContext for document
    """
    # Find parent category
    parent_uri = None
    breadcrumbs = []

    if len(doc.breadcrumbs) > 0:
        parent_parts = doc.breadcrumbs
        parent_uri = "docs://" + "/".join(parent_parts)
        breadcrumbs = get_breadcrumbs(doc.uri)
    else:
        parent_uri = "docs://"

    return NavigationContext(
        current_uri=doc.uri,
        current_type="document",
        parent_uri=parent_uri,
        breadcrumbs=breadcrumbs,
        children=[],  # Documents have no children
        sibling_count=0,  # TODO: Calculate siblings
        navigation_options={
            "up": f"Navigate to parent: {parent_uri}",
        },
    )


def get_table_of_contents(
    categories: dict[str, Category],
    documents: list[Document],
    max_depth: int | None = None,
) -> dict[str, Any]:
    """Generate a table of contents tree.

    Args:
        categories: All categories
        documents: All documents
        max_depth: Maximum depth to include (None for all)

    Returns:
        Nested dictionary representing the TOC
    """
    # Cache key
    cache = get_cache()
    cache_key = f"toc:{max_depth}"
    cached = cache.get(cache_key)
    if cached:
        return cast(dict[str, Any], cached)

    # Build TOC from root
    root_categories = [c for c in categories.values() if c.depth == 0]

    children: list[Any] = []
    for root_cat in root_categories:
        if max_depth is None or root_cat.depth < max_depth:
            children.append(_build_toc_node(root_cat, categories, documents, max_depth))

    toc: dict[str, Any] = {
        "type": "root",
        "uri": "docs://",
        "children": children,
    }

    # Cache the result
    cache.set(cache_key, toc, ttl=3600)

    return toc


def _build_toc_node(
    category: Category,
    categories: dict[str, Category],
    documents: list[Document],
    max_depth: int | None,
) -> dict[str, Any]:
    """Build a TOC node for a category.

    Args:
        category: Category to build node for
        categories: All categories
        documents: All documents
        max_depth: Maximum depth

    Returns:
        TOC node dictionary
    """
    children: list[Any] = []

    # Add child categories only if within max_depth
    if max_depth is None or category.depth + 1 < max_depth:
        for child_uri in category.child_categories:
            if child_uri in categories:
                child_cat = categories[child_uri]
                children.append(_build_toc_node(child_cat, categories, documents, max_depth))

    # Add child documents only if within max_depth
    if max_depth is None or category.depth + 1 < max_depth:
        for doc_uri in category.child_documents:
            doc = next((d for d in documents if d.uri == doc_uri), None)
            if doc:
                children.append(
                    {
                        "type": "document",
                        "uri": doc.uri,
                        "name": doc.title,
                        "tags": doc.tags,
                    }
                )

    node: dict[str, Any] = {
        "type": "category",
        "uri": category.uri,
        "name": category.label,
        "document_count": category.document_count,
        "children": children,
    }

    return node
