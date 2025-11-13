"""Unit tests for markdown parsing with YAML frontmatter."""

from datetime import datetime
from pathlib import Path

import pytest

from hierarchical_docs_mcp.models.document import Document
from hierarchical_docs_mcp.services.markdown import (
    MarkdownParseError,
    _extract_frontmatter,
    _extract_title,
    _generate_uri,
    parse_markdown_with_metadata,
    scan_markdown_files,
)


@pytest.fixture
def temp_docs(tmp_path):
    """Create a temporary documentation structure."""
    doc_root = tmp_path / "docs"
    doc_root.mkdir()

    # Create test files
    (doc_root / "guides").mkdir()
    (doc_root / "api").mkdir()

    return doc_root


class TestExtractFrontmatter:
    """Test YAML frontmatter extraction."""

    def test_valid_frontmatter(self):
        """Test extraction of valid YAML frontmatter."""
        content = """---
title: Test Document
tags: [test, documentation]
category: guides
order: 1
---

# Content

This is the body."""

        frontmatter, body = _extract_frontmatter(content)

        assert frontmatter["title"] == "Test Document"
        assert frontmatter["tags"] == ["test", "documentation"]
        assert frontmatter["category"] == "guides"
        assert frontmatter["order"] == 1
        assert "# Content" in body

    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        content = """# Document Title

Regular markdown content."""

        frontmatter, body = _extract_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_empty_frontmatter(self):
        """Test empty frontmatter section."""
        content = """---
---

# Content"""

        frontmatter, body = _extract_frontmatter(content)

        assert frontmatter == {}
        assert "# Content" in body

    def test_malformed_yaml(self):
        """Test graceful handling of malformed YAML."""
        content = """---
title: Test
invalid yaml: [unclosed
---

# Content"""

        frontmatter, body = _extract_frontmatter(content)

        # Should fall back to empty frontmatter
        assert frontmatter == {}
        # Should return original content
        assert "title: Test" in body or "# Content" in body

    def test_frontmatter_with_complex_types(self):
        """Test frontmatter with complex YAML types."""
        content = """---
title: Complex
metadata:
  author: John Doe
  created: 2024-01-01
tags:
  - tag1
  - tag2
settings:
  enabled: true
  count: 42
---

Body"""

        frontmatter, body = _extract_frontmatter(content)

        assert frontmatter["title"] == "Complex"
        assert isinstance(frontmatter["metadata"], dict)
        assert frontmatter["metadata"]["author"] == "John Doe"
        assert isinstance(frontmatter["tags"], list)

    def test_frontmatter_non_dict_type(self):
        """Test handling of non-dict YAML result."""
        content = """---
just a string
---

Body"""

        frontmatter, body = _extract_frontmatter(content)

        # Should return empty dict for non-dict frontmatter
        assert frontmatter == {}

    def test_incomplete_frontmatter(self):
        """Test incomplete frontmatter (only one delimiter)."""
        content = """---
title: Test

No closing delimiter

# Content"""

        frontmatter, body = _extract_frontmatter(content)

        # Should return empty frontmatter
        assert frontmatter == {}
        assert "title: Test" in body

    def test_frontmatter_with_special_characters(self):
        """Test frontmatter with special characters."""
        content = """---
title: "Test: With Colons"
description: "Line 1\\nLine 2"
path: "/guides/test"
---

Body"""

        frontmatter, body = _extract_frontmatter(content)

        assert "Test: With Colons" in frontmatter["title"]


