"""Integration tests for white-label branding in the web UI."""

import pytest
from fastapi.testclient import TestClient

from docs_mcp.core.config import BrandingConfig, ServerConfig
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


def _make_client(docs_dir, branding=None, **kwargs):
    """Create a test client with optional custom branding."""
    docs = scan_markdown_files(docs_dir, docs_dir)
    cats = build_category_tree(docs)
    config_kwargs = {"docs_root": str(docs_dir)}
    if branding:
        config_kwargs["branding"] = branding
    config_kwargs.update(kwargs)
    config = ServerConfig(**config_kwargs)
    server = DocumentationWebServer(config=config, documents=docs, categories=cats)
    return TestClient(server.app, raise_server_exceptions=False)


class TestDefaultBranding:
    """Test that default branding renders correctly."""

    def test_default_site_name_in_title(self, docs_dir):
        client = _make_client(docs_dir)
        r = client.get("/docs/")
        assert "Documentation" in r.text
        assert r.status_code == 200

    def test_default_footer_present(self, docs_dir):
        client = _make_client(docs_dir)
        r = client.get("/docs/")
        assert "Your Docs MCP" in r.text

    def test_default_logo_emoji_present(self, docs_dir):
        client = _make_client(docs_dir)
        r = client.get("/docs/")
        assert "&#128214;" in r.text  # book emoji

    def test_no_css_overrides_with_defaults(self, docs_dir):
        client = _make_client(docs_dir)
        r = client.get("/docs/")
        # Default primary color should not generate override block
        assert "--accent-primary" not in r.text


class TestCustomBranding:
    """Test custom branding configuration."""

    def test_custom_site_name_in_title(self, docs_dir):
        branding = BrandingConfig(site_name="Acme Docs")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "Acme Docs" in r.text

    def test_custom_site_name_in_hero(self, docs_dir):
        branding = BrandingConfig(site_name="Acme Docs")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert '<h1 class="hero-title">Acme Docs</h1>' in r.text

    def test_custom_tagline_in_hero(self, docs_dir):
        branding = BrandingConfig(site_tagline="Enterprise documentation")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "Enterprise documentation" in r.text

    def test_custom_primary_color_generates_css_overrides(self, docs_dir):
        branding = BrandingConfig(primary_color="#e11d48")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "--accent-primary: #e11d48" in r.text

    def test_custom_logo_url_renders_img(self, docs_dir):
        branding = BrandingConfig(logo_url="/static/custom/logo.svg")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert '<img src="/static/custom/logo.svg"' in r.text
        assert "&#128214;" not in r.text  # emoji should NOT appear

    def test_custom_logo_text(self, docs_dir):
        branding = BrandingConfig(logo_text="ACME")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "ACME</span>" in r.text

    def test_logo_text_defaults_to_site_name(self, docs_dir):
        branding = BrandingConfig(site_name="Acme Docs")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "Acme Docs</span>" in r.text

    def test_footer_hidden_when_powered_by_false(self, docs_dir):
        branding = BrandingConfig(show_powered_by=False)
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "Your Docs MCP" not in r.text

    def test_custom_footer_html(self, docs_dir):
        branding = BrandingConfig(footer_html="&copy; 2026 Acme Corp")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "&copy; 2026 Acme Corp" in r.text

    def test_favicon_url_renders_link(self, docs_dir):
        branding = BrandingConfig(favicon_url="/static/custom/favicon.ico")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert '<link rel="icon" href="/static/custom/favicon.ico">' in r.text

    def test_no_favicon_link_by_default(self, docs_dir):
        client = _make_client(docs_dir)
        r = client.get("/docs/")
        assert 'rel="icon"' not in r.text

    def test_custom_css_url_renders_link(self, docs_dir):
        branding = BrandingConfig(custom_css_url="/static/custom/theme.css")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "/static/custom/theme.css" in r.text

    def test_custom_js_url_renders_script(self, docs_dir):
        branding = BrandingConfig(custom_js_url="/static/custom/analytics.js")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "/static/custom/analytics.js" in r.text

    def test_custom_css_inline(self, docs_dir):
        branding = BrandingConfig(custom_css="body { background: red; }")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "body { background: red; }" in r.text

    def test_og_image_url(self, docs_dir):
        branding = BrandingConfig(og_image_url="https://example.com/og.png")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "og:image" in r.text
        assert "https://example.com/og.png" in r.text

    def test_custom_font_cdn_url(self, docs_dir):
        branding = BrandingConfig(
            font_cdn_url="https://fonts.googleapis.com/css2?family=Roboto&display=swap"
        )
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/")
        assert "fonts.googleapis.com" in r.text
        # When custom font CDN is used, vendor fonts should not be loaded
        assert "vendor/fonts/fonts.css" not in r.text

    def test_default_uses_vendored_fonts(self, docs_dir):
        client = _make_client(docs_dir)
        r = client.get("/docs/")
        assert "vendor/fonts/fonts.css" in r.text


class TestBrandingOnDocumentPage:
    """Test that branding appears on document pages too."""

    def test_custom_site_name_in_doc_page_title(self, docs_dir):
        branding = BrandingConfig(site_name="Acme Docs")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/guides/intro")
        assert "Acme Docs" in r.text

    def test_custom_primary_color_on_doc_page(self, docs_dir):
        branding = BrandingConfig(primary_color="#e11d48")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/docs/guides/intro")
        assert "--accent-primary: #e11d48" in r.text


class TestFastAPITitle:
    """Test that the FastAPI app uses branding for its title."""

    def test_default_app_title(self, docs_dir):
        client = _make_client(docs_dir)
        r = client.get("/openapi.json")
        assert r.json()["info"]["title"] == "Documentation"

    def test_custom_app_title(self, docs_dir):
        branding = BrandingConfig(site_name="Acme Docs")
        client = _make_client(docs_dir, branding=branding)
        r = client.get("/openapi.json")
        assert r.json()["info"]["title"] == "Acme Docs"
