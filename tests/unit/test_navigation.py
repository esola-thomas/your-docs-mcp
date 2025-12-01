"""Unit tests for Navigation models."""

import pytest

from docs_mcp.models.navigation import Category, NavigationContext


class TestCategoryModel:
    """Test Category model properties and methods."""

    @pytest.fixture
    def root_category(self):
        """Create a root category."""
        return Category(
            name="root",
            label="Root",
            uri="docs://",
            parent_uri=None,
            depth=0,
            child_categories=["docs://guides", "docs://api"],
            child_documents=[],
            document_count=5,
            source_category="root",
        )

    @pytest.fixture
    def nested_category(self):
        """Create a nested category."""
        return Category(
            name="security",
            label="Security",
            uri="docs://guides/security",
            parent_uri="docs://guides",
            depth=2,
            child_categories=[],
            child_documents=["docs://guides/security/authentication"],
            document_count=3,
            source_category="guides",
        )

    def test_breadcrumbs_root_returns_empty(self, root_category):
        """Test breadcrumbs for root category returns empty list."""
        breadcrumbs = root_category.breadcrumbs
        assert breadcrumbs == []

    def test_breadcrumbs_nested_category(self, nested_category):
        """Test breadcrumbs for nested category."""
        breadcrumbs = nested_category.breadcrumbs
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0] == {"name": "guides", "uri": "docs://guides"}
        assert breadcrumbs[1] == {"name": "security", "uri": "docs://guides/security"}

    def test_breadcrumbs_single_level(self):
        """Test breadcrumbs for single-level category."""
        cat = Category(
            name="guides",
            label="Guides",
            uri="docs://guides",
            parent_uri="docs://",
            depth=1,
            child_categories=[],
            child_documents=[],
            document_count=0,
            source_category="guides",
        )
        breadcrumbs = cat.breadcrumbs
        assert len(breadcrumbs) == 1
        assert breadcrumbs[0] == {"name": "guides", "uri": "docs://guides"}

    def test_breadcrumbs_invalid_uri_format(self):
        """Test breadcrumbs with non-docs URI."""
        cat = Category(
            name="invalid",
            label="Invalid",
            uri="http://invalid",
            parent_uri=None,
            depth=0,
            child_categories=[],
            child_documents=[],
            document_count=0,
            source_category="invalid",
        )
        breadcrumbs = cat.breadcrumbs
        assert breadcrumbs == []


class TestNavigationContextModel:
    """Test NavigationContext model properties."""

    @pytest.fixture
    def nav_context_with_parent(self):
        """Create navigation context with parent."""
        return NavigationContext(
            current_uri="docs://guides/security",
            current_title="Security Guide",
            current_type="category",
            parent_uri="docs://guides",
            parent_title="Guides",
            children=[
                {
                    "uri": "docs://guides/security/auth",
                    "title": "Authentication",
                    "type": "document",
                }
            ],
            breadcrumbs=[
                {"name": "guides", "uri": "docs://guides"},
                {"name": "security", "uri": "docs://guides/security"},
            ],
            navigation_options={},
        )

    @pytest.fixture
    def nav_context_no_parent(self):
        """Create navigation context without parent."""
        return NavigationContext(
            current_uri="docs://",
            current_title="Documentation Root",
            current_type="category",
            parent_uri=None,
            parent_title=None,
            children=[
                {"uri": "docs://guides", "title": "Guides", "type": "category"},
                {"uri": "docs://api", "title": "API Reference", "type": "category"},
            ],
            breadcrumbs=[],
            navigation_options={},
        )

    @pytest.fixture
    def nav_context_leaf(self):
        """Create navigation context for leaf node (no children)."""
        return NavigationContext(
            current_uri="docs://guides/quickstart",
            current_title="Quickstart",
            current_type="document",
            parent_uri="docs://guides",
            parent_title="Guides",
            children=[],
            breadcrumbs=[
                {"name": "guides", "uri": "docs://guides"},
                {"name": "quickstart", "uri": "docs://guides/quickstart"},
            ],
            navigation_options={},
        )

    def test_can_navigate_up_with_parent(self, nav_context_with_parent):
        """Test can_navigate_up returns True when parent exists."""
        assert nav_context_with_parent.can_navigate_up is True

    def test_can_navigate_up_without_parent(self, nav_context_no_parent):
        """Test can_navigate_up returns False when no parent."""
        assert nav_context_no_parent.can_navigate_up is False

    def test_can_navigate_down_with_children(self, nav_context_with_parent):
        """Test can_navigate_down returns True when children exist."""
        assert nav_context_with_parent.can_navigate_down is True

    def test_can_navigate_down_without_children(self, nav_context_leaf):
        """Test can_navigate_down returns False when no children."""
        assert nav_context_leaf.can_navigate_down is False

    def test_can_navigate_down_with_multiple_children(self, nav_context_no_parent):
        """Test can_navigate_down with multiple children."""
        assert nav_context_no_parent.can_navigate_down is True
        assert len(nav_context_no_parent.children) == 2
