"""Unit tests for configuration management."""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError

from hierarchical_docs_mcp.config import ServerConfig, SourceConfig, load_config


class TestSourceConfig:
    """Test SourceConfig model."""

    def test_source_config_creation_with_valid_path(self, tmp_path):
        """Test creation of source config with valid path."""
        # Create a test directory
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        config = SourceConfig(
            path=test_dir,
            category="guides",
            label="User Guides",
        )

        assert config.path == test_dir.resolve()
        assert config.category == "guides"
        assert config.label == "User Guides"
        assert config.recursive is True
        assert "*.md" in config.include_patterns
        assert "*.mdx" in config.include_patterns
        assert ".git" in config.exclude_patterns

    def test_source_config_with_custom_patterns(self, tmp_path):
        """Test source config with custom include/exclude patterns."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        config = SourceConfig(
            path=test_dir,
            category="api",
            label="API Docs",
            include_patterns=["*.yaml", "*.yml"],
            exclude_patterns=["temp", "*.tmp"],
            format_type="openapi",
        )

        assert config.include_patterns == ["*.yaml", "*.yml"]
        assert config.exclude_patterns == ["temp", "*.tmp"]
        assert config.format_type == "openapi"

    def test_source_config_nonexistent_path_raises_error(self, tmp_path):
        """Test that nonexistent path raises validation error."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(ValidationError) as exc_info:
            SourceConfig(
                path=nonexistent,
                category="test",
                label="Test",
            )

        assert "does not exist" in str(exc_info.value).lower()

    def test_source_config_file_path_raises_error(self, tmp_path):
        """Test that file path (not directory) raises validation error."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        with pytest.raises(ValidationError) as exc_info:
            SourceConfig(
                path=test_file,
                category="test",
                label="Test",
            )

        assert "not a directory" in str(exc_info.value).lower()

    def test_source_config_expanduser_resolves_tilde(self, tmp_path, monkeypatch):
        """Test that path with ~ is expanded."""
        # Create a test directory in tmp_path
        test_dir = tmp_path / "test_docs"
        test_dir.mkdir()

        # Mock expanduser to return our test directory
        def mock_expanduser(self):
            if str(self).startswith("~"):
                return test_dir
            return self

        monkeypatch.setattr(Path, "expanduser", mock_expanduser)

        config = SourceConfig(
            path=Path("~/test_docs"),
            category="test",
            label="Test",
        )

        assert config.path == test_dir.resolve()


class TestServerConfig:
    """Test ServerConfig model."""

    def test_server_config_defaults(self):
        """Test server config with default values."""
        config = ServerConfig()

        assert config.docs_root is None
        assert config.config_file is None
        assert config.openapi_specs == []
        assert config.cache_ttl == 3600
        assert config.max_cache_mb == 500
        assert config.search_limit == 10
        assert config.log_level == "INFO"
        assert config.watch_files is True
        assert config.max_depth == 10
        assert config.allow_hidden is False
        assert config.audit_log is True

    def test_server_config_with_docs_root(self, tmp_path):
        """Test server config with docs_root set."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=str(docs_dir))

        assert config.docs_root == docs_dir.resolve()

    def test_server_config_docs_root_nonexistent_raises_error(self, tmp_path):
        """Test that nonexistent docs_root raises validation error."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(docs_root=str(nonexistent))

        assert "does not exist" in str(exc_info.value).lower()

    def test_server_config_docs_root_not_directory_raises_error(self, tmp_path):
        """Test that file path for docs_root raises validation error."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(docs_root=str(test_file))

        assert "not a directory" in str(exc_info.value).lower()

    def test_server_config_from_env_vars(self, tmp_path, monkeypatch):
        """Test loading config from environment variables."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        monkeypatch.setenv("MCP_DOCS_DOCS_ROOT", str(docs_dir))
        monkeypatch.setenv("MCP_DOCS_CACHE_TTL", "7200")
        monkeypatch.setenv("MCP_DOCS_SEARCH_LIMIT", "20")
        monkeypatch.setenv("MCP_DOCS_LOG_LEVEL", "DEBUG")

        config = ServerConfig()

        assert config.docs_root == docs_dir.resolve()
        assert config.cache_ttl == 7200
        assert config.search_limit == 20
        assert config.log_level == "DEBUG"

    def test_server_config_openapi_specs_from_string(self, tmp_path):
        """Test parsing OpenAPI specs from comma-separated string."""
        spec1 = tmp_path / "api1.yaml"
        spec2 = tmp_path / "api2.yaml"
        spec1.write_text("openapi: 3.0.0")
        spec2.write_text("openapi: 3.0.0")

        config = ServerConfig(
            openapi_specs=f"{spec1},{spec2}"
        )

        assert len(config.openapi_specs) == 2
        assert spec1.resolve() in config.openapi_specs
        assert spec2.resolve() in config.openapi_specs

    def test_server_config_openapi_specs_empty_string(self):
        """Test that empty string for openapi_specs returns empty list."""
        config = ServerConfig(openapi_specs="")

        assert config.openapi_specs == []

    def test_server_config_openapi_specs_from_list(self, tmp_path):
        """Test OpenAPI specs from list of paths."""
        spec1 = tmp_path / "api1.yaml"
        spec2 = tmp_path / "api2.yaml"
        spec1.write_text("openapi: 3.0.0")
        spec2.write_text("openapi: 3.0.0")

        config = ServerConfig(openapi_specs=[spec1, spec2])

        assert len(config.openapi_specs) == 2

    def test_server_config_config_file_nonexistent_raises_error(self, tmp_path):
        """Test that nonexistent config_file raises validation error."""
        nonexistent = tmp_path / "config.yaml"

        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(config_file=nonexistent)

        assert "does not exist" in str(exc_info.value).lower()

    def test_server_config_config_file_valid(self, tmp_path):
        """Test valid config_file path."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("sources: []")

        config = ServerConfig(config_file=config_file)

        assert config.config_file == config_file.resolve()

    def test_server_config_sources_with_docs_root(self, tmp_path):
        """Test sources property returns SourceConfig from docs_root."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config = ServerConfig(docs_root=docs_dir)
        sources = config.sources

        assert len(sources) == 1
        assert sources[0].path == docs_dir.resolve()
        assert sources[0].category == "docs"
        assert sources[0].label == "Documentation"

    def test_server_config_sources_without_docs_root(self):
        """Test sources property returns empty list without docs_root."""
        config = ServerConfig()
        sources = config.sources

        assert sources == []

    def test_server_config_custom_values(self):
        """Test server config with custom values."""
        config = ServerConfig(
            cache_ttl=1800,
            max_cache_mb=1000,
            search_limit=50,
            log_level="WARNING",
            watch_files=False,
            max_depth=5,
            allow_hidden=True,
            audit_log=False,
        )

        assert config.cache_ttl == 1800
        assert config.max_cache_mb == 1000
        assert config.search_limit == 50
        assert config.log_level == "WARNING"
        assert config.watch_files is False
        assert config.max_depth == 5
        assert config.allow_hidden is True
        assert config.audit_log is False


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_returns_server_config(self):
        """Test that load_config returns a ServerConfig instance."""
        config = load_config()

        assert isinstance(config, ServerConfig)

    def test_load_config_with_env_vars(self, tmp_path, monkeypatch):
        """Test that load_config loads from environment variables."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        monkeypatch.setenv("MCP_DOCS_DOCS_ROOT", str(docs_dir))
        monkeypatch.setenv("MCP_DOCS_LOG_LEVEL", "ERROR")

        config = load_config()

        assert config.docs_root == docs_dir.resolve()
        assert config.log_level == "ERROR"

    def test_load_config_legacy_docs_root_env(self, tmp_path, monkeypatch):
        """Test that DOCS_ROOT (without prefix) is loaded correctly."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # The validation_alias allows DOCS_ROOT without the MCP_DOCS_ prefix
        monkeypatch.setenv("DOCS_ROOT", str(docs_dir))

        config = load_config()

        assert config.docs_root == docs_dir.resolve()
