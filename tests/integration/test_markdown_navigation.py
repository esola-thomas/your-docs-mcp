"""Integration tests for end-to-end markdown navigation workflow."""

import pytest

from hierarchical_docs_mcp.handlers.resources import handle_resource_read, list_resources
from hierarchical_docs_mcp.handlers.tools import (
    handle_get_table_of_contents,
    handle_navigate_to,
    handle_search_documentation,
)
from hierarchical_docs_mcp.services.hierarchy import (
    build_category_tree,
    get_breadcrumbs,
    get_table_of_contents,
    navigate_to_uri,
)
from hierarchical_docs_mcp.services.markdown import (
    scan_markdown_files,
)
from hierarchical_docs_mcp.services.search import search_by_metadata, search_content


@pytest.fixture
def test_docs_structure(tmp_path):
    """Create a realistic test documentation structure."""
    doc_root = tmp_path / "docs"
    doc_root.mkdir()

    # Create guides section
    guides = doc_root / "guides"
    guides.mkdir()

    (guides / "getting-started.md").write_text(r"""---
title: Getting Started
tags: [beginner, tutorial]
category: guides
order: 1
---

# Getting Started

Welcome to our documentation! This guide will help you get started quickly.

## Installation

First, install the package:

\`\`\`bash
pip install our-package
\`\`\`

## Quick Start

Here's a simple example:

\`\`\`python
from our_package import hello
hello()
\`\`\`
""")

    (guides / "configuration.md").write_text("""---
title: Configuration Guide
tags: [configuration, setup]
category: guides
order: 2
---

# Configuration

Learn how to configure the application.

## Basic Configuration

Set environment variables:
- `API_KEY`: Your API key
- `DEBUG`: Enable debug mode
""")

    # Create advanced guides
    advanced = guides / "advanced"
    advanced.mkdir()

    (advanced / "performance.md").write_text("""---
title: Performance Optimization
tags: [advanced, performance]
category: guides
order: 3
---

# Performance Optimization

Advanced tips for optimizing performance.

## Caching

Use caching to improve response times.

## Database Optimization

Index your queries properly.
""")

    # Create API reference section
    api = doc_root / "api"
    api.mkdir()

    (api / "authentication.md").write_text(r"""---
title: Authentication API
tags: [api, security, authentication]
category: api
order: 1
---

# Authentication API

API endpoints for user authentication.

## POST /auth/login

Authenticate a user and get a token.

**Parameters:**
- `username` (string): User's username
- `password` (string): User's password

**Response:**
\`\`\`json
{
  "token": "jwt-token-here",
  "expires": "2024-12-31T23:59:59Z"
}
\`\`\`
""")

    (api / "users.md").write_text("""---
title: Users API
tags: [api, users]
category: api
order: 2
---

# Users API

Manage user accounts.

## GET /users

List all users.

## POST /users

Create a new user.
""")

    return doc_root


@pytest.fixture
def loaded_documentation(test_docs_structure):
    """Load and process all documentation."""
    documents = scan_markdown_files(test_docs_structure, test_docs_structure)
    categories = build_category_tree(documents)
    return {
        "documents": documents,
        "categories": categories,
        "root": test_docs_structure,
    }


