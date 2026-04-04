"""Unit tests for BrandingConfig, feature flags, and YAML config loading."""

import pytest

from docs_mcp.core.config import BrandingConfig, ServerConfig, _apply_yaml_config, load_config


class TestBrandingConfigDefaults:
    """Test that BrandingConfig has sensible defaults."""

    def test_default_site_name(self):
        config = BrandingConfig()
        assert config.site_name == "Documentation"

    def test_default_site_tagline(self):
        config = BrandingConfig()
        assert config.site_tagline == "Browse, search, and explore documentation"

    def test_default_primary_color(self):
        config = BrandingConfig()
        assert config.primary_color == "#3b82f6"

    def test_default_show_powered_by(self):
        config = BrandingConfig()
        assert config.show_powered_by is True

    def test_default_footer_has_link(self):
        config = BrandingConfig()
        assert "Your Docs MCP" in config.footer_html

    def test_optional_fields_are_none(self):
        config = BrandingConfig()
        assert config.logo_url is None
        assert config.logo_text is None
        assert config.favicon_url is None
        assert config.font_family is None
        assert config.font_family_code is None
        assert config.font_cdn_url is None
        assert config.custom_css_url is None
        assert config.custom_css is None
        assert config.custom_js_url is None
        assert config.meta_description is None
        assert config.og_image_url is None


