"""Unit tests for MCP tool handlers."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from hierarchical_docs_mcp.handlers.tools import (
    handle_get_document,
    handle_get_table_of_contents,
    handle_navigate_to,
    handle_search_by_tags,
    handle_search_documentation,
)
from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.models.navigation import Category


class TestHandleSearchDocumentation:
    """Test handle_search_documentation function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction to the system",
                category="guides",
                tags=["tutorial"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
            Document(uri="docs://api/authentication",
                title="Authentication",
                content="API authentication details",
                category="api",
                tags=["security"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
        ]

    @pytest.fixture
    def sample_categories(self):
        """Create sample categories for testing."""
        return {
            "docs://guides": Category(
                
                name="guides",
                uri="docs://guides",
                depth=1,
                label="Guides",
                child_documents=[],
                source_category="guides",
                child_categories=[],
                document_count=1,
            )
        }

    @pytest.mark.asyncio
    async def test_search_with_query(self, sample_documents, sample_categories):
        """Test searching with a query string."""
        arguments = {"query": "authentication"}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10)

        assert isinstance(results, list)
        assert len(results) > 0
        assert all("uri" in r for r in results)

    @pytest.mark.asyncio
    async def test_search_result_format(self, sample_documents, sample_categories):
        """Test search results have correct format."""
        arguments = {"query": "authentication"}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10)

        assert len(results) > 0
        result = results[0]
        assert "uri" in result
        assert "title" in result
        assert "excerpt" in result
        assert "breadcrumbs" in result
        assert "category" in result
        assert "relevance" in result
        assert "match_type" in result

    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, sample_documents, sample_categories):
        """Test searching with category filter."""
        arguments = {"query": "guide", "category": "guides"}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_limit(self, sample_documents, sample_categories):
        """Test searching with result limit."""
        arguments = {"query": "api", "limit": 1}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10)

        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_uses_default_limit(self, sample_documents, sample_categories):
        """Test search uses default limit when not specified."""
        arguments = {"query": "test"}

        with patch("hierarchical_docs_mcp.handlers.tools.search_content") as mock_search:
            mock_search.return_value = []
            await handle_search_documentation(
                arguments, sample_documents, sample_categories, search_limit=5)

            # Should use search_limit parameter as default
            assert mock_search.called
            call_kwargs = mock_search.call_args.kwargs
            assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, sample_documents, sample_categories):
        """Test searching with empty query."""
        arguments = {"query": ""}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_missing_query(self, sample_documents, sample_categories):
        """Test searching without query parameter."""
        arguments = {}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_handles_exception(self, sample_documents, sample_categories):
        """Test search handles exceptions gracefully."""
        arguments = {"query": "test"}

        with patch("hierarchical_docs_mcp.handlers.tools.search_content") as mock_search:
            mock_search.side_effect = Exception("Search error")

            results = await handle_search_documentation(
                arguments, sample_documents, sample_categories, search_limit=10)

            assert isinstance(results, list)
            assert len(results) > 0
            assert "error" in results[0]


