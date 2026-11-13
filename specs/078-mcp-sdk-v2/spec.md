# MCP SDK 2 migration

Use published MCP SDK 2.3.0 or newer within major 2. Python 3.11 is the minimum
supported interpreter. Preserve public CLI commands, stdio and SSE endpoints,
six standard tools plus gated PDF, JSON text payloads, resource URIs, and schemas.
Invalid tool inputs and raised tool failures remain error-flagged tool results.
Categories populated after construction must be visible to registered handlers.
Web-only mode must not run stdio. Search and hidden-path fixes remain separate.

Acceptance: real SDK clients complete tools/resources round trips over stdio and
SSE, including legacy initialization, reconnects, and invalid arguments. Built
wheels install and launch successfully; unit/integration/contract suites meet the
80% coverage gate. Both package manifests advertise the interpreter minimum.
