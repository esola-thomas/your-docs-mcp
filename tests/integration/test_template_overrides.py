"""Integration tests for template override system and custom static assets."""

import pytest
from fastapi.testclient import TestClient

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.services.hierarchy import build_category_tree
from docs_mcp.core.services.markdown import scan_markdown_files
from docs_mcp.web.app import DocumentationWebServer


@pytest.fixture
def docs_dir(tmp_path):
    """Create a minimal docs directory."""
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    guides = docs_root / "guides"
    guides.mkdir()
    (guides / "intro.md").write_text(
        "---\ntitle: Intro\ntags: [guide]\n---\n# Introduction\n\nHello world.\n"
    )
    return docs_root


def _make_client(docs_dir, **kwargs):
    """Create a test client with optional config overrides."""
    docs = scan_markdown_files(docs_dir, docs_dir)
    cats = build_category_tree(docs)
    config = ServerConfig(docs_root=str(docs_dir), **kwargs)
    server = DocumentationWebServer(config=config, documents=docs, categories=cats)
    return TestClient(server.app, raise_server_exceptions=False)


class TestTemplateOverrides:
    """Test Jinja2 ChoiceLoader template override system."""

    def test_custom_home_template(self, docs_dir, tmp_path):
        """Custom home.html should override the default."""
        custom_templates = tmp_path / "custom_templates"
        custom_templates.mkdir()
        (custom_templates / "home.html").write_text(
            '{% extends "base.html" %}\n{% block content %}<h1>CUSTOM HOME</h1>{% endblock %}'
        )

        client = _make_client(docs_dir, custom_templates_dir=str(custom_templates))
        r = client.get("/docs/")
        assert r.status_code == 200
        assert "CUSTOM HOME" in r.text

    def test_non_overridden_templates_use_defaults(self, docs_dir, tmp_path):
        """Templates not in custom dir should fall back to defaults."""
        custom_templates = tmp_path / "custom_templates"
        custom_templates.mkdir()
        # Only override home.html, not doc.html
        (custom_templates / "home.html").write_text(
            '{% extends "base.html" %}\n{% block content %}<h1>CUSTOM HOME</h1>{% endblock %}'
        )

        client = _make_client(docs_dir, custom_templates_dir=str(custom_templates))
        # Doc page should still use default template
        r = client.get("/docs/guides/intro")
        assert r.status_code == 200
        assert "Introduction" in r.text

    def test_no_custom_templates_dir_uses_defaults(self, docs_dir):
        """Without custom_templates_dir, default templates work."""
        client = _make_client(docs_dir)
        r = client.get("/docs/")
        assert r.status_code == 200
        assert "Documentation" in r.text


class TestCustomStaticAssets:
    """Test custom static file directory mounting."""

    def test_custom_static_files_served(self, docs_dir, tmp_path):
        """Files in custom_static_dir should be served at /static/custom/."""
        custom_static = tmp_path / "custom_static"
        custom_static.mkdir()
        (custom_static / "theme.css").write_text("body { color: red; }")

        client = _make_client(docs_dir, custom_static_dir=str(custom_static))
        r = client.get("/static/custom/theme.css")
        assert r.status_code == 200
        assert "body { color: red; }" in r.text

    def test_default_static_files_still_served(self, docs_dir, tmp_path):
        """Default static files should still work with custom dir mounted."""
        custom_static = tmp_path / "custom_static"
        custom_static.mkdir()

        client = _make_client(docs_dir, custom_static_dir=str(custom_static))
        r = client.get("/static/css/docs.css")
        assert r.status_code == 200

    def test_no_custom_static_dir(self, docs_dir):
        """Without custom_static_dir, default static files work."""
        client = _make_client(docs_dir)
        r = client.get("/static/css/docs.css")
        assert r.status_code == 200