class TestHandleNavigateTo:
    """Test handle_navigate_to function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction",
                category="guides",
                tags=[],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),)
        ]

    @pytest.fixture
    def sample_categories(self):
        """Create sample categories for testing."""
        return {
            "docs://": Category(
                
                name="root",
                uri="docs://",
                depth=0,
                label="Root",
                source_category="root",
                child_categories=["docs://guides"],
                child_documents=[],
                document_count=1,
            ),
            "docs://guides": Category(
                
                name="guides",
                uri="docs://guides",
                depth=1,
                label="Guides",
                child_documents=["docs://guides/getting-started"],
                source_category="guides",
                child_categories=[],
                document_count=1,
            ),
        }

    @pytest.mark.asyncio
    async def test_navigate_to_uri(self, sample_documents, sample_categories):
        """Test navigating to a URI."""
        arguments = {"uri": "docs://guides"}

        result = await handle_navigate_to(arguments, sample_documents, sample_categories)

        assert "current_uri" in result
        assert result["current_uri"] == "docs://guides"
        assert "current_type" in result
        assert "parent_uri" in result
        assert "breadcrumbs" in result
        assert "children" in result

    @pytest.mark.asyncio
    async def test_navigate_result_format(self, sample_documents, sample_categories):
        """Test navigation result has correct format."""
        arguments = {"uri": "docs://guides"}

        result = await handle_navigate_to(arguments, sample_documents, sample_categories)

        assert "current_uri" in result
        assert "current_type" in result
        assert "parent_uri" in result
        assert "breadcrumbs" in result
        assert "children" in result
        assert "sibling_count" in result
        assert "navigation_options" in result

    @pytest.mark.asyncio
    async def test_navigate_with_empty_uri(self, sample_documents, sample_categories):
        """Test navigating with empty URI."""
        arguments = {"uri": ""}

        result = await handle_navigate_to(arguments, sample_documents, sample_categories)

        # Should default to root or handle gracefully
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_navigate_with_missing_uri(self, sample_documents, sample_categories):
        """Test navigating without URI parameter."""
        arguments = {}

        result = await handle_navigate_to(arguments, sample_documents, sample_categories)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_navigate_handles_exception(self, sample_documents, sample_categories):
        """Test navigation handles exceptions gracefully."""
        arguments = {"uri": "docs://invalid"}

        with patch("hierarchical_docs_mcp.handlers.tools.navigate_to_uri") as mock_navigate:
            mock_navigate.side_effect = Exception("Navigation error")

            result = await handle_navigate_to(arguments, sample_documents, sample_categories)

            assert "error" in result
            assert "Navigation error" in result["error"]


class TestHandleGetTableOfContents:
    """Test handle_get_table_of_contents function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction",
                category="guides",
                tags=[],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),)
        ]

    @pytest.fixture
    def sample_categories(self):
        """Create sample categories for testing."""
        return {
            "docs://guides": Category(
                
                name="guides",
                uri="docs://guides",
                depth=1,
                label="Guides",
                child_documents=["docs://guides/getting-started"],
                source_category="guides",
                child_categories=[],
                document_count=1,
            )
        }

    @pytest.mark.asyncio
    async def test_get_table_of_contents(self, sample_documents, sample_categories):
        """Test getting table of contents."""
        arguments = {}

        result = await handle_get_table_of_contents(
            arguments, sample_documents, sample_categories)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_toc_with_max_depth(self, sample_documents, sample_categories):
        """Test getting table of contents with max_depth."""
        arguments = {"max_depth": 2}

        result = await handle_get_table_of_contents(
            arguments, sample_documents, sample_categories)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_toc_without_max_depth(self, sample_documents, sample_categories):
        """Test getting table of contents without max_depth."""
        arguments = {}

        result = await handle_get_table_of_contents(
            arguments, sample_documents, sample_categories)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_toc_handles_exception(self, sample_documents, sample_categories):
        """Test table of contents handles exceptions gracefully."""
        arguments = {}

        with patch("hierarchical_docs_mcp.handlers.tools.get_table_of_contents") as mock_toc:
            mock_toc.side_effect = Exception("TOC error")

            result = await handle_get_table_of_contents(
                arguments, sample_documents, sample_categories)

            assert "error" in result
            assert "TOC error" in result["error"]


