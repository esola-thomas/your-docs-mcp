"""Unit tests for hierarchical navigation and category tree building."""

import pytest
from pathlib import Path
from datetime import datetime

from hierarchical_docs_mcp.services.hierarchy import (
    build_category_tree,
    get_breadcrumbs,
    navigate_to_uri,
    get_table_of_contents,
    _count_documents_recursive,
    _get_root_context,
    _get_category_context,
    _get_document_context,
    _build_toc_node,
    HierarchyError,
)
from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.models.navigation import Category, NavigationContext


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    base_time = datetime.utcnow()

    return [
        Document(
            file_path=Path("/docs/guides/getting-started.md"),
            relative_path=Path("guides/getting-started.md"),
            uri="docs://guides/getting-started",
            title="Getting Started",
            content="# Getting Started\n\nIntroduction",
            tags=["tutorial", "beginner"],
            category="guides",
            order=1,
            last_modified=base_time,
            size_bytes=100,
        ),
        Document(
            file_path=Path("/docs/guides/advanced/performance.md"),
            relative_path=Path("guides/advanced/performance.md"),
            uri="docs://guides/advanced/performance",
            title="Performance Guide",
            content="# Performance\n\nAdvanced tips",
            tags=["advanced", "optimization"],
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
            content="# Auth API\n\nAPI details",
            tags=["api", "security"],
            category="api",
            order=1,
            last_modified=base_time,
            size_bytes=150,
        ),
        Document(
            file_path=Path("/docs/readme.md"),
            relative_path=Path("readme.md"),
            uri="docs://readme",
            title="README",
            content="# README\n\nProject docs",
            tags=[],
            category=None,
            order=0,
            last_modified=base_time,
            size_bytes=50,
        ),
    ]


class TestBuildCategoryTree:
    """Test category tree building from documents."""

    def test_build_tree_from_documents(self, sample_documents):
        """Test building category tree from sample documents."""
        categories = build_category_tree(sample_documents)

        # Should have categories for: guides, guides/advanced, api
        assert "docs://guides" in categories
        assert "docs://guides/advanced" in categories
        assert "docs://api" in categories

    def test_category_hierarchy(self, sample_documents):
        """Test that parent-child relationships are correct."""
        categories = build_category_tree(sample_documents)

        guides = categories["docs://guides"]
        advanced = categories["docs://guides/advanced"]

        assert advanced.parent_uri == "docs://guides"
        assert "docs://guides/advanced" in guides.child_categories

    def test_category_depth(self, sample_documents):
        """Test that category depths are calculated correctly."""
        categories = build_category_tree(sample_documents)

        assert categories["docs://guides"].depth == 0
        assert categories["docs://guides/advanced"].depth == 1
        assert categories["docs://api"].depth == 0

    def test_category_labels(self, sample_documents):
        """Test that category labels are human-readable."""
        categories = build_category_tree(sample_documents)

        guides = categories["docs://guides"]
        assert guides.label == "Guides"

        advanced = categories["docs://guides/advanced"]
        assert advanced.label == "Advanced"

    def test_document_assignment_to_categories(self, sample_documents):
        """Test that documents are assigned to correct categories."""
        categories = build_category_tree(sample_documents)

        guides = categories["docs://guides"]
        assert "docs://guides/getting-started" in guides.child_documents

        advanced = categories["docs://guides/advanced"]
        assert "docs://guides/advanced/performance" in advanced.child_documents

    def test_document_count_calculation(self, sample_documents):
        """Test that document counts include descendants."""
        categories = build_category_tree(sample_documents)

        guides = categories["docs://guides"]
        # Should count getting-started.md + performance.md (in advanced)
        assert guides.document_count == 2

        api = categories["docs://api"]
        # Should count authentication.md
        assert api.document_count == 1

    def test_empty_document_list(self):
        """Test building tree from empty document list."""
        categories = build_category_tree([])

        assert len(categories) == 0

    def test_root_level_documents_no_category(self, sample_documents):
        """Test that root-level documents don't create categories."""
        categories = build_category_tree(sample_documents)

        # readme.md is at root, should not create a category for it
        # Only guides and api should have categories
        assert "docs://readme" not in categories

    def test_multiple_documents_same_category(self):
        """Test multiple documents in the same category."""
        docs = [
            Document(
                file_path=Path("/docs/guides/doc1.md"),
                relative_path=Path("guides/doc1.md"),
                uri="docs://guides/doc1",
                title="Doc 1",
                content="Content 1",
                last_modified=datetime.utcnow(),
                size_bytes=100,
            ),
            Document(
                file_path=Path("/docs/guides/doc2.md"),
                relative_path=Path("guides/doc2.md"),
                uri="docs://guides/doc2",
                title="Doc 2",
                content="Content 2",
                last_modified=datetime.utcnow(),
                size_bytes=100,
            ),
        ]

        categories = build_category_tree(docs)

        guides = categories["docs://guides"]
        assert len(guides.child_documents) == 2
        assert guides.document_count == 2

    def test_deeply_nested_categories(self):
        """Test deeply nested category structure."""
        docs = [
            Document(
                file_path=Path("/docs/a/b/c/d/doc.md"),
                relative_path=Path("a/b/c/d/doc.md"),
                uri="docs://a/b/c/d/doc",
                title="Deep Doc",
                content="Content",
                last_modified=datetime.utcnow(),
                size_bytes=100,
            ),
        ]

        categories = build_category_tree(docs)

        # Should create categories for a, a/b, a/b/c, a/b/c/d
        assert "docs://a" in categories
        assert "docs://a/b" in categories
        assert "docs://a/b/c" in categories
        assert "docs://a/b/c/d" in categories

        # Check depths
        assert categories["docs://a"].depth == 0
        assert categories["docs://a/b"].depth == 1
        assert categories["docs://a/b/c"].depth == 2
        assert categories["docs://a/b/c/d"].depth == 3


