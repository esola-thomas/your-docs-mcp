---
title: MCP SDK 2 Migration
category: Guides
tags: [mcp, installation, migration]
order: 10
---

# MCP SDK 2 migration

Version 2.0.0 of both `your-docs-mcp` and `your-docs-server` requires Python 3.11+
and MCP SDK `>=2.3.0,<3`. Python 3.10 deployments must upgrade their interpreter
before upgrading these packages. The previous release remains available for rollback.

```bash
pip install --upgrade "your-docs-mcp>=2,<3"
# For the web UI, REST API, and MCP SSE endpoint:
pip install --upgrade "your-docs-server>=2,<3"
```

Existing commands, configuration variables, tool names, schemas, JSON text payloads,
resource URIs, and stdio/SSE endpoints are preserved. `your-docs-web` starts only
the web server and does not start a stdio session. Streamable HTTP is outside
this migration's scope.

The SDK adapter explicitly validates tool arguments and wraps results and raised
failures. Direct Python consumers of the old internal `register_mcp_handlers`
helper should use `create_mcp_server(documents, categories, config)` instead.

Install the core package before the convenience package when testing local wheels.
Run `python scripts/smoke_install.py` from the repository to check the installed
stdio executable; add `--web` when server extras are installed to check all three
executables. The smoke check uses a temporary corpus and exits nonzero on failure.

The hidden-path and search-ranking reports in issue #78 are separate fixes.
