---
paths:
  - "docs_mcp/services/**"
---

# Services Module Rules

- Use async/await for ALL I/O operations (file reads, network, database)
- Use specific exception types — never bare `except:` or `except Exception:`
- Services must be independently testable via dependency injection
- Use `docs_mcp.utils.logger` for structured logging at appropriate levels
- Follow existing service patterns — see `cache.py` and `search.py` as reference
- Each service should have a clear single responsibility
- Public methods must have type hints on parameters and return values
- Return Pydantic models from service methods, not raw dicts
- Cache expensive operations using the cache service where appropriate
- Performance targets: <2s retrieval, <3s search, <500ms navigation