class TestHandleSearchByTags:
    """Test handle_search_by_tags function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction",
                category="guides",
                tags=["tutorial", "beginner"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
            Document(uri="docs://api/authentication",
                title="Authentication",
                content="API docs",
                category="api",
                tags=["security", "api"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
        ]

    @pytest.mark.asyncio
    async def test_search_by_tags(self, sample_documents):
        """Test searching by tags."""
        arguments = {"tags": ["tutorial"]}

        results = await handle_search_by_tags(arguments, sample_documents, search_limit=10)

        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_by_tags_result_format(self, sample_documents):
        """Test search by tags result format."""
        arguments = {"tags": ["tutorial"]}

        results = await handle_search_by_tags(arguments, sample_documents, search_limit=10)

        assert len(results) > 0
        result = results[0]
        assert "uri" in result
        assert "title" in result
        assert "excerpt" in result
        assert "breadcrumbs" in result
        assert "category" in result
        assert "tags" in result

    @pytest.mark.asyncio
    async def test_search_by_tags_with_category(self, sample_documents):
        """Test searching by tags with category filter."""
        arguments = {"tags": ["tutorial"], "category": "guides"}

        results = await handle_search_by_tags(arguments, sample_documents, search_limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_by_tags_with_limit(self, sample_documents):
        """Test searching by tags with limit."""
        arguments = {"tags": ["tutorial"], "limit": 1}

        results = await handle_search_by_tags(arguments, sample_documents, search_limit=10)

        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_by_tags_uses_default_limit(self, sample_documents):
        """Test search by tags uses default limit."""
        arguments = {"tags": ["tutorial"]}

        with patch("hierarchical_docs_mcp.handlers.tools.search_by_metadata") as mock_search:
            mock_search.return_value = []
            await handle_search_by_tags(arguments, sample_documents, search_limit=5)

            assert mock_search.called
            call_kwargs = mock_search.call_args.kwargs
            assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_by_empty_tags(self, sample_documents):
        """Test searching with empty tags list."""
        arguments = {"tags": []}

        results = await handle_search_by_tags(arguments, sample_documents, search_limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_by_tags_missing_parameter(self, sample_documents):
        """Test searching without tags parameter."""
        arguments = {}

        results = await handle_search_by_tags(arguments, sample_documents, search_limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_by_tags_handles_exception(self, sample_documents):
        """Test search by tags handles exceptions gracefully."""
        arguments = {"tags": ["test"]}

        with patch("hierarchical_docs_mcp.handlers.tools.search_by_metadata") as mock_search:
            mock_search.side_effect = Exception("Tag search error")

            results = await handle_search_by_tags(arguments, sample_documents, search_limit=10)

            assert isinstance(results, list)
            assert len(results) > 0
            assert "error" in results[0]


class TestHandleGetDocument:
    """Test handle_get_document function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(uri="docs://guides/getting-started",
                title="Getting Started",
                content="# Getting Started\n\nIntroduction to the system.",
                category="guides",
                tags=["tutorial", "beginner"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),)
        ]

    @pytest.mark.asyncio
    async def test_get_document(self, sample_documents):
        """Test getting a document."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_get_document(arguments, sample_documents)

        assert "uri" in result
        assert result["uri"] == "docs://guides/getting-started"
        assert "title" in result
        assert result["title"] == "Getting Started"
        assert "content" in result
        assert "tags" in result
        assert "category" in result
        assert "last_modified" in result
        assert "breadcrumbs" in result

    @pytest.mark.asyncio
    async def test_get_document_includes_all_fields(self, sample_documents):
        """Test get document includes all required fields."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_get_document(arguments, sample_documents)

        assert result["uri"] == "docs://guides/getting-started"
        assert result["title"] == "Getting Started"
        assert result["content"] == "# Getting Started\n\nIntroduction to the system."
        assert result["tags"] == ["tutorial", "beginner"]
        assert result["category"] == "guides"
        assert result["last_modified"] == "2024-01-01T12:00:00+00:00"
        assert isinstance(result["breadcrumbs"], list)

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, sample_documents):
        """Test getting a non-existent document."""
        arguments = {"uri": "docs://nonexistent"}

        result = await handle_get_document(arguments, sample_documents)

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_document_with_empty_uri(self, sample_documents):
        """Test getting document with empty URI."""
        arguments = {"uri": ""}

        result = await handle_get_document(arguments, sample_documents)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_document_without_uri(self, sample_documents):
        """Test getting document without URI parameter."""
        arguments = {}

        result = await handle_get_document(arguments, sample_documents)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_document_handles_exception(self, sample_documents):
        """Test get document handles exceptions gracefully."""
        arguments = {"uri": "docs://test"}

        with patch("hierarchical_docs_mcp.handlers.tools.logger"):
            # Simulate exception by making sample_documents invalid
            result = await handle_get_document(arguments, None)

            assert "error" in result

    @pytest.mark.asyncio
    async def test_get_document_breadcrumbs_format(self, sample_documents):
        """Test get document returns breadcrumbs as list."""
        arguments = {"uri": "docs://guides/getting-started"}

        result = await handle_get_document(arguments, sample_documents)

        assert isinstance(result["breadcrumbs"], list)

    @pytest.mark.asyncio
    async def test_get_document_with_multiple_tags(self):
        """Test getting document with multiple tags."""
        documents = [
            Document(uri="docs://test",
                title="Test",
                content="Test content",
                category="test",
                tags=["tag1", "tag2", "tag3"],
                file_path="/test.md",
                relative_path="test.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),)
        ]

        arguments = {"uri": "docs://test"}
        result = await handle_get_document(arguments, documents)

        assert result["tags"] == ["tag1", "tag2", "tag3"]

    @pytest.mark.asyncio
    async def test_get_document_with_no_tags(self):
        """Test getting document with no tags."""
        documents = [
            Document(uri="docs://test",
                title="Test",
                content="Test content",
                category="test",
                tags=[],
                file_path="/test.md",
                relative_path="test.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),)
        ]

        arguments = {"uri": "docs://test"}
        result = await handle_get_document(arguments, documents)

        assert result["tags"] == []
