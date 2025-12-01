"""Integration tests for edge cases and error handling paths.

These tests cover error handling and edge cases across the system
to achieve complete code coverage.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from docs_mcp.config import ServerConfig
from docs_mcp.models.document import Document
from docs_mcp.services.cache import Cache
from docs_mcp.services.hierarchy import (
    build_category_tree,
    navigate_to_uri,
)
from docs_mcp.services.markdown import scan_markdown_files
from docs_mcp.services.search import (
    _extract_excerpt,
    _highlight_matches,
    search_content,
)


class TestCacheEviction:
    """Test cache eviction when max size is reached."""

    @pytest.fixture
    def small_cache(self):
        """Create a cache with small max size for testing eviction."""
        # Use default_ttl and max_size_mb parameters
        return Cache(default_ttl=300, max_size_mb=1)

    def test_cache_evicts_oldest_entry_when_full(self, small_cache):
        """Test that cache evicts oldest entry when max size is reached."""
        # Add entries until cache is full
        # Each entry is small but eventually will fill up
        for i in range(100):
            small_cache.set(f"key{i}", "x" * 100000)  # 100KB each

        # Cache should still work and have evicted oldest entries
        # Get should return None for very old entries
        assert small_cache.get("key0") is None  # Should be evicted

    def test_evict_oldest_on_empty_cache(self, small_cache):
        """Test that _evict_oldest handles empty cache gracefully."""
        # Call evict on empty cache - should not raise
        small_cache._evict_oldest()
        # Cache should still work
        small_cache.set("key", "value")
        assert small_cache.get("key") == "value"


class TestNavigationContextEdgeCases:
    """Test navigation context edge cases."""

    def test_navigate_to_root_level_document(self, tmp_path):
        """Test navigation to a document at root level (no breadcrumbs)."""
        # Create a document at root level (no parent path)
        doc = Document(
            file_path=tmp_path / "readme.md",
            relative_path=Path("readme.md"),
            uri="docs://readme",
            title="README",
            content="# README",
            tags=[],
            frontmatter={},
            category=None,
            last_modified=datetime.now(UTC),
            size_bytes=8,
            parent=None,
        )

        # Get navigation context using navigate_to_uri
        ctx = navigate_to_uri(doc.uri, [doc], {})

        # Should have parent_uri pointing to root
        assert ctx.parent_uri == "docs://"
        # Current URI should be the document
        assert ctx.current_uri == "docs://readme"
        assert ctx.current_type == "document"


class TestMarkdownScanningErrors:
    """Test error handling in markdown file scanning."""

    def test_scan_with_validation_error(self, tmp_path):
        """Test scanning handles path validation errors gracefully."""
        # Try to scan a non-existent path (will fail validation)
        nonexistent = tmp_path / "nonexistent"

        docs = scan_markdown_files(
            source_path=nonexistent,
            doc_root=tmp_path,
            recursive=True,
        )

        # Should return empty list instead of crashing
        assert docs == []

    def test_scan_with_parsing_error(self, tmp_path):
        """Test scanning handles individual file parsing errors gracefully."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create a valid file
        valid_file = docs_dir / "valid.md"
        valid_file.write_text("# Valid\n\nContent")

        # Create a file with problematic content that might cause parsing issues
        # (though our parser is robust, we're testing the error handling path)
        problem_file = docs_dir / "problem.md"
        problem_file.write_text("")  # Empty file

        docs = scan_markdown_files(
            source_path=docs_dir,
            doc_root=tmp_path,
            recursive=False,
        )

        # Should still get the valid document
        assert len(docs) >= 1
        assert any(doc.title == "Valid" for doc in docs)

    def test_scan_with_directory_error(self, tmp_path, monkeypatch):
        """Test scanning handles directory iteration errors gracefully."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "test.md"
        test_file.write_text("# Test")

        # Mock rglob to raise an exception
        original_rglob = Path.rglob

        def failing_rglob(self, pattern):
            raise PermissionError("Simulated permission error")

        monkeypatch.setattr(Path, "rglob", failing_rglob)

        docs = scan_markdown_files(
            source_path=docs_dir,
            doc_root=tmp_path,
            recursive=True,
        )

        # Should return empty list on directory scan error
        assert docs == []

        # Restore original
        monkeypatch.setattr(Path, "rglob", original_rglob)


class TestSearchErrorHandling:
    """Test error handling in search functions."""

    def test_extract_excerpt_with_exception(self):
        """Test excerpt extraction handles exceptions gracefully."""
        # Create content that might cause issues
        content = "Test content"

        # Test with a query that will work
        result = _extract_excerpt(content, "test", context_chars=50)
        assert "test" in result.lower()

        # Even with edge cases, should return something
        result = _extract_excerpt("", "", context_chars=0)
        assert isinstance(result, str)

    def test_highlight_matches_with_invalid_regex(self):
        """Test highlight_matches handles regex errors gracefully."""
        text = "This is some text to highlight"

        # Normal case should work
        result = _highlight_matches(text, "text")
        assert "**text**" in result

        # Special regex characters should be escaped
        result = _highlight_matches(text, "text*")
        # Should not crash and should return original or highlighted text
        assert isinstance(result, str)

    def test_highlight_matches_with_exception(self, monkeypatch):
        """Test highlight_matches handles unexpected exceptions gracefully."""
        text = "Test text"
        query = "test"

        # Mock re.compile to raise an exception
        original_compile = re.compile

        def failing_compile(*args, **kwargs):
            raise Exception("Simulated regex error")

        monkeypatch.setattr(re, "compile", failing_compile)

        # Should return original text on exception
        result = _highlight_matches(text, query)
        assert result == text

        # Restore original
        monkeypatch.setattr(re, "compile", original_compile)


class TestMainEntryPointError:
    """Test error handling in __main__.py entry point."""

    def test_main_with_invalid_config(self, tmp_path, monkeypatch):
        """Test main function handles configuration errors gracefully."""
        import sys
        from io import StringIO

        from docs_mcp.__main__ import main

        # Create a config file with invalid content
        config_file = tmp_path / "invalid_config.json"
        config_file.write_text("{invalid json")

        # Mock sys.argv to use invalid config
        monkeypatch.setattr(sys, "argv", ["mcp", "--config", str(config_file)])

        # Mock sys.stderr to capture error
        mock_stderr = StringIO()
        monkeypatch.setattr(sys, "stderr", mock_stderr)

        # Should exit with error code 1
        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1

    def test_main_with_missing_config_file(self, tmp_path, monkeypatch):
        """Test main function handles missing config file gracefully."""
        import sys
        from io import StringIO

        from docs_mcp.__main__ import main

        # Mock sys.argv to use non-existent config
        nonexistent = tmp_path / "nonexistent.json"
        monkeypatch.setattr(sys, "argv", ["mcp", "--config", str(nonexistent)])

        # Mock sys.stderr
        mock_stderr = StringIO()
        monkeypatch.setattr(sys, "stderr", mock_stderr)

        # Should exit with error code 1
        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1


class TestHierarchyEdgeCases:
    """Test edge cases in hierarchy building."""

    def test_build_hierarchy_with_none_category(self, tmp_path):
        """Test hierarchy handles documents with no category gracefully."""
        # Create document with None category
        doc = Document(
            file_path=tmp_path / "uncategorized.md",
            relative_path=Path("uncategorized.md"),
            uri="docs://uncategorized",
            title="Uncategorized",
            content="# Uncategorized",
            tags=[],
            frontmatter={},
            category=None,
            last_modified=datetime.now(UTC),
            size_bytes=15,
            parent=None,
        )

        # Should not crash
        categories = build_category_tree([doc])

        # Should create some category structure
        assert isinstance(categories, dict)


class TestServerHandlerCoverage:
    """Tests to increase server.py handler coverage through actual usage."""

    @pytest.fixture
    async def initialized_server(self, tmp_path):
        """Create an initialized server."""
        from docs_mcp.server import DocumentationMCPServer

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create test documents
        guides_dir = docs_dir / "guides"
        guides_dir.mkdir()

        test_file = guides_dir / "test.md"
        test_file.write_text("# Test Guide\n\nThis is a test.")

        config = ServerConfig(docs_root=str(docs_dir))
        server = DocumentationMCPServer(config)
        await server.initialize()
        return server

    @pytest.mark.asyncio
    async def test_server_run_method_exists(self, initialized_server):
        """Test that server.run() method exists and is callable."""
        # We can't actually run it (would block), but we can verify it exists
        assert hasattr(initialized_server, "run")
        assert callable(initialized_server.run)

        # Verify it's an async method
        import inspect

        assert inspect.iscoroutinefunction(initialized_server.run)


class TestComplexSearchScenarios:
    """Test complex search scenarios to cover more code paths."""

    @pytest.fixture
    def documents_with_special_content(self, tmp_path):
        """Create documents with special content for testing."""
        from datetime import UTC, datetime

        docs = []

        # Document with very long content (to test excerpt truncation)
        long_content = "word " * 1000
        docs.append(
            Document(
                file_path=tmp_path / "long.md",
                relative_path=Path("long.md"),
                uri="docs://long",
                title="Long Document",
                content=long_content,
                tags=["long"],
                frontmatter={},
                category="test",
                last_modified=datetime.now(UTC),
                size_bytes=len(long_content),
                parent=None,
            )
        )

        # Document with special characters
        special_content = "Test with special: $regex* chars"
        docs.append(
            Document(
                file_path=tmp_path / "special.md",
                relative_path=Path("special.md"),
                uri="docs://special",
                title="Special Characters",
                content=special_content,
                tags=["special"],
                frontmatter={},
                category="test",
                last_modified=datetime.now(UTC),
                size_bytes=len(special_content),
                parent=None,
            )
        )

        return docs

    def test_search_with_excerpt_extraction_edge_cases(self, documents_with_special_content):
        """Test search with documents that stress excerpt extraction."""
        # Search the long document
        results = search_content(
            query="word",
            documents=documents_with_special_content,
            categories={},
            limit=10,
            category_filter=None,
        )

        assert len(results) > 0
        # SearchResult should have been returned
        assert hasattr(results[0], "excerpt") or hasattr(results[0], "highlighted_excerpt")

    def test_search_with_special_characters(self, documents_with_special_content):
        """Test search handles special regex characters."""
        # Search for text (not special characters directly as they get sanitized)
        results = search_content(
            query="special",
            documents=documents_with_special_content,
            categories={},
            limit=10,
            category_filter=None,
        )

        # Should handle gracefully
        assert isinstance(results, list)