class TestGetBreadcrumbs:
    """Test breadcrumb generation."""

    def test_breadcrumbs_for_nested_uri(self):
        """Test breadcrumbs for nested URI."""
        uri = "docs://guides/security/authentication"
        breadcrumbs = get_breadcrumbs(uri)

        assert len(breadcrumbs) == 3
        assert breadcrumbs[0]["name"] == "Guides"
        assert breadcrumbs[0]["uri"] == "docs://guides"
        assert breadcrumbs[1]["name"] == "Security"
        assert breadcrumbs[1]["uri"] == "docs://guides/security"
        assert breadcrumbs[2]["name"] == "Authentication"
        assert breadcrumbs[2]["uri"] == "docs://guides/security/authentication"

    def test_breadcrumbs_for_root_level(self):
        """Test breadcrumbs for root level URI."""
        uri = "docs://guides"
        breadcrumbs = get_breadcrumbs(uri)

        assert len(breadcrumbs) == 1
        assert breadcrumbs[0]["name"] == "Guides"
        assert breadcrumbs[0]["uri"] == "docs://guides"

    def test_breadcrumbs_for_empty_path(self):
        """Test breadcrumbs for empty path."""
        uri = "docs://"
        breadcrumbs = get_breadcrumbs(uri)

        assert len(breadcrumbs) == 0

    def test_breadcrumbs_for_api_uri(self):
        """Test breadcrumbs for api:// URIs."""
        uri = "api://users/create"
        breadcrumbs = get_breadcrumbs(uri)

        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["uri"] == "api://users"
        assert breadcrumbs[1]["uri"] == "api://users/create"

    def test_breadcrumbs_invalid_scheme(self):
        """Test breadcrumbs for invalid URI scheme."""
        uri = "http://example.com/docs"
        breadcrumbs = get_breadcrumbs(uri)

        assert len(breadcrumbs) == 0

    def test_breadcrumbs_title_case(self):
        """Test that breadcrumb names are title-cased."""
        uri = "docs://getting-started/first-steps"
        breadcrumbs = get_breadcrumbs(uri)

        assert breadcrumbs[0]["name"] == "Getting Started"
        assert breadcrumbs[1]["name"] == "First Steps"


class TestNavigateToUri:
    """Test URI navigation."""

    def test_navigate_to_root(self, sample_documents):
        """Test navigating to root URI."""
        categories = build_category_tree(sample_documents)
        context = navigate_to_uri("docs://", sample_documents, categories)

        assert context.current_type == "root"
        assert context.current_uri == "docs://"
        assert len(context.children) > 0
        assert context.parent_uri is None

    def test_navigate_to_category(self, sample_documents):
        """Test navigating to a category."""
        categories = build_category_tree(sample_documents)
        context = navigate_to_uri("docs://guides", sample_documents, categories)

        assert context.current_type == "category"
        assert context.current_uri == "docs://guides"
        assert context.parent_uri == "docs://"
        assert len(context.children) > 0

    def test_navigate_to_document(self, sample_documents):
        """Test navigating to a document."""
        categories = build_category_tree(sample_documents)
        context = navigate_to_uri(
            "docs://guides/getting-started", sample_documents, categories
        )

        assert context.current_type == "document"
        assert context.current_uri == "docs://guides/getting-started"
        assert context.parent_uri is not None
        assert len(context.children) == 0

    def test_navigate_to_invalid_uri(self, sample_documents):
        """Test navigating to invalid URI raises error."""
        categories = build_category_tree(sample_documents)

        with pytest.raises(HierarchyError, match="URI not found"):
            navigate_to_uri("docs://nonexistent", sample_documents, categories)

    def test_navigate_to_nested_category(self, sample_documents):
        """Test navigating to nested category."""
        categories = build_category_tree(sample_documents)
        context = navigate_to_uri("docs://guides/advanced", sample_documents, categories)

        assert context.current_type == "category"
        assert context.current_uri == "docs://guides/advanced"
        assert context.parent_uri == "docs://guides"

    def test_navigation_options_at_root(self, sample_documents):
        """Test navigation options at root."""
        categories = build_category_tree(sample_documents)
        context = navigate_to_uri("docs://", sample_documents, categories)

        assert "down" in context.navigation_options
        assert "up" not in context.navigation_options

    def test_navigation_options_at_category(self, sample_documents):
        """Test navigation options at category."""
        categories = build_category_tree(sample_documents)
        context = navigate_to_uri("docs://guides", sample_documents, categories)

        assert "down" in context.navigation_options
        assert "up" in context.navigation_options

    def test_navigation_options_at_document(self, sample_documents):
        """Test navigation options at document."""
        categories = build_category_tree(sample_documents)
        context = navigate_to_uri(
            "docs://guides/getting-started", sample_documents, categories
        )

        assert "up" in context.navigation_options
        assert "down" not in context.navigation_options


