"""CLI entry point for the Hierarchical Documentation MCP Server.

Entry Points:
- your-docs-mcp: MCP server only (stdio transport, for AI clients)
- your-docs-web: Web server only (REST API + browser UI)
- your-docs-server: Both MCP and web server concurrently
"""

from __future__ import annotations

import asyncio
import sys

from docs_mcp.config import ServerConfig, load_config
from docs_mcp.server import serve, serve_both, serve_web_only
from docs_mcp.utils.logger import logger, setup_logging


def _validate_config_and_setup() -> ServerConfig:
    """Common setup: load config, setup logging, validate sources.

    Returns:
        Validated ServerConfig instance
    """

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
    """Entry point for MCP server only (your-docs-mcp command).

    This runs the MCP server with stdio transport for AI clients like
    Claude Desktop or VS Code Copilot. No web server is started.
    """
    try:
        config = _validate_config_and_setup()

        # Force disable web server for pure MCP mode
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
    """Entry point for web server only (your-docs-web command).

    This runs the REST API and browser UI without the MCP stdio server.
    Useful for standalone documentation browsing or API access.
    """
    try:
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
    """Entry point for both servers (your-docs-server command).

    This runs both the MCP server (stdio) and web server concurrently.
    The MCP server uses stdio transport, web server uses HTTP.

    Note: When using with MCP clients, prefer 'your-docs-mcp' command
    to avoid potential stdio conflicts with web server logging.
    """
    try:
        config = _validate_config_and_setup()

        # Always enable web server for your-docs-server command
        config.enable_web_server = True

        logger.info("Starting Markdown MCP Server")
        logger.info(
            f"Web interface will be available at http://{config.web_host}:{config.web_port}"
        )

        # Run MCP server (with web server enabled)
        asyncio.run(serve_both(config))

    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
