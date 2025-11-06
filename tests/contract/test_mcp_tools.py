"""Contract tests for MCP tool handlers."""

import pytest
from datetime import datetime
from pathlib import Path

from hierarchical_docs_mcp.handlers.tools import (
    handle_search_documentation,
    handle_navigate_to,
    handle_get_table_of_contents,
    handle_search_by_tags,
    handle_get_document,
)
from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.services.hierarchy import build_category_tree


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    base_time = datetime.utcnow()

    return [
        Document(
            file_path=Path("/docs/guides/getting-started.md"),
            relative_path=Path("guides/getting-started.md"),
            uri="docs://guides/getting-started",
            title="Getting Started Guide",
            content="# Getting Started\n\nThis guide helps you get started with authentication.",
            tags=["tutorial", "beginner", "authentication"],
            category="guides",
            order=1,
            last_modified=base_time,
            size_bytes=100,
        ),
        Document(
            file_path=Path("/docs/guides/advanced/performance.md"),
            relative_path=Path("guides/advanced/performance.md"),
            uri="docs://guides/advanced/performance",
            title="Performance Optimization",
            content="# Performance\n\nAdvanced performance tips and optimization techniques.",
            tags=["advanced", "optimization", "performance"],
            category="guides",
            order=2,
            last_modified=base_time,
            size_bytes=200,
        ),
        Document(
            file_path=Path("/docs/api/authentication.md"),
            relative_path=Path("api/authentication.md"),
            uri="docs://api/authentication",
            title="Authentication API",
            content="# Authentication API\n\nAPI endpoints for user authentication.",
            tags=["api", "security", "authentication"],
            category="api",
            order=1,
            last_modified=base_time,
            size_bytes=150,
        ),
    ]


@pytest.fixture
def categories(sample_documents):
    """Build category tree from sample documents."""
    return build_category_tree(sample_documents)


