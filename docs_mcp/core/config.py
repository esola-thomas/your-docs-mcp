"""Configuration management using pydantic-settings."""

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Patterns considered dangerous in user-provided HTML
_DANGEROUS_HTML_PATTERNS = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
]

# Patterns considered dangerous in user-provided CSS
_DANGEROUS_CSS_PATTERNS = [
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"url\s*\(\s*['\"]?\s*javascript:", re.IGNORECASE),
]


class BrandingConfig(BaseSettings):
    """White-label branding configuration.

    All fields have sensible defaults so the server works out-of-the-box
    with zero branding configuration.

    Supports environment variables with prefix MCP_DOCS_BRANDING_ for
    Docker-friendly configuration (e.g. MCP_DOCS_BRANDING_SITE_NAME).
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_DOCS_BRANDING_",
        extra="ignore",
    )

    # Identity
    site_name: str = "Documentation"
    site_tagline: str = "Browse, search, and explore documentation"
    logo_url: str | None = None
    logo_text: str | None = None  # Falls back to site_name if None
    favicon_url: str | None = None

    # Footer
    footer_html: str = (
        'Powered by <a href="https://github.com/esola-thomas/your-docs-mcp"'
        ' rel="noopener noreferrer">Your Docs MCP</a>'
    )
    show_powered_by: bool = True

    # Colors
    primary_color: str = "#3b82f6"

    # Typography
    font_family: str | None = None
    font_family_code: str | None = None
    font_cdn_url: str | None = None

    # Custom CSS/JS injection
    custom_css_url: str | None = None
    custom_css: str | None = None
    custom_js_url: str | None = None

    # SEO
    meta_description: str | None = None
    og_image_url: str | None = None

    @field_validator("primary_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Ensure primary_color is a valid 6-digit hex color."""
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError(f"Invalid hex color: {v}. Must be format #RRGGBB")
        return v.lower()

    @field_validator("footer_html")
    @classmethod
    def sanitize_footer_html(cls, v: str) -> str:
        """Sanitize footer HTML against XSS patterns."""
        for pattern in _DANGEROUS_HTML_PATTERNS:
            if pattern.search(v):
                raise ValueError(f"footer_html contains disallowed pattern: {pattern.pattern}")
        return v

    @field_validator("custom_css")
    @classmethod
    def sanitize_custom_css(cls, v: str | None) -> str | None:
        """Sanitize custom CSS against injection patterns."""
        if v is None:
            return None
        for pattern in _DANGEROUS_CSS_PATTERNS:
            if pattern.search(v):
                raise ValueError(f"custom_css contains disallowed pattern: {pattern.pattern}")
        return v

    def css_variable_overrides(self) -> dict[str, str]:
        """Generate CSS custom property overrides from this config.

        Returns:
            Dict of CSS variable name -> value (empty if all defaults)
        """
        from docs_mcp.web.theme import generate_css_overrides

        return generate_css_overrides(
            primary_color=self.primary_color,
            font_family=self.font_family,
            font_family_code=self.font_family_code,
        )


class SourceConfig(BaseSettings):
    """Configuration for a single documentation source."""

    path: Path
    category: str
    label: str
    recursive: bool = True
    include_patterns: list[str] = Field(default_factory=lambda: ["*.md", "*.mdx"])
    exclude_patterns: list[str] = Field(default_factory=lambda: ["node_modules", ".git", "_*"])
    format_type: Literal["markdown", "openapi"] = "markdown"

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        """Ensure path is absolute and exists."""
        path = v.expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Documentation path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Documentation path is not a directory: {path}")
        return path


