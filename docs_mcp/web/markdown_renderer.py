"""Server-side markdown to HTML rendering with Pygments syntax highlighting."""

import re
from typing import Any

import markdown
from markdown.extensions.toc import TocExtension


class AdmonitionPreprocessor(markdown.preprocessors.Preprocessor):
    """Convert :::note/tip/warning/danger blocks to HTML admonitions."""

    PATTERN = re.compile(
        r"^:::(note|tip|warning|danger|info|caution)\s*(.*?)\n(.*?)^:::\s*$",
        re.MULTILINE | re.DOTALL,
    )

    ICONS = {
        "note": "&#x2139;&#xFE0F;",  # info
        "info": "&#x2139;&#xFE0F;",
        "tip": "&#x1F4A1;",  # lightbulb
        "warning": "&#x26A0;&#xFE0F;",  # warning
        "caution": "&#x26A0;&#xFE0F;",
        "danger": "&#x1F6A8;",  # rotating light
    }

    def run(self, lines: list[str]) -> list[str]:
        text = "\n".join(lines)

        def replace_admonition(match: re.Match[str]) -> str:
            adm_type = match.group(1).lower()
            title = match.group(2).strip() or adm_type.capitalize()
            content = match.group(3).strip()
            icon = self.ICONS.get(adm_type, "")
            # Map caution/info to their CSS class equivalents
            css_class = adm_type
            if adm_type == "caution":
                css_class = "warning"
            elif adm_type == "info":
                css_class = "note"

            return (
                f'<div class="admonition {css_class}">\n'
                f'<p class="admonition-title">{icon} {title}</p>\n'
                f"<p>{content}</p>\n"
                f"</div>\n"
            )

        text = self.PATTERN.sub(replace_admonition, text)
        return text.split("\n")


class AdmonitionExtension(markdown.Extension):
    """Markdown extension for :::type admonition blocks."""

    def extendMarkdown(self, md: markdown.Markdown) -> None:  # noqa: N802
        md.preprocessors.register(AdmonitionPreprocessor(md), "admonition_blocks", 30)


def _build_markdown_processor() -> markdown.Markdown:
    """Create a configured Markdown processor."""
    try:
        from pygments.formatters import HtmlFormatter

        HtmlFormatter()  # Verify Pygments works
        codehilite_config = {
            "css_class": "highlight",
            "linenums": False,
            "guess_lang": False,
        }
        use_codehilite = True
    except ImportError:
        codehilite_config = {}
        use_codehilite = False

    extensions: list[Any] = [
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.footnotes",
        "markdown.extensions.attr_list",
        "markdown.extensions.def_list",
        "markdown.extensions.abbr",
        "markdown.extensions.md_in_html",
        "markdown.extensions.sane_lists",
        TocExtension(
            permalink=True,
            permalink_class="header-anchor",
            permalink_title="Link to this section",
            toc_depth="2-4",
        ),
        AdmonitionExtension(),
    ]

    extension_configs: dict[str, Any] = {}

    if use_codehilite:
        extensions.append("markdown.extensions.codehilite")
        extension_configs["markdown.extensions.codehilite"] = codehilite_config

    return markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs,
        output_format="html",
    )


# Module-level processor
_md_processor: markdown.Markdown | None = None


def _get_processor() -> markdown.Markdown:
    global _md_processor
    if _md_processor is None:
        _md_processor = _build_markdown_processor()
    return _md_processor


def render_markdown(content: str) -> dict[str, Any]:
    """Render markdown content to HTML with extracted TOC.

    Args:
        content: Raw markdown string

    Returns:
        Dict with 'html' (rendered HTML) and 'toc' (list of heading dicts)
    """
    md = _get_processor()
    md.reset()

    html = md.convert(content)

    # Post-processing enhancements
    html = _enhance_code_blocks(html)
    html = _wrap_tables(html)
    html = _enhance_images(html)
    html = _enhance_task_lists(html)

    # Extract TOC from the TocExtension
    toc_items = []
    if hasattr(md, "toc_tokens"):
        toc_items = _flatten_toc(md.toc_tokens)

    return {
        "html": html,
        "toc": toc_items,
    }


def _flatten_toc(tokens: list[dict[str, Any]], depth: int = 0) -> list[dict[str, Any]]:
    """Flatten nested TOC tokens into a flat list with depth info."""
    items = []
    for token in tokens:
        items.append(
            {
                "id": token.get("id", ""),
                "name": token.get("name", ""),
                "level": token.get("level", 2),
                "depth": depth,
            }
        )
        children = token.get("children", [])
        if children:
            items.extend(_flatten_toc(children, depth + 1))
    return items


def _enhance_code_blocks(html: str) -> str:
    """Add language labels and copy button wrappers to code blocks."""

    def replace_pre(match: re.Match[str]) -> str:
        attrs = match.group(1) or ""
        code_content = match.group(2)

        # Try to extract language from class
        lang_match = re.search(r'class="[^"]*language-(\w+)', attrs)
        if not lang_match:
            lang_match = re.search(r'class="[^"]*(\w+)', attrs)

        lang = lang_match.group(1) if lang_match else ""

        # Skip if it's a Pygments-highlighted block (has highlight class)
        if "highlight" in attrs:
            lang_label = f'<span class="code-lang">{lang}</span>' if lang else ""
            return (
                f'<div class="code-block">'
                f'<div class="code-header">{lang_label}'
                f'<button class="copy-btn" title="Copy code">Copy</button></div>'
                f"<pre{attrs}>{code_content}</pre></div>"
            )

        lang_label = f'<span class="code-lang">{lang}</span>' if lang else ""
        return (
            f'<div class="code-block">'
            f'<div class="code-header">{lang_label}'
            f'<button class="copy-btn" title="Copy code">Copy</button></div>'
            f"<pre{attrs}>{code_content}</pre></div>"
        )

    # Match <pre> tags (possibly with attributes) containing code
    html = re.sub(
        r"<pre([^>]*)>(.*?)</pre>",
        replace_pre,
        html,
        flags=re.DOTALL,
    )

    return html


def _wrap_tables(html: str) -> str:
    """Wrap <table> elements in a responsive scroll container."""
    return re.sub(
        r"(<table[^>]*>.*?</table>)",
        r'<div class="table-responsive">\1</div>',
        html,
        flags=re.DOTALL,
    )


def _enhance_images(html: str) -> str:
    """Wrap standalone images in <figure> with alt text as caption."""
    # Only wrap images that are direct children of <p> (standalone images)
    return re.sub(
        r"<p>\s*(<img[^>]+>)\s*</p>",
        lambda m: f'<figure class="doc-figure">{m.group(1)}'
        + (
            f"<figcaption>{a.group(1)}</figcaption>"
            if (a := re.search(r'alt="([^"]+)"', m.group(1)))
            else ""
        )
        + "</figure>",
        html,
    )


def _enhance_task_lists(html: str) -> str:
    """Convert checkbox list items into styled task list items."""
    html = re.sub(
        r"<li>\s*\[ \]\s*",
        '<li class="task-list-item"><input type="checkbox" disabled> ',
        html,
    )
    html = re.sub(
        r"<li>\s*\[x\]\s*",
        '<li class="task-list-item task-list-item--checked">'
        '<input type="checkbox" checked disabled> ',
        html,
        flags=re.IGNORECASE,
    )
    return html
