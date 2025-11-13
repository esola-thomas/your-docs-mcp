"""Unit tests for MCP resource handlers."""

from datetime import UTC, datetime

import pytest

from hierarchical_docs_mcp.handlers.resources import (
    handle_resource_read,
    list_resources,
)
from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.models.navigation import Category


class TestHandleResourceRead:
    """Test handle_resource_read function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="# Getting Started\n\nWelcome to the guide.",
                category="guides",
                tags=["tutorial"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            ),
            Document(
                uri="docs://api/authentication",
                title="Authentication API",
                content="# Authentication\n\nAPI documentation.",
                category="api",
                tags=["security"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
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
                child_documents=["docs://guides/getting-started"],
                source_category="guides",
                child_categories=[],
                document_count=1,
            ),
            "docs://api": Category(
                name="api",
                uri="docs://api",
                depth=1,
                label="API",
                child_documents=["docs://api/authentication"],
                source_category="api",
                child_categories=[],
                document_count=1,
            ),
            "docs://": Category(
                name="root",
                uri="docs://",
                depth=0,
                label="Root",
                child_documents=[],
                source_category="root",
                child_categories=["docs://guides", "docs://api"],
                document_count=2,
            ),
        }

    @pytest.mark.asyncio
    async def test_read_document_resource(self, sample_documents, sample_categories):
        """Test reading a document resource."""
        result = await handle_resource_read(
            "docs://guides/getting-started", sample_documents, sample_categories
        )

        assert "uri" in result
        assert result["uri"] == "docs://guides/getting-started"
        assert result["mimeType"] == "text/markdown"
        assert "text" in result
        assert result["text"] == "# Getting Started\n\nWelcome to the guide."
        assert "metadata" in result
        assert result["metadata"]["title"] == "Getting Started"
        assert result["metadata"]["tags"] == ["tutorial"]
        assert result["metadata"]["category"] == "guides"

    @pytest.mark.asyncio
    async def test_read_document_includes_last_modified(self, sample_documents, sample_categories):
        """Test reading document includes last_modified timestamp."""
        result = await handle_resource_read(
            "docs://guides/getting-started", sample_documents, sample_categories
        )

        assert "last_modified" in result["metadata"]
        assert result["metadata"]["last_modified"] == "2024-01-01T12:00:00+00:00"

    @pytest.mark.asyncio
    async def test_read_category_resource(self, sample_documents, sample_categories):
        """Test reading a category resource."""
        result = await handle_resource_read("docs://guides", sample_documents, sample_categories)

        assert "uri" in result
        assert result["uri"] == "docs://guides"
        assert result["mimeType"] == "text/markdown"
        assert "text" in result
        assert "Guides" in result["text"]
        assert "metadata" in result
        assert result["metadata"]["type"] == "category"
        assert result["metadata"]["name"] == "Guides"
        assert result["metadata"]["document_count"] == 1

    @pytest.mark.asyncio
    async def test_read_category_with_subcategories(self, sample_documents, sample_categories):
        """Test reading a category with subcategories."""
        result = await handle_resource_read("docs://", sample_documents, sample_categories)

        assert result["uri"] == "docs://"
        text = result["text"]
        assert "Subcategories" in text
        assert "Guides" in text
        assert "API" in text

    @pytest.mark.asyncio
    async def test_read_category_with_documents(self, sample_documents, sample_categories):
        """Test reading a category with child documents."""
        result = await handle_resource_read("docs://guides", sample_documents, sample_categories)

        text = result["text"]
        assert "Documents" in text
        assert "Getting Started" in text
        assert "docs://guides/getting-started" in text

    @pytest.mark.asyncio
    async def test_read_nonexistent_resource(self, sample_documents, sample_categories):
        """Test reading a non-existent resource."""
        result = await handle_resource_read(
            "docs://nonexistent", sample_documents, sample_categories
        )

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_resource_with_exception(self, sample_documents):
        """Test handling exception during resource read."""
        # Pass invalid categories to trigger exception
        result = await handle_resource_read("docs://test", sample_documents, None)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_read_document_with_multiple_tags(self):
        """Test reading document with multiple tags."""
        documents = [
            Document(
                uri="docs://test",
                title="Test Doc",
                content="Content",
                category="test",
                tags=["tag1", "tag2", "tag3"],
                file_path="/test.md",
                relative_path="test.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),
            )
        ]

        result = await handle_resource_read("docs://test", documents, {})

        assert result["metadata"]["tags"] == ["tag1", "tag2", "tag3"]

    @pytest.mark.asyncio
    async def test_read_category_content_format(self, sample_documents, sample_categories):
        """Test category content is formatted correctly."""
        result = await handle_resource_read("docs://guides", sample_documents, sample_categories)

        text = result["text"]
        # Check markdown formatting
        assert text.startswith("# Guides")
        assert "**Documents**: 1" in text

    @pytest.mark.asyncio
    async def test_read_category_with_both_subcategories_and_documents(self, sample_documents):
        """Test reading category with both subcategories and documents."""
        categories = {
            "docs://parent": Category(
                name="parent",
                uri="docs://parent",
                depth=1,
                label="Parent",
                source_category="parent",
                child_categories=["docs://parent/child"],
                child_documents=["docs://parent/doc"],
                document_count=2,
            ),
            "docs://parent/child": Category(
                name="parent/child",
                uri="docs://parent/child",
                depth=2,
                label="Child",
                source_category="parent/child",
                child_categories=[],
                child_documents=[],
                document_count=0,
            ),
        }

        documents = [
            Document(
                uri="docs://parent/doc",
                title="Parent Doc",
                content="Content",
                category="parent",
                tags=[],
                file_path="/parent/doc.md",
                relative_path="parent/doc.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),
            )
        ]

        result = await handle_resource_read("docs://parent", documents, categories)

        text = result["text"]
        assert "Subcategories" in text
        assert "Child" in text
        assert "Documents" in text
        assert "Parent Doc" in text

    @pytest.mark.asyncio
    async def test_read_empty_category(self):
        """Test reading an empty category."""
        categories = {
            "docs://empty": Category(
                name="empty",
                uri="docs://empty",
                depth=1,
                label="Empty",
                source_category="empty",
                child_categories=[],
                child_documents=[],
                document_count=0,
            )
        }

        result = await handle_resource_read("docs://empty", [], categories)

        assert result["uri"] == "docs://empty"
        assert result["metadata"]["document_count"] == 0


class TestListResources:
    """Test list_resources function."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                uri="docs://guides/getting-started",
                title="Getting Started",
                content="This is an introduction guide for new users.",
                category="guides",
                tags=["tutorial"],
                file_path="/docs/guides/getting-started.md",
                relative_path="docs/guides/getting-started.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),
            ),
            Document(
                uri="docs://api/authentication",
                title="Authentication",
                content="API authentication documentation.",
                category="api",
                tags=["security"],
                file_path="/docs/api/authentication.md",
                relative_path="docs/api/authentication.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),
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
            ),
            "docs://api": Category(
                name="api",
                uri="docs://api",
                depth=1,
                label="API",
                child_documents=[],
                source_category="api",
                child_categories=[],
                document_count=1,
            ),
        }

    @pytest.mark.asyncio
    async def test_list_resources_includes_root(self, sample_documents, sample_categories):
        """Test list_resources includes root resource."""
        resources = await list_resources(sample_documents, sample_categories)

        assert len(resources) > 0
        root_resource = resources[0]
        assert root_resource["uri"] == "docs://"
        assert root_resource["name"] == "Documentation Root"
        assert root_resource["mimeType"] == "text/markdown"
        assert "description" in root_resource

    @pytest.mark.asyncio
    async def test_list_resources_includes_categories(self, sample_documents, sample_categories):
        """Test list_resources includes all categories."""
        resources = await list_resources(sample_documents, sample_categories)

        category_uris = [
            r["uri"] for r in resources if r["uri"].startswith("docs://") and r["uri"] != "docs://"
        ]
        assert "docs://guides" in category_uris
        assert "docs://api" in category_uris

    @pytest.mark.asyncio
    async def test_list_resources_includes_documents(self, sample_documents, sample_categories):
        """Test list_resources includes all documents."""
        resources = await list_resources(sample_documents, sample_categories)

        doc_uris = [r["uri"] for r in resources]
        assert "docs://guides/getting-started" in doc_uris
        assert "docs://api/authentication" in doc_uris

    @pytest.mark.asyncio
    async def test_list_resources_document_format(self, sample_documents, sample_categories):
        """Test document resources have correct format."""
        resources = await list_resources(sample_documents, sample_categories)

        doc_resources = [r for r in resources if "getting-started" in r["uri"]]
        assert len(doc_resources) == 1

        doc_resource = doc_resources[0]
        assert doc_resource["name"] == "Getting Started"
        assert doc_resource["mimeType"] == "text/markdown"
        assert "description" in doc_resource
        assert len(doc_resource["description"]) <= 100  # Excerpt limit

    @pytest.mark.asyncio
    async def test_list_resources_category_format(self, sample_categories):
        """Test category resources have correct format."""
        resources = await list_resources([], sample_categories)

        category_resources = [r for r in resources if r["uri"] == "docs://guides"]
        assert len(category_resources) == 1

        cat_resource = category_resources[0]
        assert cat_resource["name"] == "Guides"
        assert cat_resource["mimeType"] == "text/markdown"
        assert "1 documents" in cat_resource["description"]

    @pytest.mark.asyncio
    async def test_list_resources_empty_collections(self):
        """Test list_resources with empty documents and categories."""
        resources = await list_resources([], {})

        # Should still include root
        assert len(resources) == 1
        assert resources[0]["uri"] == "docs://"

    @pytest.mark.asyncio
    async def test_list_resources_count(self, sample_documents, sample_categories):
        """Test list_resources returns correct count."""
        resources = await list_resources(sample_documents, sample_categories)

        # 1 root + 2 categories + 2 documents = 5 resources
        assert len(resources) == 5

    @pytest.mark.asyncio
    async def test_list_resources_all_have_required_fields(
        self, sample_documents, sample_categories
    ):
        """Test all resources have required fields."""
        resources = await list_resources(sample_documents, sample_categories)

        for resource in resources:
            assert "uri" in resource
            assert "name" in resource
            assert "mimeType" in resource
            assert "description" in resource

    @pytest.mark.asyncio
    async def test_list_resources_document_excerpt(self, sample_documents, sample_categories):
        """Test document description uses excerpt."""
        resources = await list_resources(sample_documents, sample_categories)

        doc_resources = [r for r in resources if r["uri"] == "docs://guides/getting-started"]
        assert len(doc_resources) == 1

        # Should contain excerpt of content
        description = doc_resources[0]["description"]
        assert len(description) > 0
        assert "introduction guide" in description.lower()

    @pytest.mark.asyncio
    async def test_list_resources_category_document_count(self):
        """Test category description includes document count."""
        categories = {
            "docs://test": Category(
                name="test",
                uri="docs://test",
                depth=1,
                label="Test",
                child_documents=[],
                source_category="test",
                child_categories=[],
                document_count=5,
            )
        }

        resources = await list_resources([], categories)

        test_resources = [r for r in resources if r["uri"] == "docs://test"]
        assert len(test_resources) == 1
        assert "5 documents" in test_resources[0]["description"]

    @pytest.mark.asyncio
    async def test_list_resources_multiple_documents_same_category(self):
        """Test list_resources with multiple documents in same category."""
        documents = [
            Document(
                uri=f"docs://test/doc{i}",
                title=f"Document {i}",
                content=f"Content {i}",
                category="test",
                tags=[],
                file_path=f"/test/doc{i}.md",
                relative_path=f"test/doc{i}.md",
                size_bytes=100,
                last_modified=datetime.now(UTC),
            )
            for i in range(3)
        ]

        categories = {
            "docs://test": Category(
                name="test",
                uri="docs://test",
                depth=1,
                label="Test",
                child_documents=[d.uri for d in documents],
                source_category="test",
                child_categories=[],
                document_count=3,
            )
        }

        resources = await list_resources(documents, categories)

        # 1 root + 1 category + 3 documents = 5 resources
        assert len(resources) == 5