class TestGetTableOfContents:
    """Test table of contents generation."""

    def test_toc_generation(self, sample_documents):
        """Test basic TOC generation."""
        categories = build_category_tree(sample_documents)
        toc = get_table_of_contents(categories, sample_documents)

        assert toc["type"] == "root"
        assert toc["uri"] == "docs://"
        assert len(toc["children"]) > 0

    def test_toc_includes_categories(self, sample_documents):
        """Test that TOC includes categories."""
        categories = build_category_tree(sample_documents)
        toc = get_table_of_contents(categories, sample_documents)

        # Find guides category in children
        guides_child = next(
            (c for c in toc["children"] if c["uri"] == "docs://guides"), None
        )

        assert guides_child is not None
        assert guides_child["type"] == "category"
        assert guides_child["name"] == "Guides"

    def test_toc_includes_nested_structure(self, sample_documents):
        """Test that TOC includes nested categories."""
        categories = build_category_tree(sample_documents)
        toc = get_table_of_contents(categories, sample_documents)

        # Find guides category
        guides = next(
            (c for c in toc["children"] if c["uri"] == "docs://guides"), None
        )

        assert guides is not None
        # Should have advanced as child category
        advanced = next(
            (c for c in guides["children"] if c["uri"] == "docs://guides/advanced"),
            None,
        )
        assert advanced is not None

    def test_toc_includes_documents(self, sample_documents):
        """Test that TOC includes documents."""
        categories = build_category_tree(sample_documents)
        toc = get_table_of_contents(categories, sample_documents)

        guides = next(
            (c for c in toc["children"] if c["uri"] == "docs://guides"), None
        )

        # Should have getting-started document
        doc = next(
            (
                c
                for c in guides["children"]
                if c["uri"] == "docs://guides/getting-started"
            ),
            None,
        )
        assert doc is not None
        assert doc["type"] == "document"
        assert doc["name"] == "Getting Started"

    def test_toc_with_max_depth(self, sample_documents):
        """Test TOC generation with max depth limit."""
        categories = build_category_tree(sample_documents)
        toc = get_table_of_contents(categories, sample_documents, max_depth=1)

        # Should only include root level categories, not nested
        guides = next(
            (c for c in toc["children"] if c["uri"] == "docs://guides"), None
        )

        if guides:
            # Should not have nested children at depth 1
            assert len(guides["children"]) == 0

    def test_toc_caching(self, sample_documents):
        """Test that TOC results are cached."""
        categories = build_category_tree(sample_documents)

        # Generate twice
        toc1 = get_table_of_contents(categories, sample_documents)
        toc2 = get_table_of_contents(categories, sample_documents)

        # Results should be identical
        assert toc1["uri"] == toc2["uri"]
        assert len(toc1["children"]) == len(toc2["children"])


class TestCountDocumentsRecursive:
    """Test recursive document counting."""

    def test_count_leaf_category(self):
        """Test counting documents in leaf category."""
        category = Category(
            name="leaf",
            label="Leaf",
            uri="docs://leaf",
            depth=0,
            child_documents=["doc1", "doc2", "doc3"],
            source_category="docs",
        )

        categories = {category.uri: category}

        count = _count_documents_recursive(category, categories)
        assert count == 3

    def test_count_parent_category(self):
        """Test counting documents including nested categories."""
        parent = Category(
            name="parent",
            label="Parent",
            uri="docs://parent",
            depth=0,
            child_documents=["doc1"],
            child_categories=["docs://parent/child"],
            source_category="docs",
        )

        child = Category(
            name="child",
            label="Child",
            uri="docs://parent/child",
            parent_uri="docs://parent",
            depth=1,
            child_documents=["doc2", "doc3"],
            source_category="docs",
        )

        categories = {parent.uri: parent, child.uri: child}

        count = _count_documents_recursive(parent, categories)
        # Should count: doc1 + doc2 + doc3 = 3
        assert count == 3

    def test_count_empty_category(self):
        """Test counting in category with no documents."""
        category = Category(
            name="empty",
            label="Empty",
            uri="docs://empty",
            depth=0,
            source_category="docs",
        )

        categories = {category.uri: category}

        count = _count_documents_recursive(category, categories)
        assert count == 0


