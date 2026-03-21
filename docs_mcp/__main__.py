"""CLI entry point for the Hierarchical Documentation MCP Server.

Entry Points:
- your-docs-mcp: MCP server only (stdio transport, for AI clients)
- your-docs-web: Web server only (REST API + browser UI)
- your-docs-server: Both MCP and web server concurrently
"""

from __future__ import annotations

import asyncio
import sys


def _validate_config_and_setup():  # type: ignore[no-untyped-def]
    """Common setup: load config, setup logging, validate sources.

    Returns:
        Validated ServerConfig instance
    """
    from docs_mcp.core.config import load_config
    from docs_mcp.core.utils.logger import setup_logging

    config = load_config()
    setup_logging(config.log_level)

    if not config.sources and not config.docs_root:
        print("Error: No documentation sources configured.", file=sys.stderr)
        print(
            "Please set DOCS_ROOT environment variable or provide a config file.",
            file=sys.stderr,
        )
        sys.exit(1)

    return config


def mcp_main() -> None:
    """Entry point for MCP server only (your-docs-mcp command)."""
    try:
        from docs_mcp.mcp.server import serve
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        print("Reinstall with: pip install your-docs-mcp", file=sys.stderr)
        sys.exit(1)

    try:
        from docs_mcp.core.utils.logger import logger

        config = _validate_config_and_setup()
        config.enable_web_server = False

        logger.info("Starting MCP Server (stdio transport)")
        asyncio.run(serve(config))

    except KeyboardInterrupt:
        print("\nMCP Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def web_main() -> None:
    """Entry point for web server only (your-docs-web command)."""
    try:
        from docs_mcp.web.app import DocumentationWebServer  # noqa: F401
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        print("Install with: pip install your-docs-mcp[web]", file=sys.stderr)
        sys.exit(1)

    try:
        from docs_mcp.core.utils.logger import logger
        from docs_mcp.mcp.server import serve_web_only

        config = _validate_config_and_setup()

        logger.info("Starting Web Server only")
        logger.info(f"Web interface available at http://{config.web_host}:{config.web_port}")

        asyncio.run(serve_web_only(config))

    except KeyboardInterrupt:
        print("\nWeb Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Entry point for both servers (your-docs-server command)."""
    try:
        from docs_mcp.mcp.server import serve_both  # noqa: F401
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        print(
            "Install with: pip install your-docs-server  (or: pip install your-docs-mcp[server])",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from docs_mcp.core.utils.logger import logger

        config = _validate_config_and_setup()
        config.enable_web_server = True

        logger.info("Starting Markdown MCP Server")
        logger.info(
            f"Web interface will be available at http://{config.web_host}:{config.web_port}"
        )

        asyncio.run(serve_both(config))

    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
