"""Unit tests for Document model."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from docs_mcp.models.document import Document


class TestDocumentModel:
    """Test Document model properties and methods."""

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            file_path=Path("/docs/test.md"),
            relative_path=Path("test.md"),
            title="Test Document",
            content="# Test\n\nThis is a test document.\n\nSecond paragraph here.",
            uri="docs://test",
            category="test",
            tags=["test", "sample"],
            frontmatter={"author": "Test"},
            last_modified=datetime.now(UTC),
            size_bytes=100,
            parent=None,
        )

    @pytest.fixture
    def document_with_frontmatter(self):
        """Create a document with frontmatter."""
        return Document(
            file_path=Path("/docs/frontmatter.md"),
            relative_path=Path("frontmatter.md"),
            title="Document with Frontmatter",
            content="---\nauthor: Test\ntags: [test]\n---\n\n# Header\n\nFirst paragraph.\n\nSecond paragraph.",
            uri="docs://frontmatter",
            category="test",
            tags=["test"],
            frontmatter={},
            last_modified=datetime.now(UTC),
            size_bytes=150,
            parent=None,
        )

    @pytest.fixture
    def document_with_long_content(self):
        """Create a document with long content."""
        long_content = "This is a very long paragraph that exceeds the default max_length. " * 10
        return Document(
            file_path=Path("/docs/long.md"),
            relative_path=Path("long.md"),
            title="Long Document",
            content=long_content,
            uri="docs://long",
            category="test",
            tags=[],
            frontmatter={},
            last_modified=datetime.now(UTC),
            size_bytes=len(long_content),
            parent=None,
        )

    def test_excerpt_returns_first_paragraph(self, sample_document):
        """Test excerpt returns the first paragraph."""
        excerpt = sample_document.excerpt()
        assert excerpt == "# Test"
        assert "Second paragraph" not in excerpt

    def test_excerpt_strips_frontmatter(self, document_with_frontmatter):
        """Test excerpt removes frontmatter delimiter."""
        excerpt = document_with_frontmatter.excerpt()
        assert "---" not in excerpt
        assert excerpt.startswith("# Header")

    def test_excerpt_truncates_long_content(self, document_with_long_content):
        """Test excerpt truncates content longer than max_length."""
        excerpt = document_with_long_content.excerpt(max_length=100)
        assert len(excerpt) <= 104  # max_length + "..."
        assert excerpt.endswith("...")

    def test_excerpt_no_paragraphs_returns_content(self):
        """Test excerpt with no paragraph breaks returns full content."""
        doc = Document(
            file_path=Path("/docs/no-para.md"),
            relative_path=Path("no-para.md"),
            title="No Paragraphs",
            content="Single line content",
            uri="docs://no-para",
            category="test",
            tags=[],
            frontmatter={},
            last_modified=datetime.now(UTC),
            size_bytes=19,
            parent=None,
        )
        excerpt = doc.excerpt()
        assert excerpt == "Single line content"

    def test_excerpt_empty_content(self):
        """Test excerpt with empty content."""
        doc = Document(
            file_path=Path("/docs/empty.md"),
            relative_path=Path("empty.md"),
            title="Empty",
            content="",
            uri="docs://empty",
            category="test",
            tags=[],
            frontmatter={},
            last_modified=datetime.now(UTC),
            size_bytes=0,
            parent=None,
        )
        excerpt = doc.excerpt()
        assert excerpt == ""

    def test_excerpt_custom_max_length(self, sample_document):
        """Test excerpt with custom max_length."""
        excerpt = sample_document.excerpt(max_length=10)
        assert len(excerpt) <= 14  # Allow for "..." and word boundary
        assert "..." in excerpt or len(excerpt) <= 10

    def test_breadcrumbs_property(self):
        """Test breadcrumbs property returns path components."""
        doc = Document(
            file_path=Path("/docs/guides/getting-started.md"),
            relative_path=Path("guides/getting-started.md"),
            title="Getting Started",
            content="# Getting Started",
            uri="docs://guides/getting-started",
            category="guides",
            tags=[],
            frontmatter={},
            last_modified=datetime.now(UTC),
            size_bytes=17,
            parent=None,
        )
        # Breadcrumbs should be path components excluding the filename
        assert doc.breadcrumbs == ["guides"]

    def test_breadcrumbs_nested_path(self):
        """Test breadcrumbs with nested directory structure."""
        doc = Document(
            file_path=Path("/docs/api/v1/endpoints/users.md"),
            relative_path=Path("api/v1/endpoints/users.md"),
            title="Users Endpoint",
            content="# Users",
            uri="docs://api/v1/endpoints/users",
            category="api",
            tags=[],
            frontmatter={},
            last_modified=datetime.now(UTC),
            size_bytes=7,
            parent=None,
        )
        assert doc.breadcrumbs == ["api", "v1", "endpoints"]

    def test_breadcrumbs_root_level(self):
        """Test breadcrumbs for root-level document."""
        doc = Document(
            file_path=Path("/docs/readme.md"),
            relative_path=Path("readme.md"),
            title="README",
            content="# README",
            uri="docs://readme",
            category=None,
            tags=[],
            frontmatter={},
            last_modified=datetime.now(UTC),
            size_bytes=8,
            parent=None,
        )
        assert doc.breadcrumbs == []
