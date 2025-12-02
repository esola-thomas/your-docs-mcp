"""Configuration management using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Default to False for MCP safety - use your-docs-web or your-docs-server for web access
    enable_web_server: bool = False
    web_host: str = "127.0.0.1"
    web_port: int = 8123

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

    @property
    def sources(self) -> list[SourceConfig]:
        """Get list of documentation sources.

        Returns a list of SourceConfig objects, either from:
        1. Multi-source config file (if specified)
        2. Single docs_root (if specified)
        3. Empty list (if neither specified)
        """
        # TODO: Implement multi-source config file loading
        # For now, just return single source from docs_root
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


def load_config() -> ServerConfig:
    """Load server configuration from environment and files."""
    return ServerConfig()