class TestSearchDocumentationTool:
    """Test search_documentation tool contract."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, sample_documents, categories):
        """Test that search returns results with correct structure."""
        arguments = {"query": "authentication", "limit": 10}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, search_limit=10
        )

        assert isinstance(results, list)
        assert len(results) > 0

        # Check first result structure
        result = results[0]
        assert "uri" in result
        assert "title" in result
        assert "excerpt" in result
        assert "breadcrumbs" in result
        assert "category" in result
        assert "relevance" in result
        assert "match_type" in result

    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, sample_documents, categories):
        """Test search with category filter."""
        arguments = {"query": "authentication", "category": "api", "limit": 10}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, search_limit=10
        )

        # All results should be from api category
        for result in results:
            if "uri" in result:
                assert "api" in result["category"] or "api" in result["uri"]

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, sample_documents, categories):
        """Test that search respects result limit."""
        arguments = {"query": "guide", "limit": 1}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, search_limit=10
        )

        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, sample_documents, categories):
        """Test search with empty query."""
        arguments = {"query": "", "limit": 10}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, search_limit=10
        )

        # Should return empty or all documents
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_no_results(self, sample_documents, categories):
        """Test search that returns no results."""
        arguments = {"query": "nonexistent_term_xyz", "limit": 10}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, search_limit=10
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_result_has_breadcrumbs(self, sample_documents, categories):
        """Test that search results include breadcrumb paths."""
        arguments = {"query": "authentication", "limit": 10}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, search_limit=10
        )

        if len(results) > 0 and "breadcrumbs" in results[0]:
            # Breadcrumbs should be a string like "Guides > Getting Started"
            assert isinstance(results[0]["breadcrumbs"], str)

    @pytest.mark.asyncio
    async def test_search_relevance_score(self, sample_documents, categories):
        """Test that results include relevance scores."""
        arguments = {"query": "authentication", "limit": 10}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, search_limit=10
        )

        for result in results:
            if "relevance" in result:
                assert isinstance(result["relevance"], (int, float))
                assert result["relevance"] >= 0


class TestNavigateToTool:
    """Test navigate_to tool contract."""

    @pytest.mark.asyncio
    async def test_navigate_to_root(self, sample_documents, categories):
        """Test navigating to root URI."""
        arguments = {"uri": "docs://"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        assert "current_uri" in result
        assert result["current_uri"] == "docs://"
        assert result["current_type"] == "root"
        assert "children" in result
        assert isinstance(result["children"], list)

    @pytest.mark.asyncio
    async def test_navigate_to_category(self, sample_documents, categories):
        """Test navigating to a category."""
        arguments = {"uri": "docs://guides"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        assert result["current_uri"] == "docs://guides"
        assert result["current_type"] == "category"
        assert "parent_uri" in result
        assert "breadcrumbs" in result
        assert "children" in result

    @pytest.mark.asyncio
    async def test_navigate_to_document(self, sample_documents, categories):
        """Test navigating to a document."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        assert result["current_uri"] == "docs://guides/getting-started"
        assert result["current_type"] == "document"
        assert result["parent_uri"] is not None

    @pytest.mark.asyncio
    async def test_navigate_invalid_uri(self, sample_documents, categories):
        """Test navigating to invalid URI returns error."""
        arguments = {"uri": "docs://nonexistent"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_navigate_result_has_navigation_options(
        self, sample_documents, categories
    ):
        """Test that navigation result includes navigation options."""
        arguments = {"uri": "docs://guides"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        assert "navigation_options" in result
        assert isinstance(result["navigation_options"], dict)

    @pytest.mark.asyncio
    async def test_navigate_breadcrumbs_structure(self, sample_documents, categories):
        """Test that breadcrumbs have correct structure."""
        arguments = {"uri": "docs://guides/advanced"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        if "breadcrumbs" in result and len(result["breadcrumbs"]) > 0:
            breadcrumb = result["breadcrumbs"][0]
            # Each breadcrumb should have name and uri
            assert "name" in breadcrumb or "uri" in breadcrumb

    @pytest.mark.asyncio
    async def test_navigate_children_structure(self, sample_documents, categories):
        """Test that children have correct structure."""
        arguments = {"uri": "docs://guides"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        if len(result["children"]) > 0:
            child = result["children"][0]
            assert "type" in child
            assert "uri" in child
            assert "name" in child


class TestGetTableOfContentsTool:
    """Test get_table_of_contents tool contract."""

    @pytest.mark.asyncio
    async def test_toc_basic_structure(self, sample_documents, categories):
        """Test that TOC has correct basic structure."""
        arguments = {}

        result = await handle_get_table_of_contents(
            arguments, sample_documents, categories
        )

        assert "type" in result
        assert result["type"] == "root"
        assert "uri" in result
        assert "children" in result
        assert isinstance(result["children"], list)

    @pytest.mark.asyncio
    async def test_toc_includes_categories(self, sample_documents, categories):
        """Test that TOC includes categories."""
        arguments = {}

        result = await handle_get_table_of_contents(
            arguments, sample_documents, categories
        )

        # Should have at least guides and api categories
        assert len(result["children"]) > 0

        # Check structure of a category node
        if len(result["children"]) > 0:
            category_node = result["children"][0]
            assert "type" in category_node
            assert "uri" in category_node
            assert "name" in category_node

    @pytest.mark.asyncio
    async def test_toc_with_max_depth(self, sample_documents, categories):
        """Test TOC generation with max_depth parameter."""
        arguments = {"max_depth": 1}

        result = await handle_get_table_of_contents(
            arguments, sample_documents, categories
        )

        # Should still return valid structure
        assert "type" in result
        assert "children" in result

    @pytest.mark.asyncio
    async def test_toc_nested_structure(self, sample_documents, categories):
        """Test that TOC includes nested structure."""
        arguments = {}

        result = await handle_get_table_of_contents(
            arguments, sample_documents, categories
        )

        # Look for nested children
        for child in result["children"]:
            if "children" in child:
                assert isinstance(child["children"], list)


class TestSearchByTagsTool:
    """Test search_by_tags tool contract."""

    @pytest.mark.asyncio
    async def test_search_by_single_tag(self, sample_documents, categories):
        """Test searching by a single tag."""
        arguments = {"tags": ["authentication"], "limit": 10}

        results = await handle_search_by_tags(
            arguments, sample_documents, search_limit=10
        )

        assert isinstance(results, list)
        # Should find documents with authentication tag
        assert len(results) > 0

        # Check result structure
        if len(results) > 0:
            result = results[0]
            assert "uri" in result
            assert "title" in result

    @pytest.mark.asyncio
    async def test_search_by_multiple_tags(self, sample_documents, categories):
        """Test searching by multiple tags."""
        arguments = {"tags": ["advanced", "performance"], "limit": 10}

        results = await handle_search_by_tags(
            arguments, sample_documents, search_limit=10
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_by_tags_respects_limit(self, sample_documents, categories):
        """Test that tag search respects limit."""
        arguments = {"tags": ["tutorial"], "limit": 1}

        results = await handle_search_by_tags(
            arguments, sample_documents, search_limit=10
        )

        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_by_nonexistent_tag(self, sample_documents, categories):
        """Test searching for nonexistent tag."""
        arguments = {"tags": ["nonexistent_tag"], "limit": 10}

        results = await handle_search_by_tags(
            arguments, sample_documents, search_limit=10
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_by_tags_with_category_filter(
        self, sample_documents, categories
    ):
        """Test tag search with category filter."""
        arguments = {"tags": ["authentication"], "category": "guides", "limit": 10}

        results = await handle_search_by_tags(
            arguments, sample_documents, search_limit=10
        )

        # Results should be filtered by category
        for result in results:
            if "category" in result:
                assert result["category"] == "guides"


class TestGetDocumentTool:
    """Test get_document tool contract."""

    @pytest.mark.asyncio
    async def test_get_document_by_uri(self, sample_documents, categories):
        """Test getting a document by URI."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_get_document(arguments, sample_documents)

        assert "uri" in result
        assert result["uri"] == "docs://guides/getting-started"
        assert "title" in result
        assert "content" in result

    @pytest.mark.asyncio
    async def test_get_document_includes_metadata(self, sample_documents, categories):
        """Test that get_document includes metadata."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_get_document(arguments, sample_documents)

        assert "tags" in result
        assert "category" in result
        assert "last_modified" in result

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, sample_documents, categories):
        """Test getting nonexistent document returns error."""
        arguments = {"uri": "docs://nonexistent"}

        result = await handle_get_document(arguments, sample_documents)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_document_content_preserved(self, sample_documents, categories):
        """Test that document content is fully preserved."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_get_document(arguments, sample_documents)

        # Content should be present and non-empty
        assert "content" in result
        assert len(result["content"]) > 0


class TestToolContractCompliance:
    """Test that all tools follow MCP contract requirements."""

    @pytest.mark.asyncio
    async def test_all_tools_return_valid_json(self, sample_documents, categories):
        """Test that all tools return JSON-serializable data."""
        import json

        # Test each tool
        tools = [
            handle_search_documentation(
                {"query": "test", "limit": 10}, sample_documents, categories, 10
            ),
            handle_navigate_to({"uri": "docs://"}, sample_documents, categories),
            handle_get_table_of_contents({}, sample_documents, categories),
            handle_search_by_tags({"tags": ["test"], "limit": 10}, sample_documents, 10),
            handle_get_document(
                {"uri": "docs://guides/getting-started"}, sample_documents
            ),
        ]

        for tool_result in tools:
            result = await tool_result
            # Should be JSON serializable
            try:
                json.dumps(result)
            except (TypeError, ValueError):
                pytest.fail(f"Tool result is not JSON serializable: {result}")

    @pytest.mark.asyncio
    async def test_tools_handle_missing_arguments(self, sample_documents, categories):
        """Test that tools handle missing arguments gracefully."""
        # Search without query
        result1 = await handle_search_documentation(
            {}, sample_documents, categories, 10
        )
        assert isinstance(result1, list)

        # Navigate without URI
        result2 = await handle_navigate_to({}, sample_documents, categories)
        assert isinstance(result2, dict)

        # Get document without URI
        result3 = await handle_get_document({}, sample_documents)
        assert isinstance(result3, dict)

    @pytest.mark.asyncio
    async def test_tools_handle_invalid_arguments(self, sample_documents, categories):
        """Test that tools handle invalid argument types gracefully."""
        # Search with invalid query type
        result1 = await handle_search_documentation(
            {"query": 123}, sample_documents, categories, 10
        )
        assert isinstance(result1, list)

        # Navigate with invalid URI type
        result2 = await handle_navigate_to(
            {"uri": None}, sample_documents, categories
        )
        assert isinstance(result2, dict)


class TestToolResponseFormats:
    """Test that tool responses follow expected formats."""

    @pytest.mark.asyncio
    async def test_search_result_fields(self, sample_documents, categories):
        """Test that search results have all expected fields."""
        arguments = {"query": "authentication", "limit": 10}

        results = await handle_search_documentation(
            arguments, sample_documents, categories, 10
        )

        required_fields = ["uri", "title", "excerpt", "breadcrumbs", "relevance"]

        for result in results:
            if "error" not in result:
                for field in required_fields:
                    assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_navigation_result_fields(self, sample_documents, categories):
        """Test that navigation results have all expected fields."""
        arguments = {"uri": "docs://guides"}

        result = await handle_navigate_to(arguments, sample_documents, categories)

        if "error" not in result:
            required_fields = [
                "current_uri",
                "current_type",
                "breadcrumbs",
                "children",
                "navigation_options",
            ]

            for field in required_fields:
                assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_document_result_fields(self, sample_documents, categories):
        """Test that document results have all expected fields."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_get_document(arguments, sample_documents)

        if "error" not in result:
            required_fields = ["uri", "title", "content", "tags", "category"]

            for field in required_fields:
                assert field in result, f"Missing field: {field}"