class TestExtractTitle:
    """Test title extraction from various sources."""

    def test_title_from_frontmatter(self):
        """Test title from frontmatter takes precedence."""
        frontmatter = {"title": "Frontmatter Title"}
        body = "# Heading Title"
        filename = "file-name.md"

        title = _extract_title(frontmatter, body, filename)

        assert title == "Frontmatter Title"

    def test_title_from_heading(self):
        """Test title from markdown heading."""
        frontmatter = {}
        body = "# Heading Title\n\nContent"
        filename = "file-name.md"

        title = _extract_title(frontmatter, body, filename)

        assert title == "Heading Title"

    def test_title_from_filename(self):
        """Test title from filename fallback."""
        frontmatter = {}
        body = "Content without heading"
        filename = "file-name-test.md"

        title = _extract_title(frontmatter, body, filename)

        assert title == "File Name Test"  # Should be title-cased and spaces

    def test_title_from_heading_h2(self):
        """Test that only h1 headings are extracted."""
        frontmatter = {}
        body = "## Heading 2\n\nContent"
        filename = "test.md"

        # Should fall back to filename since no h1
        title = _extract_title(frontmatter, body, filename)

        assert title == "Test"

    def test_title_with_multiple_headings(self):
        """Test that first h1 heading is used."""
        frontmatter = {}
        body = """# First Heading

Content

# Second Heading"""
        filename = "test.md"

        title = _extract_title(frontmatter, body, filename)

        assert title == "First Heading"

    def test_title_from_filename_with_underscores(self):
        """Test filename with underscores."""
        frontmatter = {}
        body = "Content"
        filename = "file_name_test.md"

        title = _extract_title(frontmatter, body, filename)

        assert title == "File Name Test"

    def test_title_from_filename_with_numbers(self):
        """Test filename with numbers."""
        frontmatter = {}
        body = "Content"
        filename = "01-getting-started.md"

        title = _extract_title(frontmatter, body, filename)

        assert "Getting Started" in title


class TestGenerateURI:
    """Test URI generation from relative paths."""

    def test_simple_path(self):
        """Test URI generation for simple path."""
        relative_path = Path("guides/getting-started.md")
        uri = _generate_uri(relative_path)

        assert uri == "docs://guides/getting-started"

    def test_nested_path(self):
        """Test URI generation for nested path."""
        relative_path = Path("guides/security/authentication.md")
        uri = _generate_uri(relative_path)

        assert uri == "docs://guides/security/authentication"

    def test_root_level_file(self):
        """Test URI generation for root level file."""
        relative_path = Path("readme.md")
        uri = _generate_uri(relative_path)

        assert uri == "docs://readme"

    def test_path_with_mdx_extension(self):
        """Test URI generation removes .mdx extension."""
        relative_path = Path("guides/test.mdx")
        uri = _generate_uri(relative_path)

        assert uri == "docs://guides/test"