class TestEndToEndNavigation:
    """Test complete navigation workflows."""

    def test_load_and_parse_all_documents(self, test_docs_structure):
        """Test loading and parsing all documents in structure."""
        documents = scan_markdown_files(test_docs_structure, test_docs_structure)

        # Should have parsed all 5 documents
        assert len(documents) >= 5

        # Check that all have URIs
        for doc in documents:
            assert doc.uri.startswith("docs://")
            assert len(doc.title) > 0

    def test_build_complete_hierarchy(self, loaded_documentation):
        """Test building complete category hierarchy."""
        categories = loaded_documentation["categories"]

        # Should have guides, guides/advanced, and api categories
        assert "docs://guides" in categories
        assert "docs://guides/advanced" in categories
        assert "docs://api" in categories

        # Check hierarchy relationships
        guides = categories["docs://guides"]
        assert "docs://guides/advanced" in guides.child_categories

    def test_navigate_through_hierarchy(self, loaded_documentation):
        """Test navigating through the documentation hierarchy."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # Start at root
        root_context = navigate_to_uri("docs://", docs, cats)
        assert root_context.current_type == "root"
        assert len(root_context.children) > 0

        # Navigate to guides
        guides_context = navigate_to_uri("docs://guides", docs, cats)
        assert guides_context.current_type == "category"
        assert guides_context.parent_uri == "docs://"

        # Navigate to a document
        doc_context = navigate_to_uri("docs://guides/getting-started", docs, cats)
        assert doc_context.current_type == "document"
        assert doc_context.parent_uri == "docs://guides"

    def test_search_across_all_documents(self, loaded_documentation):
        """Test searching across all documentation."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # Search for "authentication"
        results = search_content("authentication", docs, cats, limit=10)

        # Should find authentication in API docs
        assert len(results) > 0

        # Results should have authentication-related docs
        uris = [r.document_uri for r in results]
        assert any("authentication" in uri for uri in uris)

    def test_search_by_tags(self, loaded_documentation):
        """Test searching by metadata tags."""
        docs = loaded_documentation["documents"]

        # Search for documents with "api" tag
        results = search_by_metadata(tags=["api"], documents=docs, limit=10)

        # Should find API documents
        assert len(results) > 0

        # All results should have "api" tag
        for result in results:
            doc = next((d for d in docs if d.uri == result.document_uri), None)
            if doc:
                assert "api" in doc.tags

    def test_table_of_contents_generation(self, loaded_documentation):
        """Test generating complete table of contents."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        toc = get_table_of_contents(cats, docs)

        # Should have root with children
        assert toc["type"] == "root"
        assert len(toc["children"]) > 0

        # Should have nested structure
        for child in toc["children"]:
            if child["uri"] == "docs://guides":
                # Guides should have nested children
                assert len(child["children"]) > 0

    def test_breadcrumb_trails(self, loaded_documentation):
        """Test breadcrumb generation for nested documents."""
        # Get breadcrumbs for nested document
        breadcrumbs = get_breadcrumbs("docs://guides/advanced/performance")

        # Should have 3 levels
        assert len(breadcrumbs) == 3
        assert breadcrumbs[0]["name"] == "Guides"
        assert breadcrumbs[1]["name"] == "Advanced"
        assert breadcrumbs[2]["name"] == "Performance"


class TestMCPToolsIntegration:
    """Test MCP tool handlers with real documentation."""

    @pytest.mark.asyncio
    async def test_search_tool_workflow(self, loaded_documentation):
        """Test complete search workflow through MCP tool."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        arguments = {
            "query": "performance optimization",
            "limit": 5,
        }

        results = await handle_search_documentation(arguments, docs, cats, 10)

        # Should find performance-related documents
        assert len(results) > 0

        # Check result structure
        result = results[0]
        assert "uri" in result
        assert "title" in result
        assert "excerpt" in result
        assert "breadcrumbs" in result

    @pytest.mark.asyncio
    async def test_navigate_tool_workflow(self, loaded_documentation):
        """Test complete navigation workflow through MCP tool."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # Navigate to guides
        nav_result = await handle_navigate_to({"uri": "docs://guides"}, docs, cats)

        assert nav_result["current_uri"] == "docs://guides"
        assert len(nav_result["children"]) > 0

        # Verify we can navigate to child
        child_uri = nav_result["children"][0]["uri"]
        child_result = await handle_navigate_to({"uri": child_uri}, docs, cats)

        assert "current_uri" in child_result

    @pytest.mark.asyncio
    async def test_toc_tool_workflow(self, loaded_documentation):
        """Test TOC generation through MCP tool."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        toc = await handle_get_table_of_contents({}, docs, cats)

        # Should have complete hierarchy
        assert "children" in toc
        assert len(toc["children"]) >= 2  # guides and api

    @pytest.mark.asyncio
    async def test_category_filter_in_search(self, loaded_documentation):
        """Test searching with category filter."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # Search only in API category
        arguments = {
            "query": "user",
            "category": "api",
            "limit": 10,
        }

        results = await handle_search_documentation(arguments, docs, cats, 10)

        # Results should be from API category
        for result in results:
            if "category" in result:
                # Category names are title-cased from breadcrumbs
                assert result["category"] == "Api"


class TestMCPResourcesIntegration:
    """Test MCP resource handlers with real documentation."""

    @pytest.mark.asyncio
    async def test_read_document_resource(self, loaded_documentation):
        """Test reading document through resource handler."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        result = await handle_resource_read("docs://guides/getting-started", docs, cats)

        # Should return document content
        assert "text" in result
        assert "Getting Started" in result["text"]
        assert "Installation" in result["text"]

    @pytest.mark.asyncio
    async def test_read_category_resource(self, loaded_documentation):
        """Test reading category through resource handler."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        result = await handle_resource_read("docs://guides", docs, cats)

        # Should return category overview
        assert "text" in result
        # Should list child items
        assert len(result["text"]) > 0

    @pytest.mark.asyncio
    async def test_list_all_resources(self, loaded_documentation):
        """Test listing all available resources."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        resources = await list_resources(docs, cats)

        # Should have root + categories + documents
        assert len(resources) >= 8  # root + 3 cats + 5 docs

        # Check resource types
        uris = [r["uri"] for r in resources]
        assert "docs://" in uris
        assert "docs://guides" in uris
        assert "docs://guides/getting-started" in uris