class ServerConfig(BaseSettings):
    """Main server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_DOCS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Documentation root (single source mode)
    docs_root: Path | None = Field(
        None,
        validation_alias=AliasChoices("docs_root", "DOCS_ROOT", "MCP_DOCS_DOCS_ROOT"),
    )

    # Multi-source configuration file
    config_file: Path | None = None

    # OpenAPI specification files
    openapi_specs: list[Path] = Field(default_factory=list)

    # Cache configuration
    cache_ttl: int = 3600  # 1 hour
    max_cache_mb: int = 500

    # Search configuration
    search_limit: int = 10

    # Logging configuration
    log_level: str = "INFO"

    # File watching
    watch_files: bool = True

    # Directory traversal limits
    max_depth: int = 10

    # Security settings
    allow_hidden: bool = False
    audit_log: bool = True

    # Web server configuration
    # Default to False for MCP safety - use your-docs-server for web access
    enable_web_server: bool = False
    enable_mcp_transport: bool = True
    web_host: str = "127.0.0.1"
    web_port: int = 8123

    # Feature flags
    enable_pdf_generation: bool = False

    # GitHub repo for "Edit on GitHub" links
    github_repo: str = Field(
        "",
        validation_alias=AliasChoices("github_repo", "DOCS_GITHUB_REPO", "MCP_DOCS_GITHUB_REPO"),
    )

    # Base URL for canonical URLs and sitemap
    base_url: str = Field(
        "",
        validation_alias=AliasChoices("base_url", "DOCS_BASE_URL", "MCP_DOCS_BASE_URL"),
    )

    # White-label branding
    branding: BrandingConfig = Field(default_factory=BrandingConfig)

    # Custom asset directories
    custom_static_dir: Path | None = None
    custom_templates_dir: Path | None = None

    # Internal: sources loaded from YAML config
    _yaml_sources: list[SourceConfig] | None = None

    @field_validator("docs_root")
    @classmethod
    def validate_docs_root(cls, v: Path | None) -> Path | None:
        """Validate and resolve documentation root path."""
        if v is None:
            return None
        path = v.expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Documentation root does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Documentation root is not a directory: {path}")
        return path

    @field_validator("openapi_specs", mode="before")
    @classmethod
    def parse_openapi_specs(cls, v: str | list[Path]) -> list[Path]:
        """Parse comma-separated OpenAPI spec paths."""
        if isinstance(v, str):
            if not v:
                return []
            paths = [Path(p.strip()).expanduser().resolve() for p in v.split(",")]
            return paths
        return v

    @field_validator("config_file")
    @classmethod
    def validate_config_file(cls, v: Path | None) -> Path | None:
        """Validate configuration file path."""
        if v is None:
            return None
        path = v.expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Configuration file does not exist: {path}")
        return path

    @field_validator("custom_static_dir")
    @classmethod
    def validate_custom_static_dir(cls, v: Path | None) -> Path | None:
        """Validate custom static directory exists."""
        if v is None:
            return None
        path = v.expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"Custom static directory does not exist: {path}")
        return path

    @field_validator("custom_templates_dir")
    @classmethod
    def validate_custom_templates_dir(cls, v: Path | None) -> Path | None:
        """Validate custom templates directory exists."""
        if v is None:
            return None
        path = v.expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"Custom templates directory does not exist: {path}")
        return path

    @property
    def sources(self) -> list[SourceConfig]:
        """Get list of documentation sources.

        Priority:
        1. Sources loaded from YAML config file
        2. Single source from docs_root
        3. Empty list
        """
        if self._yaml_sources is not None:
            return self._yaml_sources
        if self.docs_root:
            return [
                SourceConfig(
                    path=self.docs_root,
                    category="docs",
                    label="Documentation",
                    recursive=True,
                )
            ]
        return []


def _discover_config_file() -> Path | None:
    """Auto-discover a YAML config file in the current working directory."""
    cwd = Path.cwd()
    for name in (".your-docs.yaml", ".your-docs.yml", "your-docs.yaml", "your-docs.yml"):
        path = cwd / name
        if path.is_file():
            return path
    return None


def _apply_yaml_config(config: ServerConfig, yaml_data: dict[str, Any]) -> None:
    """Apply YAML config values to an existing ServerConfig.

    Only applies values that were not already set via environment variables.
    Mutates the config in place.

    Args:
        config: ServerConfig instance to update
        yaml_data: Parsed YAML dictionary
    """
    # Apply branding section
    branding_data = yaml_data.get("branding")
    if branding_data and isinstance(branding_data, dict):
        config.branding = BrandingConfig(**branding_data)

    # Apply server section (only fields not set by env vars)
    server_data = yaml_data.get("server")
    if server_data and isinstance(server_data, dict):
        field_map = {
            "host": "web_host",
            "port": "web_port",
            "log_level": "log_level",
            "search_limit": "search_limit",
            "cache_ttl": "cache_ttl",
            "max_cache_mb": "max_cache_mb",
            "watch_files": "watch_files",
            "max_depth": "max_depth",
            "allow_hidden": "allow_hidden",
            "audit_log": "audit_log",
            "github_repo": "github_repo",
            "base_url": "base_url",
            "enable_pdf_generation": "enable_pdf_generation",
            "enable_mcp_transport": "enable_mcp_transport",
        }
        for yaml_key, config_attr in field_map.items():
            if yaml_key in server_data:
                setattr(config, config_attr, server_data[yaml_key])

    # Apply custom directories
    if "custom_static_dir" in yaml_data:
        path = Path(yaml_data["custom_static_dir"]).expanduser().resolve()
        if path.is_dir():
            config.custom_static_dir = path

    if "custom_templates_dir" in yaml_data:
        path = Path(yaml_data["custom_templates_dir"]).expanduser().resolve()
        if path.is_dir():
            config.custom_templates_dir = path

    # Apply sources section
    sources_data = yaml_data.get("sources")
    if sources_data and isinstance(sources_data, list):
        yaml_sources = []
        for src in sources_data:
            if isinstance(src, dict) and "path" in src:
                try:
                    yaml_sources.append(SourceConfig(**src))
                except Exception:
                    pass  # Skip invalid sources, log in production
        if yaml_sources:
            config._yaml_sources = yaml_sources


def load_config() -> ServerConfig:
    """Load server configuration from environment, YAML file, and defaults.

    Priority: environment variables > YAML config > defaults
    """
    config = ServerConfig()

    # Find config file: explicit path > auto-discovery
    config_path = config.config_file or _discover_config_file()

    if config_path and config_path.is_file():
        try:
            with open(config_path) as f:
                yaml_data = yaml.safe_load(f)
            if yaml_data and isinstance(yaml_data, dict):
                _apply_yaml_config(config, yaml_data)
        except Exception:
            pass  # Config file parsing errors are non-fatal

    return config