class TestParseMarkdownWithMetadata:
    """Test complete markdown parsing with metadata."""

    def test_parse_valid_markdown_file(self, temp_docs):
        """Test parsing a valid markdown file."""
        test_file = temp_docs / "guides" / "test.md"
        test_file.write_text(
            """---
title: Test Guide
tags: [test, guide]
category: guides
order: 1
---

# Getting Started

This is a test guide."""
        )

        doc = parse_markdown_with_metadata(test_file, temp_docs)

        assert isinstance(doc, Document)
        assert doc.title == "Test Guide"
        assert doc.tags == ["test", "guide"]
        assert doc.category == "guides"
        assert doc.order == 1
        assert "Getting Started" in doc.content
        assert doc.uri == "docs://guides/test"

    def test_parse_markdown_without_frontmatter(self, temp_docs):
        """Test parsing markdown without frontmatter."""
        test_file = temp_docs / "guides" / "simple.md"
        test_file.write_text(
            """# Simple Document

Content here."""
        )

        doc = parse_markdown_with_metadata(test_file, temp_docs)

        assert doc.title == "Simple Document"
        assert doc.tags == []
        assert doc.category is None

    def test_parse_markdown_with_malformed_frontmatter(self, temp_docs):
        """Test parsing markdown with malformed frontmatter."""
        test_file = temp_docs / "guides" / "malformed.md"
        test_file.write_text(
            """---
title: Test
broken: [yaml
---

# Content"""
        )

        doc = parse_markdown_with_metadata(test_file, temp_docs)

        # Should succeed with fallback handling
        assert isinstance(doc, Document)

    def test_parse_nonexistent_file(self, temp_docs):
        """Test parsing nonexistent file."""
        nonexistent = temp_docs / "nonexistent.md"

        with pytest.raises(MarkdownParseError):
            parse_markdown_with_metadata(nonexistent, temp_docs)

    def test_parse_file_outside_root(self, temp_docs, tmp_path):
        """Test parsing file outside doc root."""
        outside_file = tmp_path / "outside.md"
        outside_file.write_text("# Outside")

        with pytest.raises(MarkdownParseError, match="validation failed"):
            parse_markdown_with_metadata(outside_file, temp_docs)

    def test_parse_hidden_file(self, temp_docs):
        """Test parsing hidden file is blocked."""
        hidden_file = temp_docs / ".hidden.md"
        hidden_file.write_text("# Hidden")

        with pytest.raises(MarkdownParseError, match="validation failed"):
            parse_markdown_with_metadata(hidden_file, temp_docs)

    def test_parse_file_with_unicode_content(self, temp_docs):
        """Test parsing file with Unicode content."""
        test_file = temp_docs / "unicode.md"
        test_file.write_text(
            """---
title: 中文标题
---

# 中文内容

这是中文文档。"""
        )

        doc = parse_markdown_with_metadata(test_file, temp_docs)

        assert "中文标题" in doc.title
        assert "中文内容" in doc.content

    def test_document_metadata_fields(self, temp_docs):
        """Test that all document metadata fields are populated."""
        test_file = temp_docs / "complete.md"
        test_file.write_text(
            """---
title: Complete Doc
tags: [tag1, tag2]
category: test
order: 5
parent: root
---

Content"""
        )

        doc = parse_markdown_with_metadata(test_file, temp_docs)

        assert doc.file_path == test_file.resolve()
        assert doc.relative_path == Path("complete.md")
        assert doc.uri == "docs://complete"
        assert doc.title == "Complete Doc"
        assert doc.tags == ["tag1", "tag2"]
        assert doc.category == "test"
        assert doc.order == 5
        assert doc.parent == "root"
        assert isinstance(doc.last_modified, datetime)
        assert doc.size_bytes > 0

    def test_parse_caching(self, temp_docs):
        """Test that parsed documents are cached."""
        test_file = temp_docs / "cached.md"
        test_file.write_text("# Cached")

        # First parse
        doc1 = parse_markdown_with_metadata(test_file, temp_docs)

        # Second parse should hit cache
        doc2 = parse_markdown_with_metadata(test_file, temp_docs)

        # Should return same data
        assert doc1.title == doc2.title
        assert doc1.uri == doc2.uri


