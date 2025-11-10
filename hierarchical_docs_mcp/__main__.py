"""CLI entry point for the Hierarchical Documentation MCP Server."""

import asyncio
import sys

from hierarchical_docs_mcp.config import load_config
from hierarchical_docs_mcp.server import serve
from hierarchical_docs_mcp.utils.logger import setup_logging


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Load configuration
        config = load_config()

        # Setup logging
        setup_logging(config.log_level)

        # Validate configuration
        if not config.sources and not config.docs_root:
            print("Error: No documentation sources configured.", file=sys.stderr)
            print(
                "Please set DOCS_ROOT environment variable or provide a config file.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Run server
        asyncio.run(serve(config))

    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
