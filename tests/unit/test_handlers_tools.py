"""Unit tests for MCP tool handlers."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.mcp.handlers.tools import (
    handle_generate_pdf_release,
    handle_get_all_tags,
    handle_get_document,
    handle_get_table_of_contents,
    handle_navigate_to,
    handle_search_by_tags,
    handle_search_documentation,
)


class TestHandleSearchDocumentation:
    """Test handle_search_documentation function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction to the system",
                category="guides",
                tags=["tutorial"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            ),
            Document(
                uri="docs://api/authentication",
                title="Authentication",
                content="API authentication details",
                category="api",
                tags=["security"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            ),
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
            arguments, sample_documents, sample_categories, search_limit=10
        )

        assert isinstance(results, list)
        assert len(results) > 0
        assert all("uri" in r for r in results)

    @pytest.mark.asyncio
    async def test_search_result_format(self, sample_documents, sample_categories):
        """Test search results have correct format."""
        arguments = {"query": "authentication"}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10
        )

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
            arguments, sample_documents, sample_categories, search_limit=10
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_limit(self, sample_documents, sample_categories):
        """Test searching with result limit."""
        arguments = {"query": "api", "limit": 1}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10
        )

        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_uses_default_limit(self, sample_documents, sample_categories):
        """Test search uses default limit when not specified."""
        arguments = {"query": "test"}

        with patch("docs_mcp.mcp.handlers.tools.search_content") as mock_search:
            mock_search.return_value = []
            await handle_search_documentation(
                arguments, sample_documents, sample_categories, search_limit=5
            )

            # Should use search_limit parameter as default
            assert mock_search.called
            call_kwargs = mock_search.call_args.kwargs
            assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, sample_documents, sample_categories):
        """Test searching with empty query."""
        arguments = {"query": ""}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_missing_query(self, sample_documents, sample_categories):
        """Test searching without query parameter."""
        arguments = {}

        results = await handle_search_documentation(
            arguments, sample_documents, sample_categories, search_limit=10
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_handles_exception(self, sample_documents, sample_categories):
        """Test search handles exceptions gracefully."""
        arguments = {"query": "test"}

        with patch("docs_mcp.mcp.handlers.tools.search_content") as mock_search:
            mock_search.side_effect = Exception("Search error")

            results = await handle_search_documentation(
                arguments, sample_documents, sample_categories, search_limit=10
            )

            assert isinstance(results, list)
            assert len(results) > 0
            assert "error" in results[0]


class TestHandleNavigateTo:
    """Test handle_navigate_to function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction",
                category="guides",
                tags=[],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            )
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

        with patch("docs_mcp.mcp.handlers.tools.navigate_to_uri") as mock_navigate:
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
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction",
                category="guides",
                tags=[],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            )
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

        result = await handle_get_table_of_contents(arguments, sample_documents, sample_categories)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_toc_with_max_depth(self, sample_documents, sample_categories):
        """Test getting table of contents with max_depth."""
        arguments = {"max_depth": 2}

        result = await handle_get_table_of_contents(arguments, sample_documents, sample_categories)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_toc_without_max_depth(self, sample_documents, sample_categories):
        """Test getting table of contents without max_depth."""
        arguments = {}

        result = await handle_get_table_of_contents(arguments, sample_documents, sample_categories)

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_toc_handles_exception(self, sample_documents, sample_categories):
        """Test table of contents handles exceptions gracefully."""
        arguments = {}

        with patch("docs_mcp.mcp.handlers.tools.get_table_of_contents") as mock_toc:
            mock_toc.side_effect = Exception("TOC error")

            result = await handle_get_table_of_contents(
                arguments, sample_documents, sample_categories
            )

            assert "error" in result
            assert "TOC error" in result["error"]


class TestHandleSearchByTags:
    """Test handle_search_by_tags function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction",
                category="guides",
                tags=["tutorial", "beginner"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            ),
            Document(
                uri="docs://api/authentication",
                title="Authentication",
                content="API docs",
                category="api",
                tags=["security", "api"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            ),
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

        with patch("docs_mcp.mcp.handlers.tools.search_by_metadata") as mock_search:
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

        with patch("docs_mcp.mcp.handlers.tools.search_by_metadata") as mock_search:
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
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="# Getting Started\n\nIntroduction to the system.",
                category="guides",
                tags=["tutorial", "beginner"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
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

        with patch("docs_mcp.mcp.handlers.tools.logger"):
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
            Document(
                uri="docs://test",
                title="Test",
                content="Test content",
                category="test",
                tags=["tag1", "tag2", "tag3"],
                file_path="/test.md",
                relative_path="test.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            )
        ]

        arguments = {"uri": "docs://test"}
        result = await handle_get_document(arguments, documents)

        assert result["tags"] == ["tag1", "tag2", "tag3"]

    @pytest.mark.asyncio
    async def test_get_document_with_no_tags(self):
        """Test getting document with no tags."""
        documents = [
            Document(
                uri="docs://test",
                title="Test",
                content="Test content",
                category="test",
                tags=[],
                file_path="/test.md",
                relative_path="test.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            )
        ]

        arguments = {"uri": "docs://test"}
        result = await handle_get_document(arguments, documents)

        assert result["tags"] == []


class TestHandleGetAllTags:
    """Test handle_get_all_tags function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction",
                category="guides",
                tags=["tutorial", "beginner"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            ),
            Document(
                uri="docs://api/authentication",
                title="Authentication",
                content="API docs",
                category="api",
                tags=["security", "api", "tutorial"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            ),
            Document(
                uri="docs://api/authorization",
                title="Authorization",
                content="Authorization docs",
                category="api",
                tags=["security", "api"],
                file_path="/docs/api/authorization.md",
                relative_path="docs/api/authorization.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_all_tags(self, sample_documents):
        """Test getting all unique tags."""
        arguments = {}

        result = await handle_get_all_tags(arguments, sample_documents)

        assert "tags" in result
        assert "count" in result
        assert isinstance(result["tags"], list)
        # Should have 4 unique tags: api, beginner, security, tutorial
        assert result["count"] == 4
        assert sorted(result["tags"]) == ["api", "beginner", "security", "tutorial"]

    @pytest.mark.asyncio
    async def test_get_all_tags_sorted_alphabetically(self, sample_documents):
        """Test tags are sorted alphabetically."""
        arguments = {}

        result = await handle_get_all_tags(arguments, sample_documents)

        assert result["tags"] == sorted(result["tags"])

    @pytest.mark.asyncio
    async def test_get_all_tags_with_category_filter(self, sample_documents):
        """Test filtering tags by category."""
        arguments = {"category": "api"}

        result = await handle_get_all_tags(arguments, sample_documents)

        # Only api and security tags from api category (tutorial appears in api too)
        assert "tags" in result
        assert "api" in result["tags"]
        assert "security" in result["tags"]
        assert "tutorial" in result["tags"]
        assert "beginner" not in result["tags"]

    @pytest.mark.asyncio
    async def test_get_all_tags_with_include_counts(self, sample_documents):
        """Test including document counts per tag."""
        arguments = {"include_counts": True}

        result = await handle_get_all_tags(arguments, sample_documents)

        assert "tags" in result
        assert "count" in result
        assert "tag_counts" in result
        assert isinstance(result["tag_counts"], list)

        # Verify structure of tag_counts
        for item in result["tag_counts"]:
            assert "tag" in item
            assert "document_count" in item

    @pytest.mark.asyncio
    async def test_get_all_tags_counts_are_correct(self, sample_documents):
        """Test document counts are accurate."""
        arguments = {"include_counts": True}

        result = await handle_get_all_tags(arguments, sample_documents)

        tag_counts_dict = {item["tag"]: item["document_count"] for item in result["tag_counts"]}

        # tutorial appears in 2 docs (getting-started and authentication)
        assert tag_counts_dict["tutorial"] == 2
        # api appears in 2 docs (authentication and authorization)
        assert tag_counts_dict["api"] == 2
        # security appears in 2 docs
        assert tag_counts_dict["security"] == 2
        # beginner appears in 1 doc
        assert tag_counts_dict["beginner"] == 1

    @pytest.mark.asyncio
    async def test_get_all_tags_without_counts(self, sample_documents):
        """Test tag_counts is not included when include_counts is false."""
        arguments = {"include_counts": False}

        result = await handle_get_all_tags(arguments, sample_documents)

        assert "tags" in result
        assert "count" in result
        assert "tag_counts" not in result

    @pytest.mark.asyncio
    async def test_get_all_tags_with_category_and_counts(self, sample_documents):
        """Test combining category filter with counts."""
        arguments = {"category": "guides", "include_counts": True}

        result = await handle_get_all_tags(arguments, sample_documents)

        assert "tag_counts" in result
        # Only guides category has tutorial and beginner
        tag_names = [item["tag"] for item in result["tag_counts"]]
        assert "tutorial" in tag_names
        assert "beginner" in tag_names
        assert "api" not in tag_names

    @pytest.mark.asyncio
    async def test_get_all_tags_empty_documents(self):
        """Test with empty document list."""
        arguments = {}

        result = await handle_get_all_tags(arguments, [])

        assert result["tags"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_all_tags_no_matching_category(self, sample_documents):
        """Test with category that has no documents."""
        arguments = {"category": "nonexistent"}

        result = await handle_get_all_tags(arguments, sample_documents)

        assert result["tags"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_all_tags_documents_without_tags(self):
        """Test with documents that have no tags."""
        documents = [
            Document(
                uri="docs://test",
                title="Test",
                content="Test content",
                category="test",
                tags=[],
                file_path="/test.md",
                relative_path="test.md",
                size_bytes=100,
                last_modified=datetime.now(timezone.utc),
            )
        ]

        arguments = {}
        result = await handle_get_all_tags(arguments, documents)

        assert result["tags"] == []
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_get_all_tags_handles_exception(self):
        """Test get all tags handles exceptions gracefully."""
        arguments = {}

        # Pass None to trigger exception
        result = await handle_get_all_tags(arguments, None)  # type: ignore

        assert "error" in result


class TestHandleGeneratePdfRelease:
    """Test handle_generate_pdf_release function."""

    @pytest.fixture
    def mock_docs_root(self, tmp_path):
        """Create a mock docs root directory with a script."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script_path = scripts_dir / "generate-docs-pdf.sh"
        script_path.write_text("#!/bin/bash\necho 'PDF generated'\n")
        script_path.chmod(0o755)
        return docs_root

    @pytest.mark.asyncio
    async def test_generate_pdf_with_all_metadata(self, mock_docs_root):
        """Test generating PDF with all metadata fields."""
        arguments = {
            "title": "Test Documentation",
            "subtitle": "Complete Guide",
            "author": "Test Author",
            "version": "1.0.0",
            "confidential": True,
            "owner": "Test Corp",
        }

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock successful process execution
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            assert result["success"] is True
            assert "output_file" in result
            assert "manifest_file" in result

    @pytest.mark.asyncio
    async def test_generate_pdf_with_minimal_arguments(self, mock_docs_root):
        """Test generating PDF with minimal arguments (only version)."""
        arguments = {"version": "2.0.0"}

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_generate_pdf_default_version(self, mock_docs_root):
        """Test generating PDF without version (uses current date)."""
        arguments = {"title": "My Docs"}

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            assert result["success"] is True
            # Should use default version (current date)
            assert "output_file" in result

    @pytest.mark.asyncio
    async def test_generate_pdf_subtitle_included_in_command(self, mock_docs_root):
        """Test that subtitle parameter is properly passed to script."""
        arguments = {
            "title": "My Docs",
            "subtitle": "Technical Guide",
            "version": "1.0.0",
        }

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            await handle_generate_pdf_release(arguments, mock_docs_root)

            # Verify subtitle was passed in the command
            call_args = mock_subprocess.call_args
            cmd = call_args[0] if call_args else []
            # Should contain --subtitle flag
            assert "--subtitle" in cmd
            assert "Technical Guide" in cmd

    @pytest.mark.asyncio
    async def test_generate_pdf_confidential_flag(self, mock_docs_root):
        """Test that confidential flag is properly passed."""
        arguments = {
            "version": "1.0.0",
            "confidential": True,
            "owner": "ACME Corp",
        }

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            await handle_generate_pdf_release(arguments, mock_docs_root)

            call_args = mock_subprocess.call_args
            cmd = call_args[0] if call_args else []
            assert "--confidential" in cmd
            assert "--owner" in cmd
            assert "ACME Corp" in cmd

    @pytest.mark.asyncio
    async def test_generate_pdf_script_not_found(self, tmp_path):
        """Test error handling when script is not found."""
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        # Don't create scripts directory - and mock path checking to ensure script isn't found

        arguments = {"version": "1.0.0"}

        # Patch all possible script locations to not exist
        with patch("docs_mcp.mcp.handlers.tools.Path.exists", return_value=False):
            result = await handle_generate_pdf_release(arguments, docs_root)

            assert result["success"] is False
            assert "error" in result
            assert "script not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_pdf_script_execution_failed(self, mock_docs_root):
        """Test error handling when script execution fails."""
        arguments = {"version": "1.0.0"}

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(
                return_value=(b"", b"Error: PDF generation failed")
            )
            mock_subprocess.return_value = mock_process

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            assert result["success"] is False
            assert "error" in result
            assert "pdf generation failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_pdf_handles_exception(self, mock_docs_root):
        """Test exception handling during PDF generation."""
        arguments = {"version": "1.0.0"}

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_subprocess.side_effect = Exception("Subprocess error")

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            assert result["success"] is False
            assert "error" in result
            assert "subprocess error" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_pdf_empty_arguments(self, mock_docs_root):
        """Test generating PDF with empty arguments dictionary."""
        arguments = {}

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            # Should still work with defaults
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_generate_pdf_command_structure(self, mock_docs_root):
        """Test that command is properly structured with all parameters."""
        arguments = {
            "title": "Docs",
            "subtitle": "Guide",
            "author": "Team",
            "version": "1.0.0",
            "confidential": False,
        }

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            await handle_generate_pdf_release(arguments, mock_docs_root)

            call_args = mock_subprocess.call_args[0]
            # Should have script path as first argument
            assert str(call_args[0]).endswith("generate-docs-pdf.sh")
            # Should have all flags
            assert "--title" in call_args
            assert "--subtitle" in call_args
            assert "--author" in call_args
            # Confidential=False should not add --confidential flag
            assert "--confidential" not in call_args

    @pytest.mark.asyncio
    async def test_generate_pdf_result_format(self, mock_docs_root):
        """Test that result has correct format on success."""
        arguments = {"version": "1.0.0"}

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            stdout = "Done\nOutput: /path/to/output.pdf\nManifest: /path/to/manifest.json"
            mock_process.communicate = AsyncMock(return_value=(stdout.encode(), b""))
            mock_subprocess.return_value = mock_process

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            assert "success" in result
            assert "output_file" in result
            assert "manifest_file" in result
            assert result["output_file"] == "/path/to/output.pdf"
            assert result["manifest_file"] == "/path/to/manifest.json"

    @pytest.mark.asyncio
    async def test_generate_pdf_with_special_characters_in_metadata(self, mock_docs_root):
        """Test handling of special characters in metadata fields."""
        arguments = {
            "title": 'Test\'s "Documentation"',
            "subtitle": "Guide & Reference",
            "author": "O'Brien, Inc.",
            "version": "1.0.0",
        }

        with patch("docs_mcp.mcp.handlers.tools.asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            result = await handle_generate_pdf_release(arguments, mock_docs_root)

            # Should handle special characters without errors
            assert result["success"] is True