class TestScanMarkdownFiles:
    """Test scanning directories for markdown files."""

    def test_scan_single_directory(self, temp_docs):
        """Test scanning a single directory."""
        (temp_docs / "test1.md").write_text("# Test 1")
        (temp_docs / "test2.md").write_text("# Test 2")

        documents = scan_markdown_files(temp_docs, temp_docs, recursive=False)

        assert len(documents) == 2
        titles = [doc.title for doc in documents]
        assert "Test 1" in titles
        assert "Test 2" in titles

    def test_scan_recursive(self, temp_docs):
        """Test recursive scanning."""
        (temp_docs / "root.md").write_text("# Root")
        (temp_docs / "guides" / "guide1.md").write_text("# Guide 1")
        (temp_docs / "guides" / "guide2.md").write_text("# Guide 2")
        (temp_docs / "api" / "api1.md").write_text("# API 1")

        documents = scan_markdown_files(temp_docs, temp_docs, recursive=True)

        assert len(documents) >= 4

    def test_scan_with_include_patterns(self, temp_docs):
        """Test scanning with specific include patterns."""
        (temp_docs / "test.md").write_text("# MD")
        (temp_docs / "test.mdx").write_text("# MDX")
        (temp_docs / "test.txt").write_text("# TXT")

        documents = scan_markdown_files(
            temp_docs, temp_docs, recursive=False, include_patterns=["*.md"]
        )

        # Should only include .md files
        assert len(documents) == 1
        assert documents[0].file_path.suffix == ".md"

    def test_scan_with_exclude_patterns(self, temp_docs):
        """Test scanning with exclude patterns."""
        (temp_docs / "node_modules").mkdir()
        (temp_docs / "node_modules" / "test.md").write_text("# Node Modules")
        (temp_docs / ".git").mkdir()
        (temp_docs / ".git" / "test.md").write_text("# Git")
        (temp_docs / "valid.md").write_text("# Valid")

        documents = scan_markdown_files(
            temp_docs,
            temp_docs,
            recursive=True,
            exclude_patterns=["node_modules", ".git"],
        )

        # Should exclude node_modules and .git
        paths = [str(doc.file_path) for doc in documents]
        assert not any("node_modules" in p for p in paths)
        assert not any(".git" in p for p in paths)

    def test_scan_empty_directory(self, temp_docs):
        """Test scanning empty directory."""
        empty_dir = temp_docs / "empty"
        empty_dir.mkdir()

        documents = scan_markdown_files(empty_dir, temp_docs, recursive=True)

        assert len(documents) == 0

    def test_scan_with_malformed_files(self, temp_docs):
        """Test that scanning continues despite malformed files."""
        (temp_docs / "valid.md").write_text("# Valid")
        # Create a file that might cause parsing issues
        (temp_docs / "invalid.md").write_text("---\ninvalid yaml: [[[\n---\n# Invalid")
        (temp_docs / "another_valid.md").write_text("# Another Valid")

        documents = scan_markdown_files(temp_docs, temp_docs, recursive=False)

        # Should still get the valid files
        assert len(documents) >= 2

    def test_scan_nonexistent_directory(self, temp_docs):
        """Test scanning nonexistent directory."""
        nonexistent = temp_docs / "nonexistent"

        documents = scan_markdown_files(nonexistent, temp_docs)

        assert len(documents) == 0

    def test_scan_mdx_files(self, temp_docs):
        """Test scanning .mdx files."""
        (temp_docs / "component.mdx").write_text("# MDX Component")

        documents = scan_markdown_files(
            temp_docs, temp_docs, recursive=False, include_patterns=["*.mdx"]
        )

        assert len(documents) == 1
        assert documents[0].file_path.suffix == ".mdx"

    def test_scan_preserves_directory_structure(self, temp_docs):
        """Test that scanning preserves directory structure in URIs."""
        # Create directory structure
        (temp_docs / "guides").mkdir(exist_ok=True)
        (temp_docs / "guides" / "advanced").mkdir(parents=True, exist_ok=True)

        # Create files
        (temp_docs / "guides" / "getting-started.md").write_text("# Getting Started")
        (temp_docs / "guides" / "advanced" / "performance.md").write_text("# Performance")

        documents = scan_markdown_files(temp_docs, temp_docs, recursive=True)

        uris = [doc.uri for doc in documents]
        assert any("guides/getting-started" in uri for uri in uris)
        assert any("guides/advanced/performance" in uri for uri in uris)


class TestMarkdownEdgeCases:
    """Test edge cases in markdown parsing."""

    def test_empty_markdown_file(self, temp_docs):
        """Test parsing empty markdown file."""
        empty_file = temp_docs / "empty.md"
        empty_file.write_text("")

        doc = parse_markdown_with_metadata(empty_file, temp_docs)

        assert doc.content == ""
        assert doc.title == "Empty"  # From filename

    def test_markdown_with_code_blocks(self, temp_docs):
        """Test that code blocks are preserved."""
        code_file = temp_docs / "code.md"
        code_file.write_text(
            """# Code Example

```python
def hello():
    print("Hello, World!")
```

Text after code."""
        )

        doc = parse_markdown_with_metadata(code_file, temp_docs)

        assert "```python" in doc.content
        assert "def hello():" in doc.content

    def test_markdown_with_inline_code(self, temp_docs):
        """Test that inline code is preserved."""
        inline_file = temp_docs / "inline.md"
        inline_file.write_text("# Inline\n\nUse `print()` function.")

        doc = parse_markdown_with_metadata(inline_file, temp_docs)

        assert "`print()`" in doc.content

    def test_markdown_with_tables(self, temp_docs):
        """Test that markdown tables are preserved."""
        table_file = temp_docs / "table.md"
        table_file.write_text(
            """# Table

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
"""
        )

        doc = parse_markdown_with_metadata(table_file, temp_docs)

        assert "|" in doc.content
        assert "Column 1" in doc.content

    def test_very_large_file(self, temp_docs):
        """Test parsing very large markdown file."""
        large_file = temp_docs / "large.md"
        large_content = "# Large\n\n" + ("Line of content\n" * 10000)
        large_file.write_text(large_content)

        doc = parse_markdown_with_metadata(large_file, temp_docs)

        assert doc.size_bytes > 100000
        assert "Large" in doc.title