class TestBrandingConfigValidation:
    """Test BrandingConfig field validation."""

    def test_valid_hex_color(self):
        config = BrandingConfig(primary_color="#e11d48")
        assert config.primary_color == "#e11d48"

    def test_hex_color_normalized_to_lowercase(self):
        config = BrandingConfig(primary_color="#E11D48")
        assert config.primary_color == "#e11d48"

    def test_invalid_hex_color_rejected(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            BrandingConfig(primary_color="red")

    def test_short_hex_color_rejected(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            BrandingConfig(primary_color="#fff")

    def test_hex_without_hash_rejected(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            BrandingConfig(primary_color="3b82f6")

    def test_footer_html_allows_safe_html(self):
        config = BrandingConfig(footer_html='<a href="https://example.com">Example</a>')
        assert "Example" in config.footer_html

    def test_footer_html_rejects_script_tag(self):
        with pytest.raises(ValueError, match="disallowed pattern"):
            BrandingConfig(footer_html='<script>alert("xss")</script>')

    def test_footer_html_rejects_javascript_url(self):
        with pytest.raises(ValueError, match="disallowed pattern"):
            BrandingConfig(footer_html='<a href="javascript:alert(1)">click</a>')

    def test_footer_html_rejects_event_handlers(self):
        with pytest.raises(ValueError, match="disallowed pattern"):
            BrandingConfig(footer_html='<div onclick="alert(1)">click</div>')

    def test_custom_css_allows_safe_css(self):
        config = BrandingConfig(custom_css="body { color: red; }")
        assert config.custom_css == "body { color: red; }"

    def test_custom_css_rejects_expression(self):
        with pytest.raises(ValueError, match="disallowed pattern"):
            BrandingConfig(custom_css="body { width: expression(100); }")

    def test_custom_css_rejects_javascript_url(self):
        with pytest.raises(ValueError, match="disallowed pattern"):
            BrandingConfig(custom_css="body { background: url(javascript:alert(1)); }")

    def test_custom_css_none_is_allowed(self):
        config = BrandingConfig(custom_css=None)
        assert config.custom_css is None


class TestBrandingCSSOverrides:
    """Test CSS variable override generation."""

    def test_default_colors_produce_no_overrides(self):
        config = BrandingConfig()
        overrides = config.css_variable_overrides()
        assert overrides == {}

    def test_custom_primary_color_generates_overrides(self):
        config = BrandingConfig(primary_color="#e11d48")
        overrides = config.css_variable_overrides()
        assert "--accent-primary" in overrides
        assert overrides["--accent-primary"] == "#e11d48"
        assert "--accent-hover" in overrides
        assert "--accent-light" in overrides
        assert "--info" in overrides

    def test_custom_font_generates_override(self):
        config = BrandingConfig(font_family="'Roboto', sans-serif")
        overrides = config.css_variable_overrides()
        assert overrides["--font-sans"] == "'Roboto', sans-serif"

    def test_custom_code_font_generates_override(self):
        config = BrandingConfig(font_family_code="'Fira Code', monospace")
        overrides = config.css_variable_overrides()
        assert overrides["--font-mono"] == "'Fira Code', monospace"


class TestBrandingEnvironmentVariables:
    """Test that BrandingConfig reads from environment variables."""

    def test_site_name_from_env(self, monkeypatch):
        monkeypatch.setenv("MCP_DOCS_BRANDING_SITE_NAME", "Env Docs")
        config = BrandingConfig()
        assert config.site_name == "Env Docs"

    def test_primary_color_from_env(self, monkeypatch):
        monkeypatch.setenv("MCP_DOCS_BRANDING_PRIMARY_COLOR", "#e11d48")
        config = BrandingConfig()
        assert config.primary_color == "#e11d48"

    def test_logo_url_from_env(self, monkeypatch):
        monkeypatch.setenv("MCP_DOCS_BRANDING_LOGO_URL", "/static/custom/logo.png")
        config = BrandingConfig()
        assert config.logo_url == "/static/custom/logo.png"

    def test_favicon_url_from_env(self, monkeypatch):
        monkeypatch.setenv("MCP_DOCS_BRANDING_FAVICON_URL", "/favicon.ico")
        config = BrandingConfig()
        assert config.favicon_url == "/favicon.ico"

    def test_site_tagline_from_env(self, monkeypatch):
        monkeypatch.setenv("MCP_DOCS_BRANDING_SITE_TAGLINE", "Custom tagline")
        config = BrandingConfig()
        assert config.site_tagline == "Custom tagline"

    def test_explicit_kwarg_overrides_env(self, monkeypatch):
        monkeypatch.setenv("MCP_DOCS_BRANDING_SITE_NAME", "Env Docs")
        config = BrandingConfig(site_name="Kwarg Docs")
        assert config.site_name == "Kwarg Docs"


class TestServerConfigBranding:
    """Test that ServerConfig includes branding."""

    def test_default_branding(self):
        config = ServerConfig()
        assert isinstance(config.branding, BrandingConfig)
        assert config.branding.site_name == "Documentation"

    def test_custom_static_dir_none_by_default(self):
        config = ServerConfig()
        assert config.custom_static_dir is None

    def test_custom_templates_dir_none_by_default(self):
        config = ServerConfig()
        assert config.custom_templates_dir is None

    def test_custom_static_dir_validates_exists(self, tmp_path):
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        config = ServerConfig(custom_static_dir=str(static_dir))
        assert config.custom_static_dir == static_dir

    def test_custom_static_dir_rejects_nonexistent(self, tmp_path):
        with pytest.raises(ValueError, match="does not exist"):
            ServerConfig(custom_static_dir=str(tmp_path / "nonexistent"))

    def test_custom_templates_dir_validates_exists(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        config = ServerConfig(custom_templates_dir=str(templates_dir))
        assert config.custom_templates_dir == templates_dir


class TestYAMLConfigLoading:
    """Test YAML configuration file loading."""

    def test_apply_branding_from_yaml(self):
        config = ServerConfig()
        yaml_data = {
            "branding": {
                "site_name": "Acme Docs",
                "primary_color": "#e11d48",
            }
        }
        _apply_yaml_config(config, yaml_data)
        assert config.branding.site_name == "Acme Docs"
        assert config.branding.primary_color == "#e11d48"

    def test_apply_server_settings_from_yaml(self):
        config = ServerConfig()
        yaml_data = {
            "server": {
                "host": "0.0.0.0",
                "port": 9000,
                "log_level": "DEBUG",
            }
        }
        _apply_yaml_config(config, yaml_data)
        assert config.web_host == "0.0.0.0"
        assert config.web_port == 9000
        assert config.log_level == "DEBUG"

    def test_apply_sources_from_yaml(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig()
        yaml_data = {
            "sources": [
                {
                    "path": str(docs_dir),
                    "category": "guides",
                    "label": "Guides",
                }
            ]
        }
        _apply_yaml_config(config, yaml_data)
        assert len(config.sources) == 1
        assert config.sources[0].category == "guides"

    def test_yaml_sources_override_docs_root(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        guides_dir = tmp_path / "guides"
        guides_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        yaml_data = {
            "sources": [
                {
                    "path": str(guides_dir),
                    "category": "guides",
                    "label": "Guides",
                }
            ]
        }
        _apply_yaml_config(config, yaml_data)
        # YAML sources take precedence
        assert len(config.sources) == 1
        assert config.sources[0].category == "guides"

    def test_docs_root_still_works_without_yaml(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))
        assert len(config.sources) == 1
        assert config.sources[0].category == "docs"

    def test_load_config_discovers_yaml_file(self, tmp_path, monkeypatch):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        yaml_content = f"""
branding:
  site_name: "Test Docs"
sources:
  - path: {docs_dir}
    category: test
    label: Test
"""
        yaml_file = tmp_path / ".your-docs.yaml"
        yaml_file.write_text(yaml_content)

        monkeypatch.chdir(tmp_path)
        config = load_config()
        assert config.branding.site_name == "Test Docs"

    def test_load_config_works_without_yaml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config = load_config()
        assert config.branding.site_name == "Documentation"

    def test_invalid_yaml_sources_skipped(self, tmp_path):
        config = ServerConfig()
        yaml_data = {
            "sources": [
                {"path": "/nonexistent/path", "category": "bad", "label": "Bad"},
            ]
        }
        _apply_yaml_config(config, yaml_data)
        # Invalid source should be skipped, fall back to docs_root
        assert len(config.sources) == 0

    def test_empty_yaml_data_is_safe(self):
        config = ServerConfig()
        _apply_yaml_config(config, {})
        assert config.branding.site_name == "Documentation"

    def test_custom_static_dir_from_yaml(self, tmp_path):
        static_dir = tmp_path / "custom_static"
        static_dir.mkdir()

        config = ServerConfig()
        yaml_data = {"custom_static_dir": str(static_dir)}
        _apply_yaml_config(config, yaml_data)
        assert config.custom_static_dir == static_dir

    def test_enable_pdf_from_yaml(self):
        config = ServerConfig()
        yaml_data = {"server": {"enable_pdf_generation": True}}
        _apply_yaml_config(config, yaml_data)
        assert config.enable_pdf_generation is True

    def test_enable_mcp_transport_from_yaml(self):
        config = ServerConfig()
        yaml_data = {"server": {"enable_mcp_transport": False}}
        _apply_yaml_config(config, yaml_data)
        assert config.enable_mcp_transport is False


class TestFeatureFlags:
    """Test feature flag configuration."""

    def test_pdf_generation_disabled_by_default(self):
        config = ServerConfig()
        assert config.enable_pdf_generation is False

    def test_pdf_generation_enabled_via_kwarg(self):
        config = ServerConfig(enable_pdf_generation=True)
        assert config.enable_pdf_generation is True

    def test_mcp_transport_enabled_by_default(self):
        config = ServerConfig()
        assert config.enable_mcp_transport is True

    def test_mcp_transport_disabled_via_kwarg(self):
        config = ServerConfig(enable_mcp_transport=False)
        assert config.enable_mcp_transport is False


class TestToolDefinitionsPDFGating:
    """Test that get_tool_definitions gates PDF tool correctly."""

    def test_pdf_tool_excluded_by_default(self):
        from docs_mcp.mcp.handlers.registry import get_tool_definitions

        tools = get_tool_definitions()
        names = [t.name for t in tools]
        assert "generate_pdf_release" not in names

    def test_pdf_tool_included_when_enabled(self):
        from docs_mcp.mcp.handlers.registry import get_tool_definitions

        tools = get_tool_definitions(enable_pdf=True)
        names = [t.name for t in tools]
        assert "generate_pdf_release" in names

    def test_base_tools_always_present(self):
        from docs_mcp.mcp.handlers.registry import get_tool_definitions

        tools = get_tool_definitions()
        names = [t.name for t in tools]
        assert "search_documentation" in names
        assert "navigate_to" in names
        assert "get_table_of_contents" in names
        assert "get_document" in names
        assert "get_all_tags" in names
        assert "search_by_tags" in names

    def test_tool_count_without_pdf(self):
        from docs_mcp.mcp.handlers.registry import get_tool_definitions

        tools = get_tool_definitions()
        assert len(tools) == 6

    def test_tool_count_with_pdf(self):
        from docs_mcp.mcp.handlers.registry import get_tool_definitions

        tools = get_tool_definitions(enable_pdf=True)
        assert len(tools) == 7