class TestGetRootContext:
    """Test root context generation."""

    def test_root_context_creation(self, sample_documents):
        """Test creating root context."""
        categories = build_category_tree(sample_documents)
        context = _get_root_context(categories)

        assert context.current_uri == "docs://"
        assert context.current_type == "root"
        assert context.parent_uri is None
        assert len(context.breadcrumbs) == 0

    def test_root_context_includes_root_categories(self, sample_documents):
        """Test that root context includes root-level categories."""
        categories = build_category_tree(sample_documents)
        context = _get_root_context(categories)

        # Should have guides and api
        category_uris = [c["uri"] for c in context.children]
        assert "docs://guides" in category_uris
        assert "docs://api" in category_uris


class TestGetCategoryContext:
    """Test category context generation."""

    def test_category_context_creation(self, sample_documents):
        """Test creating category context."""
        categories = build_category_tree(sample_documents)
        context = _get_category_context("docs://guides", categories)

        assert context.current_uri == "docs://guides"
        assert context.current_type == "category"

    def test_category_context_children(self, sample_documents):
        """Test that category context includes children."""
        categories = build_category_tree(sample_documents)
        context = _get_category_context("docs://guides", categories)

        # Should have both child categories and documents
        assert len(context.children) > 0

        # Check for advanced category
        child_uris = [c["uri"] for c in context.children]
        assert "docs://guides/advanced" in child_uris
        assert "docs://guides/getting-started" in child_uris


class TestGetDocumentContext:
    """Test document context generation."""

    def test_document_context_creation(self, sample_documents):
        """Test creating document context."""
        categories = build_category_tree(sample_documents)
        doc = sample_documents[0]  # getting-started

        context = _get_document_context(doc, categories)

        assert context.current_uri == doc.uri
        assert context.current_type == "document"
        assert len(context.children) == 0

    def test_document_context_parent(self, sample_documents):
        """Test that document context has correct parent."""
        categories = build_category_tree(sample_documents)
        doc = sample_documents[0]  # guides/getting-started

        context = _get_document_context(doc, categories)

        assert context.parent_uri == "docs://guides"


class TestHierarchyEdgeCases:
    """Test edge cases in hierarchy operations."""

    def test_single_document_at_root(self):
        """Test hierarchy with single root-level document."""
        doc = Document(
            file_path=Path("/docs/readme.md"),
            relative_path=Path("readme.md"),
            uri="docs://readme",
            title="README",
            content="Content",
            last_modified=datetime.utcnow(),
            size_bytes=100,
        )

        categories = build_category_tree([doc])

        # Should have no categories (document is at root)
        assert len(categories) == 0

    def test_documents_with_special_characters_in_path(self):
        """Test handling paths with special characters."""
        doc = Document(
            file_path=Path("/docs/guides/test-doc_name.md"),
            relative_path=Path("guides/test-doc_name.md"),
            uri="docs://guides/test-doc_name",
            title="Test Doc",
            content="Content",
            last_modified=datetime.utcnow(),
            size_bytes=100,
        )

        categories = build_category_tree([doc])

        assert "docs://guides" in categories

    def test_empty_uri_navigation(self, sample_documents):
        """Test navigation with empty URI alias."""
        categories = build_category_tree(sample_documents)

        # Should handle "docs" and "" as root
        context1 = navigate_to_uri("docs", sample_documents, categories)
        context2 = navigate_to_uri("", sample_documents, categories)

        assert context1.current_type == "root"
        assert context2.current_type == "root"

    def test_category_breadcrumbs_property(self, sample_documents):
        """Test Category breadcrumbs property."""
        categories = build_category_tree(sample_documents)

        advanced = categories["docs://guides/advanced"]
        breadcrumbs = advanced.breadcrumbs

        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["name"] == "guides"
        assert breadcrumbs[1]["name"] == "advanced"

    def test_category_is_root_property(self, sample_documents):
        """Test Category is_root property."""
        categories = build_category_tree(sample_documents)

        guides = categories["docs://guides"]
        advanced = categories["docs://guides/advanced"]

        assert guides.is_root is True
        assert advanced.is_root is False
