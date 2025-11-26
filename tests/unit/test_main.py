"""Unit tests for CLI entry point."""

from unittest.mock import AsyncMock, patch

import pytest

from docs_mcp.__main__ import main
from docs_mcp.config import ServerConfig


class TestMain:
    """Test main CLI entry point."""

    def test_main_exits_if_no_docs_root(self, capsys):
        """Test that main exits with error if no documentation sources configured."""
        # Mock load_config to return config without docs_root
        mock_config = ServerConfig()

        with patch("docs_mcp.__main__.load_config", return_value=mock_config):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "No documentation sources configured" in captured.err

    def test_main_with_valid_config(self, tmp_path):
        """Test main with valid configuration."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        mock_config = ServerConfig(docs_root=str(docs_dir))

        # Mock functions to avoid actually starting the server
        with patch("docs_mcp.__main__.load_config", return_value=mock_config):
            with patch("docs_mcp.__main__.setup_logging"):
                with patch(
                    "docs_mcp.__main__.serve", new_callable=AsyncMock
                ) as mock_serve:
                    try:
                        main()
                    except SystemExit:
                        pass

                    # Verify serve was called (server was started)
                    assert mock_serve.call_count > 0

    def test_main_handles_keyboard_interrupt(self, tmp_path, capsys):
        """Test that main handles KeyboardInterrupt gracefully."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        mock_config = ServerConfig(docs_root=str(docs_dir))

        # Mock serve to raise KeyboardInterrupt
        mock_serve = AsyncMock(side_effect=KeyboardInterrupt)

        with patch("docs_mcp.__main__.load_config", return_value=mock_config):
            with patch("docs_mcp.__main__.setup_logging"):
                with patch("docs_mcp.__main__.serve", mock_serve):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "stopped by user" in captured.err.lower()

    def test_main_handles_general_exception(self, tmp_path, capsys):
        """Test that main handles general exceptions."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        mock_config = ServerConfig(docs_root=str(docs_dir))

        # Mock serve to raise general exception
        mock_serve = AsyncMock(side_effect=Exception("Test error"))

        with patch("docs_mcp.__main__.load_config", return_value=mock_config):
            with patch("docs_mcp.__main__.setup_logging"):
                with patch("docs_mcp.__main__.serve", mock_serve):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Test error" in captured.err

    def test_main_calls_setup_logging(self, tmp_path):
        """Test that main calls setup_logging with correct log level."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        mock_config = ServerConfig(docs_root=str(docs_dir), log_level="DEBUG")

        with patch("docs_mcp.__main__.load_config", return_value=mock_config):
            with patch("docs_mcp.__main__.setup_logging") as mock_setup:
                with patch("docs_mcp.__main__.serve", new_callable=AsyncMock):
                    try:
                        main()
                    except SystemExit:
                        pass

                    mock_setup.assert_called_once_with("DEBUG")

    def test_main_loads_config(self, tmp_path):
        """Test that main loads configuration."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        mock_config = ServerConfig(docs_root=str(docs_dir))

        with patch(
            "docs_mcp.__main__.load_config", return_value=mock_config
        ) as mock_load:
            with patch("docs_mcp.__main__.setup_logging"):
                with patch("docs_mcp.__main__.serve", new_callable=AsyncMock):
                    try:
                        main()
                    except SystemExit:
                        pass

                    mock_load.assert_called_once()

    def test_main_validation_error_message(self, capsys):
        """Test that validation error messages are displayed."""
        # Mock load_config to raise ValueError
        with patch(
            "docs_mcp.__main__.load_config",
            side_effect=ValueError("Invalid path"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Invalid path" in captured.err


class TestMainModuleExecution:
    """Test __main__ module execution."""

    def test_main_is_callable(self):
        """Test that main function is callable."""
        assert callable(main)

    def test_main_function_signature(self):
        """Test that main has correct signature (no parameters)."""
        import inspect

        sig = inspect.signature(main)
        assert len(sig.parameters) == 0
        assert sig.return_annotation in (None, type(None), inspect.Signature.empty)
