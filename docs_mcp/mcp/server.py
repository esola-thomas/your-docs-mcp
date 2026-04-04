"""Main MCP server implementation."""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server

from docs_mcp.core.config import ServerConfig
from docs_mcp.core.models.document import Document
from docs_mcp.core.models.navigation import Category
from docs_mcp.core.services.hierarchy import build_category_tree
from docs_mcp.core.services.markdown import scan_markdown_files
from docs_mcp.core.utils.logger import logger
from docs_mcp.mcp.handlers.registry import register_mcp_handlers


def _get_vector_store():  # type: ignore[no-untyped-def]
    """Lazy import vector store."""
    try:
        from docs_mcp.vector.search import get_vector_store

        return get_vector_store()
    except ImportError:
        return None


class DocumentationMCPServer:
    """Hierarchical Documentation MCP Server."""

    def __init__(self, config: ServerConfig) -> None:
        """Initialize the server."""
        self.config = config
        self.server = Server("hierarchical-docs-mcp")
        self.documents: list[Document] = []
        self.categories: dict[str, Category] = {}

        register_mcp_handlers(self.server, self.documents, self.categories, self.config)

    async def initialize(self) -> None:
        """Initialize the server by loading documentation."""
        logger.info("Initializing documentation server...")

        for source in self.config.sources:
            logger.info(f"Loading documentation from: {source.path}")

            try:
                docs = scan_markdown_files(
                    source_path=source.path,
                    doc_root=source.path,
                    recursive=source.recursive,
                    include_patterns=source.include_patterns,
                    exclude_patterns=source.exclude_patterns,
                    allow_hidden=self.config.allow_hidden,
                )

                self.documents.extend(docs)
                logger.info(f"Loaded {len(docs)} documents from {source.path}")

            except Exception as e:
                logger.error(f"Failed to load documentation from {source.path}: {e}")

        if self.documents:
            self.categories = build_category_tree(self.documents)
            logger.info(f"Built category tree with {len(self.categories)} categories")

            try:
                vs = _get_vector_store()
                if vs:
                    vs.add_documents(self.documents)
            except Exception as e:
                logger.error(f"Failed to index documents: {e}")

        logger.info(
            f"Initialization complete: {len(self.documents)} documents, "
            f"{len(self.categories)} categories"
        )

    async def run(self) -> None:
        """Run the server with stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def serve(config: ServerConfig) -> None:
    """Create and run the MCP server."""
    server = DocumentationMCPServer(config)
    await server.initialize()
    await server.run()


async def serve_both(config: ServerConfig) -> None:
    """Create and run both MCP and web servers concurrently."""
    import uvicorn

    from docs_mcp.web.app import DocumentationWebServer

    mcp_server = DocumentationMCPServer(config)
    await mcp_server.initialize()

    async def run_web_server() -> None:
        web_server = DocumentationWebServer(
            config=config,
            documents=mcp_server.documents,
            categories=mcp_server.categories,
        )

        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": False,
                },
            },
            "handlers": {
                "stderr": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["stderr"], "level": "WARNING", "propagate": False},
                "uvicorn.error": {"handlers": ["stderr"], "level": "WARNING", "propagate": False},
                "uvicorn.access": {
                    "handlers": ["stderr"],
                    "level": "WARNING",
                    "propagate": False,
                },
            },
        }

        uvicorn_config = uvicorn.Config(
            app=web_server.app,
            host=config.web_host,
            port=config.web_port,
            log_config=log_config,
            access_log=False,
        )

        uvicorn_server = uvicorn.Server(uvicorn_config)
        await uvicorn_server.serve()

    async def run_mcp_server() -> None:
        await mcp_server.run()

    tasks = []

    if config.enable_web_server:
        logger.info(f"Starting web server on {config.web_host}:{config.web_port}")
        tasks.append(asyncio.create_task(run_web_server()))
        await asyncio.sleep(0.1)

    tasks.append(asyncio.create_task(run_mcp_server()))

    await asyncio.gather(*tasks)
