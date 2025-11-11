"""Unit tests for search functionality."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.models.navigation import Category
from hierarchical_docs_mcp.services.search import (
    SearchError,
    _extract_excerpt,
    _highlight_matches,
    search_by_metadata,
    search_content,
)


class TestSearchContent:
    """Test search_content function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(uri="docs://guides/getting-started",
                title="Getting Started Guide",
                content="This is a comprehensive guide to getting started with the system. "
                "It covers installation, configuration, and basic usage.",
                category="guides",
                tags=["tutorial", "beginner"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
            Document(uri="docs://api/authentication",
                title="Authentication API",
                content="The authentication API provides endpoints for user login, "
                "logout, and token management. Use JWT tokens for secure access.",
                category="api",
                tags=["security", "api"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
            Document(uri="docs://guides/advanced",
                title="Advanced Topics",
                content="Advanced configuration options and optimization techniques. "
                "Learn how to fine-tune performance and customize behavior.",
                category="guides",
                tags=["advanced", "tutorial"],
                file_path="/docs/guides/advanced.md",
                relative_path="docs/guides/advanced.md",
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
                label="Guides",
                depth=0,
                source_category="guides",
                child_documents=["docs://guides/getting-started", "docs://guides/advanced"],
                child_categories=[],
                document_count=2,),
            "docs://api": Category(
                name="api",
                uri="docs://api",
                label="API",
                depth=0,
                source_category="api",
                child_documents=["docs://api/authentication"],
                child_categories=[],
                document_count=1,),
        }

    def test_search_content_basic_query(self, sample_documents, sample_categories):
        """Test basic content search."""
        results = search_content("authentication", sample_documents, sample_categories)

        assert len(results) > 0
        assert any("authentication" in r.title.lower() for r in results)

    def test_search_content_in_title(self, sample_documents, sample_categories):
        """Test search matching in document title."""
        results = search_content("Getting Started", sample_documents, sample_categories)

        assert len(results) > 0
        first_result = results[0]
        assert "Getting Started" in first_result.title
        assert first_result.match_type == "title"
        assert first_result.relevance_score > 0

    def test_search_content_in_body(self, sample_documents, sample_categories):
        """Test search matching in document content."""
        results = search_content("JWT", sample_documents, sample_categories)

        assert len(results) > 0
        assert any("JWT" in r.excerpt for r in results)

    def test_search_content_case_insensitive(self, sample_documents, sample_categories):
        """Test search is case-insensitive."""
        results_lower = search_content("authentication", sample_documents, sample_categories)
        results_upper = search_content("AUTHENTICATION", sample_documents, sample_categories)
        results_mixed = search_content("Authentication", sample_documents, sample_categories)

        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_content_with_limit(self, sample_documents, sample_categories):
        """Test search respects result limit."""
        results = search_content("guide", sample_documents, sample_categories, limit=1)

        assert len(results) == 1

    def test_search_content_with_category_filter(self, sample_documents, sample_categories):
        """Test search with category filter."""
        results = search_content(
            "guide", sample_documents, sample_categories, category_filter="guides")

        assert len(results) > 0
        assert all("guides" in r.document_uri for r in results)

    def test_search_content_empty_query(self, sample_documents, sample_categories):
        """Test search with empty query returns empty results."""
        results = search_content("", sample_documents, sample_categories)

        assert len(results) == 0

    def test_search_content_no_matches(self, sample_documents, sample_categories):
        """Test search with no matching documents."""
        results = search_content("xyznonexistent", sample_documents, sample_categories)

        assert len(results) == 0

    def test_search_content_relevance_scoring(self, sample_documents, sample_categories):
        """Test search results are sorted by relevance."""
        results = search_content("guide", sample_documents, sample_categories)

        assert len(results) > 0
        # Results should be sorted by relevance (highest first)
        for i in range(len(results) - 1):
            assert results[i].relevance_score >= results[i + 1].relevance_score

    def test_search_content_metadata_match(self, sample_documents, sample_categories):
        """Test search matching in metadata (tags, category)."""
        results = search_content("tutorial", sample_documents, sample_categories)

        assert len(results) > 0
        # Should match documents with 'tutorial' tag
        assert any("tutorial" in doc.tags for doc in sample_documents if doc.uri in [r.document_uri for r in results])

    def test_search_content_special_characters_escaped(self, sample_documents, sample_categories):
        """Test search handles regex special characters."""
        # This should not cause regex errors
        results = search_content("API.", sample_documents, sample_categories)

        # Should work without raising exceptions
        assert isinstance(results, list)

    def test_search_content_invalid_regex_raises_error(self, sample_documents, sample_categories):
        """Test search with invalid regex pattern."""
        with patch("hierarchical_docs_mcp.services.search.sanitize_query") as mock_sanitize:
            mock_sanitize.return_value = "["  # Invalid regex
            with pytest.raises(SearchError, match="Invalid search pattern"):
                search_content("[", sample_documents, sample_categories)

    def test_search_content_breadcrumbs_included(self, sample_documents, sample_categories):
        """Test search results include breadcrumbs."""
        results = search_content("authentication", sample_documents, sample_categories)

        assert len(results) > 0
        for result in results:
            assert isinstance(result.breadcrumbs, list)

    def test_search_content_highlighted_excerpt(self, sample_documents, sample_categories):
        """Test search results include highlighted excerpts."""
        results = search_content("authentication", sample_documents, sample_categories)

        assert len(results) > 0
        for result in results:
            if result.relevance_score > 0:
                assert result.excerpt != ""

    def test_search_content_multiple_matches(self, sample_documents, sample_categories):
        """Test search with multiple matching documents."""
        results = search_content("guide", sample_documents, sample_categories)

        # Should find multiple documents with "guide" in title or content
        assert len(results) >= 2

    def test_search_content_caching(self, sample_documents, sample_categories):
        """Test search results are cached."""
        # First search
        results1 = search_content("authentication", sample_documents, sample_categories)

        # Second search (should be cached)
        with patch("hierarchical_docs_mcp.services.search.get_cache") as mock_cache:
            mock_cache.return_value.get.return_value = results1
            results2 = search_content("authentication", sample_documents, sample_categories)

            # Should return cached results
            assert results1 == results2


class TestSearchByMetadata:
    """Test search_by_metadata function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(uri="docs://guides/getting-started",
                title="Getting Started",
                content="Introduction to the system",
                category="guides",
                tags=["tutorial", "beginner"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
            Document(uri="docs://api/authentication",
                title="Authentication",
                content="Authentication details",
                category="api",
                tags=["security", "api"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
            Document(uri="docs://guides/advanced",
                title="Advanced Guide",
                content="Advanced topics",
                category="guides",
                tags=["tutorial", "advanced"],
                file_path="/docs/guides/advanced.md",
                relative_path="docs/guides/advanced.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),),
        ]

    def test_search_by_tags(self, sample_documents):
        """Test searching by tags."""
        results = search_by_metadata(tags=["tutorial"], documents=sample_documents)

        assert len(results) > 0
        assert all("tutorial" in doc.tags for doc in sample_documents if doc.uri in [r.document_uri for r in results])

    def test_search_by_multiple_tags(self, sample_documents):
        """Test searching by multiple tags (OR logic)."""
        results = search_by_metadata(tags=["security", "beginner"], documents=sample_documents)

        assert len(results) >= 2
        # Should find documents with either "security" OR "beginner"

    def test_search_by_category(self, sample_documents):
        """Test searching by category."""
        results = search_by_metadata(category="guides", documents=sample_documents)

        assert len(results) == 2
        assert all(r.category == "guides" or "guides" in r.document_uri for r in results)

    def test_search_by_tags_and_category(self, sample_documents):
        """Test searching by both tags and category (AND logic)."""
        results = search_by_metadata(
            tags=["tutorial"], category="guides", documents=sample_documents)

        assert len(results) > 0
        # Should find documents that match BOTH criteria
        for result in results:
            matching_doc = next(d for d in sample_documents if d.uri == result.document_uri)
            assert "tutorial" in matching_doc.tags
            assert matching_doc.category == "guides"

    def test_search_by_metadata_with_limit(self, sample_documents):
        """Test metadata search respects limit."""
        results = search_by_metadata(tags=["tutorial"], documents=sample_documents, limit=1)

        assert len(results) == 1

    def test_search_by_metadata_no_matches(self, sample_documents):
        """Test metadata search with no matches."""
        results = search_by_metadata(tags=["nonexistent"], documents=sample_documents)

        assert len(results) == 0

    def test_search_by_metadata_empty_filters(self, sample_documents):
        """Test metadata search with no filters returns all documents."""
        results = search_by_metadata(documents=sample_documents, limit=10)

        assert len(results) == len(sample_documents)

    def test_search_by_metadata_none_documents(self):
        """Test metadata search with None documents."""
        results = search_by_metadata(tags=["test"], documents=None)

        assert len(results) == 0

    def test_search_by_metadata_includes_breadcrumbs(self, sample_documents):
        """Test metadata search results include breadcrumbs."""
        results = search_by_metadata(tags=["tutorial"], documents=sample_documents)

        assert len(results) > 0
        for result in results:
            assert isinstance(result.breadcrumbs, list)

    def test_search_by_metadata_includes_excerpt(self, sample_documents):
        """Test metadata search results include excerpt."""
        results = search_by_metadata(tags=["tutorial"], documents=sample_documents)

        assert len(results) > 0
        for result in results:
            assert result.excerpt != ""

    def test_search_by_metadata_match_type(self, sample_documents):
        """Test metadata search results have correct match type."""
        results = search_by_metadata(tags=["tutorial"], documents=sample_documents)

        assert len(results) > 0
        for result in results:
            assert result.match_type == "metadata"

    def test_search_by_metadata_relevance_score(self, sample_documents):
        """Test metadata search results have relevance score."""
        results = search_by_metadata(tags=["tutorial"], documents=sample_documents)

        assert len(results) > 0
        for result in results:
            assert result.relevance_score == 1.0


class TestExtractExcerpt:
    """Test _extract_excerpt helper function."""

    def test_extract_excerpt_with_match(self):
        """Test extracting excerpt with query match."""
        content = "This is a long document with some interesting content about Python programming."
        query = "interesting"

        excerpt = _extract_excerpt(content, query, context_chars=20)

        assert "interesting" in excerpt
        assert "..." in excerpt  # Should have ellipsis for truncation

    def test_extract_excerpt_no_match(self):
        """Test extracting excerpt when query doesn't match."""
        content = "This is a document without the search term."
        query = "nonexistent"

        excerpt = _extract_excerpt(content, query, context_chars=20)

        assert len(excerpt) > 0
        assert excerpt.endswith("...")

    def test_extract_excerpt_at_start(self):
        """Test extracting excerpt when match is at start."""
        content = "Python is a great language for programming and data science."
        query = "Python"

        excerpt = _extract_excerpt(content, query, context_chars=20)

        assert excerpt.startswith("Python")
        assert excerpt.endswith("...")

    def test_extract_excerpt_at_end(self):
        """Test extracting excerpt when match is at end."""
        content = "This document is about programming in Python"
        query = "Python"

        excerpt = _extract_excerpt(content, query, context_chars=20)

        assert "Python" in excerpt
        assert excerpt.startswith("...")

    def test_extract_excerpt_short_content(self):
        """Test extracting excerpt from short content."""
        content = "Short text"
        query = "text"

        excerpt = _extract_excerpt(content, query, context_chars=20)

        assert "text" in excerpt

    def test_extract_excerpt_case_insensitive(self):
        """Test extract excerpt is case-insensitive."""
        content = "This document contains PYTHON programming examples."
        query = "python"

        excerpt = _extract_excerpt(content, query, context_chars=20)

        assert "PYTHON" in excerpt


class TestHighlightMatches:
    """Test _highlight_matches helper function."""

    def test_highlight_matches_basic(self):
        """Test basic match highlighting."""
        text = "This is a test document"
        query = "test"

        highlighted = _highlight_matches(text, query)

        assert "**test**" in highlighted

    def test_highlight_matches_case_insensitive(self):
        """Test highlighting is case-insensitive."""
        text = "This is a TEST document"
        query = "test"

        highlighted = _highlight_matches(text, query)

        assert "**TEST**" in highlighted

    def test_highlight_matches_multiple_occurrences(self):
        """Test highlighting multiple occurrences."""
        text = "test test test"
        query = "test"

        highlighted = _highlight_matches(text, query)

        assert highlighted.count("**test**") == 3

    def test_highlight_matches_no_match(self):
        """Test highlighting with no matches."""
        text = "This is a document"
        query = "nonexistent"

        highlighted = _highlight_matches(text, query)

        assert highlighted == text

    def test_highlight_matches_custom_marker(self):
        """Test highlighting with custom marker."""
        text = "This is a test"
        query = "test"

        highlighted = _highlight_matches(text, query, highlight="__")

        assert "__test__" in highlighted

    def test_highlight_matches_special_characters(self):
        """Test highlighting handles special characters."""
        text = "Use API."
        query = "API."

        # Should not raise exception
        highlighted = _highlight_matches(text, query)
        assert isinstance(highlighted, str)


class TestSearchError:
    """Test SearchError exception."""

    def test_search_error_creation(self):
        """Test creating SearchError."""
        error = SearchError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_search_error_can_be_raised(self):
        """Test SearchError can be raised and caught."""
        with pytest.raises(SearchError):
            raise SearchError("Test error")

    def test_search_error_with_cause(self):
        """Test SearchError with underlying cause."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise SearchError("Search failed") from e
        except SearchError as error:
            assert str(error) == "Search failed"
            assert isinstance(error.__cause__, ValueError)
