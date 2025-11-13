# Research: Hierarchical Documentation MCP Server

**Feature**: Hierarchical Documentation MCP Server  
**Date**: November 4, 2025  
**Purpose**: Resolve technical uncertainties identified in Technical Context

## Research Tasks

### 1. OpenAPI Parser Library Selection

**Decision**: Use `openapi-spec-validator` + `prance` combination

**Rationale**:
- `openapi-spec-validator`: Industry-standard validator, actively maintained, supports OpenAPI 3.0 and 3.1
- `prance`: Excellent for resolving $ref references and flattening specs for easier traversal
- Combination provides both validation and usable parsed structure
- Both libraries are mature with strong community adoption

**Alternatives Considered**:
- `openapi-core`: More focused on request/response validation for running APIs, overkill for documentation parsing
- Manual parsing: Would require reimplementing $ref resolution and validation logic
- `swagger-parser`: Primarily JavaScript, Python port not as well maintained

**Implementation Approach**:
```python
from openapi_spec_validator import validate_spec
from prance import ResolvingParser

# Validate spec first
validate_spec(spec_dict)

# Parse with reference resolution
parser = ResolvingParser(spec_path)
resolved_spec = parser.specification
```

---

### 2. Search and Indexing Strategy

**Decision**: Start with simple regex-based search, add whoosh if performance requires

**Rationale**:
- For documentation sets <10GB, regex search with smart caching is sufficient
- Python's `re` module is fast enough for <5000 documents (meets SC-002: <3s)
- Avoid premature optimization - add complexity only if performance testing shows need
- Whoosh is pure Python, easy to add later without changing interfaces

**Alternatives Considered**:
- `whoosh`: Full-text search library, pure Python. Good fallback if regex insufficient.
- `tantivy-py`: Rust-based, extremely fast but adds external dependency and complexity
- `elasticsearch`/`opensearch`: Server-based solutions, massive overkill for local documentation
- `sqlite FTS5`: Requires database setup, against file-system-only constraint

**Implementation Approach**:
```python
# Phase 1: Simple regex with caching
import re
from functools import lru_cache

@lru_cache(maxsize=1000)
def search_content(pattern: str, category: str = None):
    compiled = re.compile(pattern, re.IGNORECASE)
    results = []
    for file in get_markdown_files(category):
        content = read_cached(file)
        if compiled.search(content):
            results.append(create_result(file, content, pattern))
    return results

# Phase 2 (if needed): Add whoosh indexing
# from whoosh.index import create_in
# from whoosh.qparser import QueryParser
```

**Performance Strategy**:
- Implement regex first with comprehensive caching
- Add performance tests with 5000 document corpus
- If <3s threshold not met, migrate to whoosh
- Keep interface identical (search function signature unchanged)

---

### 3. File Watching for Cache Invalidation

**Decision**: Use `watchdog` library

**Rationale**:
- Cross-platform (Linux inotify, macOS FSEvents, Windows ReadDirectoryChangesW)
- Mature and actively maintained (10+ years, 6k+ stars)
- Clean API with both synchronous and asynchronous support
- Handles edge cases like rapid file changes, directory moves
- Used by major Python projects (pytest-watch, sphinx-autobuild)

**Alternatives Considered**:
- `inotify-simple`: Linux-only, doesn't meet cross-platform requirement
- Manual polling: Inefficient, high CPU usage, misses rapid changes
- No watching: Requires manual cache clearing, poor UX
- `pyinotify`: Deprecated, watchdog is successor

**Implementation Approach**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DocChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.md', '.mdx', '.yaml', '.json')):
            cache.invalidate(event.src_path)
    
    def on_created(self, event):
        if event.src_path.endswith(('.md', '.mdx', '.yaml', '.json')):
            cache.invalidate_category(os.path.dirname(event.src_path))

observer = Observer()
observer.schedule(DocChangeHandler(), docs_root, recursive=True)
observer.start()
```

**Cache Invalidation Strategy**:
- File modified → invalidate that file's cache entry
- File created/deleted → invalidate parent directory listing cache
- Directory created/deleted → invalidate parent and ancestor listings
- Configurable: Can disable watching for read-only documentation

---

## Additional Research Areas

### 4. MCP SDK Usage Patterns

**Decision**: Use official `mcp` Python SDK with server class approach

**Rationale**:
- Official SDK ensures protocol compliance
- Server class provides structured handler registration
- Built-in transport handling (stdio, HTTP)
- Active development by Anthropic team

**Key Patterns**:
```python
from mcp.server import Server
from mcp.types import Tool, Resource

server = Server("hierarchical-docs")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="search_documentation", ...),
        Tool(name="navigate_to", ...),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_documentation":
        return await search_handler(arguments)
```

---

### 5. Configuration Management

**Decision**: Use `pydantic-settings` for configuration with environment variable support

**Rationale**:
- Type-safe configuration with validation
- Automatic environment variable parsing
- Supports multiple sources (env vars, .env files, YAML)
- Excellent error messages for misconfiguration

**Configuration Schema**:
```python
from pydantic_settings import BaseSettings
from pydantic import Field, DirectoryPath

