"""Unit tests for server-side markdown rendering."""

from docs_mcp.web.markdown_renderer import render_markdown


class TestRenderMarkdown:
    """Test the render_markdown function."""

    def test_basic_markdown(self):
        """Test rendering basic markdown to HTML."""
        result = render_markdown("# Hello\n\nWorld")
        assert "<h1" in result["html"]
        assert "Hello" in result["html"]
        assert "World" in result["html"]
        assert isinstance(result["toc"], list)

    def test_code_block_with_language(self):
        """Test fenced code blocks get syntax highlighting."""
        md = "```python\ndef hello():\n    pass\n```"
        result = render_markdown(md)
        assert "<pre" in result["html"]
        assert "copy-btn" in result["html"]

    def test_code_block_without_language(self):
        """Test fenced code blocks without language."""
        md = "```\nsome code\n```"
        result = render_markdown(md)
        assert "<pre" in result["html"]

    def test_table_rendering(self):
        """Test table rendering."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = render_markdown(md)
        assert "<table" in result["html"]
        assert "<th" in result["html"]

    def test_heading_anchors(self):
        """Test headings get permalink anchors."""
        result = render_markdown("## Section Title")
        assert 'id="section-title"' in result["html"]
        assert "header-anchor" in result["html"]

    def test_toc_extraction(self):
        """Test TOC is extracted from headings."""
        md = "## First\n\nText\n\n## Second\n\nMore text"
        result = render_markdown(md)
        assert len(result["toc"]) >= 2
        assert result["toc"][0]["name"] == "First"
        assert result["toc"][1]["name"] == "Second"

    def test_admonition_note(self):
        """Test :::note admonition blocks."""
        md = ":::note Important\nThis is a note.\n:::"
        result = render_markdown(md)
        assert "admonition" in result["html"]
        assert "note" in result["html"]
        assert "Important" in result["html"]

    def test_admonition_warning(self):
        """Test :::warning admonition blocks."""
        md = ":::warning\nBe careful.\n:::"
        result = render_markdown(md)
        assert "admonition" in result["html"]
        assert "warning" in result["html"]

    def test_admonition_tip(self):
        """Test :::tip admonition blocks."""
        md = ":::tip\nHelpful hint.\n:::"
        result = render_markdown(md)
        assert "admonition" in result["html"]
        assert "tip" in result["html"]

    def test_admonition_danger(self):
        """Test :::danger admonition blocks."""
        md = ":::danger\nDangerous!\n:::"
        result = render_markdown(md)
        assert "admonition" in result["html"]
        assert "danger" in result["html"]

    def test_inline_code(self):
        """Test inline code rendering."""
        result = render_markdown("Use `print()` function")
        assert "<code>" in result["html"]

    def test_bold_and_italic(self):
        """Test emphasis rendering."""
        result = render_markdown("**bold** and *italic*")
        assert "<strong>" in result["html"]
        assert "<em>" in result["html"]

    def test_links(self):
        """Test link rendering."""
        result = render_markdown("[click](https://example.com)")
        assert '<a href="https://example.com">' in result["html"]

    def test_empty_content(self):
        """Test rendering empty content."""
        result = render_markdown("")
        assert result["html"] == ""
        assert result["toc"] == []

    def test_blockquote(self):
        """Test blockquote rendering."""
        result = render_markdown("> This is a quote")
        assert "<blockquote" in result["html"]

    def test_unordered_list(self):
        """Test unordered list rendering."""
        result = render_markdown("- item 1\n- item 2")
        assert "<ul>" in result["html"]
        assert "<li>" in result["html"]

    def test_ordered_list(self):
        """Test ordered list rendering."""
        result = render_markdown("1. first\n2. second")
        assert "<ol>" in result["html"]

    def test_footnotes(self):
        """Test footnote rendering."""
        md = "Text with footnote[^1].\n\n[^1]: Footnote content."
        result = render_markdown(md)
        assert "footnote" in result["html"].lower()

    def test_multiple_renders_reset_state(self):
        """Test that consecutive renders don't leak state."""
        render_markdown("## Heading A")  # prime the processor
        r2 = render_markdown("## Heading B")
        assert "Heading A" not in r2["html"]
        assert "Heading B" in r2["html"]
