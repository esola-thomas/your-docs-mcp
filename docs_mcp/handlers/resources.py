"""MCP resource handlers for URI-based documentation access."""

from typing import Any

from docs_mcp.models.document import Document
from docs_mcp.models.navigation import Category
from docs_mcp.utils.logger import logger


async def handle_resource_read(
    uri: str,
    documents: list[Document],
    categories: dict[str, Category],
) -> dict[str, Any]:
    """Handle resource read request for a docs:// URI.

    Args:
        uri: Resource URI
        documents: All documents
        categories: Category tree

    Returns:
        Resource content
    """
    logger.info(f"Resource read request: {uri}")

    try:
        # Check if it's a document
        doc = next((d for d in documents if d.uri == uri), None)
        if doc:
            return {
                "uri": doc.uri,
                "mimeType": "text/markdown",
                "text": doc.content,
                "metadata": {
                    "title": doc.title,
                    "tags": doc.tags,
                    "category": doc.category,
                    "last_modified": doc.last_modified.isoformat(),
                },
            }

        # Check if it's a category
        if uri in categories:
            category = categories[uri]
            # Return category overview
            content = f"# {category.label}\n\n"
            content += f"**Documents**: {category.document_count}\n\n"

            if category.child_categories:
                content += "## Subcategories\n\n"
                for child_uri in category.child_categories:
                    if child_uri in categories:
                        child = categories[child_uri]
                        content += f"- [{child.label}]({child.uri})\n"

            if category.child_documents:
                content += "\n## Documents\n\n"
                for doc_uri in category.child_documents:
                    doc = next((d for d in documents if d.uri == doc_uri), None)
                    if doc:
                        content += f"- [{doc.title}]({doc.uri})\n"

            return {
                "uri": uri,
                "mimeType": "text/markdown",
                "text": content,
                "metadata": {
                    "type": "category",
                    "name": category.label,
                    "document_count": category.document_count,
                },
            }

        return {"error": f"Resource not found: {uri}"}

    except Exception as e:
        logger.error(f"Resource read failed: {e}")
        return {"error": str(e)}


async def list_resources(
    documents: list[Document],
    categories: dict[str, Category],
) -> list[dict[str, Any]]:
    """List all available resources.

    Args:
        documents: All documents
        categories: Category tree

    Returns:
        List of resource descriptions
    """
    resources = []

    # Add root
    resources.append(
        {
            "uri": "docs://",
            "name": "Documentation Root",
            "mimeType": "text/markdown",
            "description": "Root of documentation hierarchy",
        }
    )

    # Add categories
    for category in categories.values():
        resources.append(
            {
                "uri": category.uri,
                "name": category.label,
                "mimeType": "text/markdown",
                "description": f"Category with {category.document_count} documents",
            }
        )

    # Add documents
    for doc in documents:
        resources.append(
            {
                "uri": doc.uri,
                "name": doc.title,
                "mimeType": "text/markdown",
                "description": doc.excerpt(100),
            }
        )

    logger.info(f"Listed {len(resources)} resources")
    return resources