class SourceConfig(BaseModel):
    path: DirectoryPath
    category: str
    label: str
    recursive: bool = True
    include_patterns: list[str] = ["*.md", "*.mdx"]
    exclude_patterns: list[str] = ["node_modules", ".git"]

class ServerConfig(BaseSettings):
    docs_root: DirectoryPath = Field(default="./docs")
    sources: list[SourceConfig] = []
    openapi_specs: list[FilePath] = []
    cache_ttl: int = 3600  # 1 hour default
    max_depth: int = 10
    enable_file_watching: bool = True
    
    class Config:
        env_prefix = "MCP_DOCS_"
        env_file = ".env"
        yaml_file = ".mcp-docs.yaml"
```

---

### 6. Security Best Practices for MCP Servers

**Research Findings**:

**Path Traversal Prevention**:
- Always use `Path.resolve()` to normalize paths
- Check `resolved_path.is_relative_to(base_path)` (Python 3.9+)
- Reject paths containing `..`, hidden files (`.`), and special chars
- Use allowlist approach: explicitly enumerate allowed directories

**Query Sanitization**:
- Escape special regex characters when building search patterns
- Limit query length (max 500 chars)
- Remove control characters and null bytes
- Log all queries for audit trail

**OpenAPI Description Safety**:
- Scan descriptions for prompt injection patterns
- Patterns to detect: "ignore previous", "disregard", "override", "instead execute"
- Sanitize or reject specs containing suspicious patterns
- Consider content filtering for AI-facing descriptions

**Implementation**:
```python
from pathlib import Path

def validate_path(requested: str, base: Path) -> Path:
    # Normalize and resolve
    resolved = (base / requested).resolve()
    
    # Must be within base
    if not resolved.is_relative_to(base):
        raise SecurityError("Path outside documentation root")
    
    # No hidden files/dirs
    if any(part.startswith('.') for part in resolved.parts):
        raise SecurityError("Hidden files not accessible")
    
    return resolved

def sanitize_query(query: str) -> str:
    # Remove control chars
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)
    
    # Limit length
    if len(query) > 500:
        raise ValueError("Query too long")
    
    # Escape for regex
    return re.escape(query)
```

---

## Testing Strategy Research

**MCP Protocol Compliance Testing**:
- Use MCP Inspector tool for manual protocol testing
- Create automated contract tests verifying JSON-RPC message format
- Test both tool and resource primitives
- Validate error responses match MCP error codes

**Cross-Platform Testing**:
- GitHub Actions matrix: Ubuntu, macOS, Windows
- Test stdio transport on all platforms
- Verify path handling differences (/ vs \\)
- Test with actual Claude Desktop and VS Code configs

**Performance Testing**:
- Generate synthetic documentation sets (1k, 5k, 10k docs)
- Measure response times for all success criteria
- Load test with concurrent queries (using asyncio)
- Profile memory usage with large document sets

**Security Testing**:
- Automated penetration testing with known attack patterns
- Fuzzing path inputs with various traversal attempts
- Test query injection with special characters
- Verify audit logging captures all attempts

---

## Dependencies Summary

**Core Dependencies** (pyproject.toml):
```toml
[project]
dependencies = [
    "mcp>=1.0.0",  # Official MCP SDK
    "pyyaml>=6.0",  # YAML parsing
    "pydantic>=2.0",  # Data validation
    "pydantic-settings>=2.0",  # Config management
    "openapi-spec-validator>=0.7",  # OpenAPI validation
    "prance>=23.0",  # OpenAPI parsing with $ref resolution
    "watchdog>=3.0",  # File system watching
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-mock>=3.0",
    "pytest-cov>=4.0",
]
performance = [
    "whoosh>=2.7",  # Optional fast search (if needed)
]
```

---

## Risk Mitigation

**Risk 1: MCP Protocol Changes**
- Mitigation: Pin `mcp` SDK version, monitor release notes, maintain contract tests
- Impact: Medium - protocol is stabilizing but still evolving

**Risk 2: Performance with Large Documentation**
- Mitigation: Implement caching first, whoosh fallback ready, performance tests in CI
- Impact: Low - spec requirements are reasonable for modern hardware

**Risk 3: Cross-Platform Path Handling**
- Mitigation: Use `pathlib.Path` exclusively (handles platform differences), test on all OSes
- Impact: Low - Python's pathlib abstracts platform differences well

**Risk 4: OpenAPI Spec Complexity**
- Mitigation: Comprehensive validation, clear error messages, examples in docs
- Impact: Medium - specs can be malformed or extremely complex

**Risk 5: Security Vulnerabilities**
- Mitigation: Security-first design, automated security tests, regular audits
- Impact: High - file system access requires careful validation

---

## Conclusion

All technical uncertainties have been resolved with concrete decisions:

1. ✅ **OpenAPI Parsing**: openapi-spec-validator + prance
2. ✅ **Search Strategy**: Start with regex, add whoosh if needed
3. ✅ **File Watching**: watchdog library
4. ✅ **MCP SDK**: Official mcp Python SDK
5. ✅ **Configuration**: pydantic-settings
6. ✅ **Security**: Comprehensive validation patterns identified

**Ready for Phase 1**: Design (data models, contracts, quickstart)
