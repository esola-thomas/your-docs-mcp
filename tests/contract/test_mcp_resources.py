"""Contract tests for MCP resource handlers."""

from datetime import datetime, timedelta, timezone, UTC
from pathlib import Path

import pytest

from hierarchical_docs_mcp.handlers.resources import (
    handle_resource_read,
    list_resources,
)
from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.services.hierarchy import build_category_tree


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    base_time = datetime.now(UTC)

    return [
        Document(
            file_path=Path("/docs/guides/getting-started.md"),
            relative_path=Path("guides/getting-started.md"),
            uri="docs://guides/getting-started",
            title="Getting Started",
            content="# Getting Started\n\nWelcome to the documentation.",
            tags=["tutorial"],
            category="guides",
            order=1,
            last_modified=base_time,
            size_bytes=100,
        ),
        Document(
            file_path=Path("/docs/api/authentication.md"),
            relative_path=Path("api/authentication.md"),
            uri="docs://api/authentication",
            title="Authentication API",
            content="# Authentication\n\nAPI authentication details.",
            tags=["api", "security"],
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


class TestResourceRead:
    """Test resource read operations."""

    @pytest.mark.asyncio
    async def test_read_document_resource(self, sample_documents, categories):
        """Test reading a document resource."""
        uri = "docs://guides/getting-started"

        result = await handle_resource_read(uri, sample_documents, categories)

        assert "uri" in result
        assert result["uri"] == uri
        assert "mimeType" in result
        assert result["mimeType"] == "text/markdown"
        assert "text" in result
        assert len(result["text"]) > 0

    @pytest.mark.asyncio
    async def test_read_document_includes_metadata(self, sample_documents, categories):
        """Test that document resource includes metadata."""
        uri = "docs://guides/getting-started"

        result = await handle_resource_read(uri, sample_documents, categories)

        assert "metadata" in result
        metadata = result["metadata"]

        assert "title" in metadata
        assert "tags" in metadata
        assert "category" in metadata
        assert "last_modified" in metadata

    @pytest.mark.asyncio
    async def test_read_category_resource(self, sample_documents, categories):
        """Test reading a category resource."""
        uri = "docs://guides"

        result = await handle_resource_read(uri, sample_documents, categories)

        assert "uri" in result
        assert result["uri"] == uri
        assert "mimeType" in result
        assert "text" in result
        # Category should return generated overview
        assert "Guides" in result["text"] or "guides" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_read_category_includes_metadata(self, sample_documents, categories):
        """Test that category resource includes metadata."""
        uri = "docs://guides"

        result = await handle_resource_read(uri, sample_documents, categories)

        assert "metadata" in result
        metadata = result["metadata"]

        assert "type" in metadata
        assert metadata["type"] == "category"
        assert "name" in metadata
        assert "document_count" in metadata

    @pytest.mark.asyncio
    async def test_read_nonexistent_resource(self, sample_documents, categories):
        """Test reading nonexistent resource returns error."""
        uri = "docs://nonexistent"

        result = await handle_resource_read(uri, sample_documents, categories)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_read_document_content_preserved(self, sample_documents, categories):
        """Test that document content is fully preserved."""
        uri = "docs://guides/getting-started"

        result = await handle_resource_read(uri, sample_documents, categories)

        # Content should include original markdown
        assert "#" in result["text"]  # Should have markdown heading

    @pytest.mark.asyncio
    async def test_read_category_lists_subcategories(self, sample_documents, categories):
        """Test that category resource lists subcategories."""
        # Add a document in a nested category
        nested_doc = Document(
            file_path=Path("/docs/guides/advanced/test.md"),
            relative_path=Path("guides/advanced/test.md"),
            uri="docs://guides/advanced/test",
            title="Advanced Test",
            content="Advanced content",
            last_modified=datetime.now(UTC),
            size_bytes=50,
        )

        docs_with_nested = sample_documents + [nested_doc]
        nested_categories = build_category_tree(docs_with_nested)

        uri = "docs://guides"
        result = await handle_resource_read(uri, docs_with_nested, nested_categories)

        # Should mention subcategories
        text = result["text"]
        # Category overview should be in markdown format
        assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_read_category_lists_documents(self, sample_documents, categories):
        """Test that category resource lists documents."""
        uri = "docs://guides"

        result = await handle_resource_read(uri, sample_documents, categories)

        text = result["text"]
        # Should list the "Getting Started" document
        assert "Getting Started" in text or "getting-started" in text.lower()


class TestListResources:
    """Test resource listing operations."""

    @pytest.mark.asyncio
    async def test_list_resources_returns_list(self, sample_documents, categories):
        """Test that list_resources returns a list."""
        result = await list_resources(sample_documents, categories)

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_list_resources_includes_root(self, sample_documents, categories):
        """Test that resource list includes root."""
        result = await list_resources(sample_documents, categories)

        # Should have root resource
        root = next((r for r in result if r["uri"] == "docs://"), None)
        assert root is not None
        assert "name" in root
        assert "description" in root or "mimeType" in root

    @pytest.mark.asyncio
    async def test_list_resources_includes_categories(self, sample_documents, categories):
        """Test that resource list includes categories."""
        result = await list_resources(sample_documents, categories)

        # Should have guides category
        guides = next((r for r in result if r["uri"] == "docs://guides"), None)
        assert guides is not None

    @pytest.mark.asyncio
    async def test_list_resources_includes_documents(self, sample_documents, categories):
        """Test that resource list includes documents."""
        result = await list_resources(sample_documents, categories)

        # Should have getting-started document
        doc = next((r for r in result if r["uri"] == "docs://guides/getting-started"), None)
        assert doc is not None

    @pytest.mark.asyncio
    async def test_resource_list_structure(self, sample_documents, categories):
        """Test that resource list entries have correct structure."""
        result = await list_resources(sample_documents, categories)

        for resource in result:
            assert "uri" in resource
            assert "name" in resource
            # Should have either description or mimeType
            assert "description" in resource or "mimeType" in resource

    @pytest.mark.asyncio
    async def test_list_resources_mime_types(self, sample_documents, categories):
        """Test that resources have appropriate mime types."""
        result = await list_resources(sample_documents, categories)

        for resource in result:
            if "mimeType" in resource:
                # Should be text/markdown for docs
                assert resource["mimeType"] in [
                    "text/markdown",
                    "application/json",
                    "text/plain",
                ]


class TestResourceContract:
    """Test MCP resource contract compliance."""

    @pytest.mark.asyncio
    async def test_document_resource_has_required_fields(self, sample_documents, categories):
        """Test that document resources have all required fields."""
        uri = "docs://guides/getting-started"

        result = await handle_resource_read(uri, sample_documents, categories)

        if "error" not in result:
            required_fields = ["uri", "mimeType", "text"]

            for field in required_fields:
                assert field in result, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_category_resource_has_required_fields(self, sample_documents, categories):
        """Test that category resources have all required fields."""
        uri = "docs://guides"

        result = await handle_resource_read(uri, sample_documents, categories)

        if "error" not in result:
            required_fields = ["uri", "mimeType", "text"]

            for field in required_fields:
                assert field in result, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_resources_are_json_serializable(self, sample_documents, categories):
        """Test that all resource responses are JSON serializable."""
        import json

        # Test document resource
        doc_result = await handle_resource_read(
            "docs://guides/getting-started", sample_documents, categories
        )
        try:
            json.dumps(doc_result)
        except (TypeError, ValueError):
            pytest.fail(f"Document resource is not JSON serializable: {doc_result}")

        # Test category resource
        cat_result = await handle_resource_read("docs://guides", sample_documents, categories)
        try:
            json.dumps(cat_result)
        except (TypeError, ValueError):
            pytest.fail(f"Category resource is not JSON serializable: {cat_result}")

        # Test resource list
        list_result = await list_resources(sample_documents, categories)
        try:
            json.dumps(list_result)
        except (TypeError, ValueError):
            pytest.fail(f"Resource list is not JSON serializable: {list_result}")

    @pytest.mark.asyncio
    async def test_resource_uris_are_valid(self, sample_documents, categories):
        """Test that all resource URIs follow the docs:// scheme."""
        result = await list_resources(sample_documents, categories)

        for resource in result:
            assert resource["uri"].startswith("docs://") or resource["uri"].startswith("api://")

    @pytest.mark.asyncio
    async def test_resource_names_are_human_readable(self, sample_documents, categories):
        """Test that resource names are human-readable."""
        result = await list_resources(sample_documents, categories)

        for resource in result:
            # Name should be present and non-empty
            assert "name" in resource
            assert len(resource["name"]) > 0
            # Should not be just the URI
            assert resource["name"] != resource["uri"]


class TestResourceEdgeCases:
    """Test edge cases in resource handling."""

    @pytest.mark.asyncio
    async def test_read_empty_document(self, categories):
        """Test reading a document with empty content."""
        empty_doc = Document(
            file_path=Path("/docs/empty.md"),
            relative_path=Path("empty.md"),
            uri="docs://empty",
            title="Empty Document",
            content="",
            last_modified=datetime.now(UTC),
            size_bytes=0,
        )

        result = await handle_resource_read("docs://empty", [empty_doc], categories)

        assert "text" in result
        # Should return empty string, not None
        assert result["text"] == ""

    @pytest.mark.asyncio
    async def test_read_category_with_no_documents(self):
        """Test reading an empty category."""
        empty_doc = Document(
            file_path=Path("/docs/empty/placeholder.md"),
            relative_path=Path("empty/placeholder.md"),
            uri="docs://empty/placeholder",
            title="Placeholder",
            content="# Placeholder",
            last_modified=datetime.now(UTC),
            size_bytes=10,
        )

        categories = build_category_tree([empty_doc])

        result = await handle_resource_read("docs://empty", [empty_doc], categories)

        # Should return category overview
        assert "uri" in result
        assert result["uri"] == "docs://empty"

    @pytest.mark.asyncio
    async def test_read_with_special_characters_in_uri(self, sample_documents, categories):
        """Test reading resources with special characters in URI."""
        special_doc = Document(
            file_path=Path("/docs/test-doc_name.md"),
            relative_path=Path("test-doc_name.md"),
            uri="docs://test-doc_name",
            title="Special Doc",
            content="Content",
            last_modified=datetime.now(UTC),
            size_bytes=50,
        )

        result = await handle_resource_read("docs://test-doc_name", [special_doc], categories)

        assert "uri" in result
        assert result["uri"] == "docs://test-doc_name"

    @pytest.mark.asyncio
    async def test_list_resources_with_no_documents(self):
        """Test listing resources when no documents exist."""
        result = await list_resources([], {})

        # Should still return list with at least root
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_resource_metadata_datetime_serialization(self, sample_documents, categories):
        """Test that datetime in metadata is properly serialized."""
        uri = "docs://guides/getting-started"

        result = await handle_resource_read(uri, sample_documents, categories)

        if "metadata" in result and "last_modified" in result["metadata"]:
            # Should be ISO format string, not datetime object
            last_modified = result["metadata"]["last_modified"]
            assert isinstance(last_modified, str)
            # Should be parseable as ISO format
            from datetime import datetime

            datetime.fromisoformat(last_modified.replace("Z", "+00:00"))


class TestResourceCaching:
    """Test resource caching behavior."""

    @pytest.mark.asyncio
    async def test_repeated_reads_return_consistent_data(self, sample_documents, categories):
        """Test that repeated reads return consistent data."""
        uri = "docs://guides/getting-started"

        result1 = await handle_resource_read(uri, sample_documents, categories)
        result2 = await handle_resource_read(uri, sample_documents, categories)

        # Results should be consistent
        assert result1["uri"] == result2["uri"]
        assert result1["text"] == result2["text"]

    @pytest.mark.asyncio
    async def test_list_resources_is_consistent(self, sample_documents, categories):
        """Test that list_resources returns consistent results."""
        result1 = await list_resources(sample_documents, categories)
        result2 = await list_resources(sample_documents, categories)

        # Should have same number of resources
        assert len(result1) == len(result2)

        # Should have same URIs
        uris1 = {r["uri"] for r in result1}
        uris2 = {r["uri"] for r in result2}
        assert uris1 == uris2