class TestComplexQueries:
    """Test complex query scenarios."""

    def test_search_with_code_blocks(self, loaded_documentation):
        """Test searching content with code blocks."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # Search for code-related terms
        results = search_content("pip install", docs, cats, limit=10)

        # Should find getting-started guide
        assert len(results) > 0

    def test_search_across_frontmatter(self, loaded_documentation):
        """Test searching across frontmatter metadata."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # Search by title
        results = search_content("Configuration", docs, cats, limit=10)

        # Should find configuration guide
        assert len(results) > 0
        assert any("configuration" in r.document_uri.lower() for r in results)

    def test_navigation_with_deeply_nested_structure(self, loaded_documentation):
        """Test navigation in deeply nested structure."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # Navigate to nested document
        context = navigate_to_uri("docs://guides/advanced/performance", docs, cats)

        assert context.current_type == "document"
        assert len(context.breadcrumbs) == 3

    def test_document_count_in_categories(self, loaded_documentation):
        """Test that category document counts are accurate."""
        cats = loaded_documentation["categories"]

        guides = cats["docs://guides"]
        # Should count getting-started, configuration, and performance
        assert guides.document_count >= 3

        api = cats["docs://api"]
        # Should count authentication and users
        assert api.document_count >= 2


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    @pytest.mark.asyncio
    async def test_user_finds_api_documentation(self, loaded_documentation):
        """Simulate user looking for API documentation."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # User searches for "authentication"
        search_results = await handle_search_documentation(
            {"query": "authentication", "limit": 10}, docs, cats, 10
        )

        assert len(search_results) > 0

        # User navigates to first result
        first_result_uri = search_results[0]["uri"]
        nav_result = await handle_navigate_to({"uri": first_result_uri}, docs, cats)

        assert nav_result["current_type"] == "document"

        # User reads the document
        doc_content = await handle_resource_read(first_result_uri, docs, cats)

        assert "text" in doc_content
        assert "authentication" in doc_content["text"].lower()

    @pytest.mark.asyncio
    async def test_user_browses_from_root(self, loaded_documentation):
        """Simulate user browsing from documentation root."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # User starts at root
        root_nav = await handle_navigate_to({"uri": "docs://"}, docs, cats)

        assert root_nav["current_type"] == "root"
        assert len(root_nav["children"]) > 0

        # User clicks on "guides" category
        guides_nav = await handle_navigate_to({"uri": "docs://guides"}, docs, cats)

        assert guides_nav["current_type"] == "category"
        assert len(guides_nav["children"]) > 0

        # User selects "Getting Started"
        getting_started = await handle_navigate_to(
            {"uri": "docs://guides/getting-started"}, docs, cats
        )

        assert getting_started["current_type"] == "document"

    @pytest.mark.asyncio
    async def test_ai_assistant_explores_documentation(self, loaded_documentation):
        """Simulate AI assistant exploring and summarizing documentation."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # AI gets table of contents
        toc = await handle_get_table_of_contents({}, docs, cats)

        # AI identifies main categories
        category_count = len(toc["children"])
        assert category_count >= 2  # guides and api

        # AI searches for specific topics
        perf_results = await handle_search_documentation(
            {"query": "performance", "limit": 5}, docs, cats, 10
        )

        # AI can find relevant content
        assert len(perf_results) > 0

    def test_cache_improves_repeated_queries(self, loaded_documentation):
        """Test that repeated queries benefit from caching."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        # First query
        results1 = search_content("authentication", docs, cats, limit=10)

        # Second identical query (should hit cache)
        results2 = search_content("authentication", docs, cats, limit=10)

        # Results should be consistent
        assert len(results1) == len(results2)
        assert results1[0].document_uri == results2[0].document_uri


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_search_with_invalid_category(self, loaded_documentation):
        """Test search with nonexistent category filter."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        results = await handle_search_documentation(
            {"query": "test", "category": "nonexistent", "limit": 10},
            docs,
            cats,
            10,
        )

        # Should return empty results, not error
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_navigate_to_invalid_uri(self, loaded_documentation):
        """Test navigation to invalid URI."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        result = await handle_navigate_to({"uri": "docs://nonexistent"}, docs, cats)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_read_nonexistent_resource(self, loaded_documentation):
        """Test reading nonexistent resource."""
        docs = loaded_documentation["documents"]
        cats = loaded_documentation["categories"]

        result = await handle_resource_read("docs://nonexistent", docs, cats)

        assert "error" in result
