# Building a Hierarchical Documentation MCP: Complete Implementation Guide

**The Model Context Protocol is production-ready**, and multiple mature implementations exist that can be leveraged or adapted. After analyzing existing solutions, technical specifications, and cross-platform compatibility, this guide provides a complete implementation plan for an open-source MCP supporting hierarchical documentation traversal with markdown and OpenAPI support.

## Can existing solutions be adopted?

**Short answer: Partially adopt, then extend.** Several excellent implementations exist that solve parts of the problem, but none provide complete hierarchical documentation traversal with both markdown and OpenAPI support out-of-the-box.

**Best candidates for adaptation:**

**Docs MCP Server** (arabold/docs-mcp-server) offers semantic chunking, multi-source support, and version awareness—ideal for the base architecture. However, it focuses on search rather than hierarchical navigation. **Official Filesystem Server** provides comprehensive tree traversal tools and security patterns perfect for hierarchical structures but lacks documentation-specific features. **FastMCP's OpenAPI integration** enables automatic API documentation conversion but requires curation for optimal LLM performance.

The recommended approach: **Start with FastMCP framework + Official Filesystem patterns + OpenAPI auto-generation, then add hierarchical navigation layer**.

## MCP Architecture Fundamentals

The Model Context Protocol uses a **client-server architecture** with JSON-RPC 2.0 messaging. Every MCP server provides three core primitives: **Tools** (executable actions), **Resources** (read-only data with URIs), and **Prompts** (reusable templates). For hierarchical documentation, Resources handle navigation while Tools manage search and dynamic operations.

**Critical design principle**: Resources are application-controlled (user decides what to fetch), while Tools are model-controlled (AI decides when to invoke). For documentation systems, this means the user explicitly navigates sections via Resources, while the AI autonomously searches via Tools.

MCP supports two transport mechanisms: **stdio** for local processes (perfect for Claude Desktop integration) and **Streamable HTTP** for remote servers (ideal for team deployments). The protocol's initialization sequence negotiates capabilities, enabling servers to declare whether they support tools, resources, or both.

## Technical Implementation Plan

### Phase 1: Foundation with FastMCP

**Choose FastMCP (Python)** as the primary framework for rapid development with minimal boilerplate. The high-level API with decorators enables quick prototyping while maintaining production-ready quality.

**Basic server structure:**
```python
from fastmcp import FastMCP
from pathlib import Path
import yaml

mcp = FastMCP(name="hierarchical-docs")
DOCS_ROOT = Path(os.getenv("DOCS_ROOT", "./docs"))
```

FastMCP automatically generates JSON schemas from Python type hints, handles transport configuration, and provides built-in authentication options (OAuth, GitHub, Azure). This eliminates hundreds of lines of boilerplate compared to using the low-level SDK directly.

### Phase 2: Hierarchical Resource Structure

Design URI patterns that naturally reflect documentation hierarchy using **RFC 6570 URI templates**:

```
docs://                                    (Root - list all categories)
docs://{category}                          (Category - list sections)
docs://{category}/{section}                (Section - list features)
docs://{category}/{section}/{feature}      (Feature - show details)
```

**Implement multi-level resources:**
```python
@mcp.resource("docs://")
def get_root() -> dict:
    """List all documentation categories."""
    return {
        "categories": [
            {"name": cat.name, "uri": f"docs://{cat.name}", "count": len(list(cat.glob("**/*.md")))}
            for cat in DOCS_ROOT.iterdir() if cat.is_dir()
        ]
    }

@mcp.resource("docs://{category}")
def get_category(category: str) -> dict:
    """List sections within a category."""
    cat_path = DOCS_ROOT / category
    sections = [d for d in cat_path.iterdir() if d.is_dir()]
    documents = [f for f in cat_path.glob("*.md")]
    
    return {
        "category": category,
        "sections": [{"name": s.name, "uri": f"docs://{category}/{s.name}"} for s in sections],
        "documents": [{"name": d.stem, "uri": f"docs://{category}/{d.name}"} for d in documents]
    }

@mcp.resource("docs://{category}/{section}/{feature}")
def get_feature_details(category: str, section: str, feature: str) -> str:
    """Get detailed documentation for a specific feature."""
    file_path = DOCS_ROOT / category / section / f"{feature}.md"
    if not file_path.exists():
        raise FileNotFoundError(f"Feature documentation not found: {category}/{section}/{feature}")
    
    # Parse frontmatter and content
    content = file_path.read_text()
    return enrich_with_metadata(content, file_path)
```

The wildcard parameter pattern `{path*}` handles arbitrary depth: `@mcp.resource("docs://{path*}")` matches any nested path like `docs://api/endpoints/users/get`.

### Phase 3: OpenAPI Integration Layer

**Use FastMCP's built-in OpenAPI support** to automatically generate documentation from Swagger specs:

```python
from fastmcp.server.openapi import RouteMap, MCPType
import httpx

# Load OpenAPI spec
spec = load_openapi_spec("./openapi.yaml")

# Create MCP from OpenAPI with curated mappings
openapi_mcp = FastMCP.from_openapi(
    openapi_spec=spec,
    client=httpx.AsyncClient(),
    route_maps=[
        # Convert GET endpoints to Resources
        RouteMap(methods=["GET"], pattern=r"^/api/docs/.*", mcp_type=MCPType.RESOURCE),
        # Exclude internal endpoints
        RouteMap(pattern=r"^/internal/.*", mcp_type=MCPType.EXCLUDE),
        # Actions become Tools
        RouteMap(methods=["POST", "PUT", "DELETE"], mcp_type=MCPType.TOOL)
    ]
)
```

**Hierarchical mapping from OpenAPI paths:**
OpenAPI naturally structures APIs hierarchically. Map path segments to resource URIs:

```
/customers                    → api://customers
/customers/{id}               → api://customers/{id}
/customers/{id}/orders        → api://customers/{id}/orders
```

**Enrich OpenAPI descriptions for AI clarity:**
```yaml
/todos:
  get:
    summary: Discover existing todos for contextual task awareness
    description: >
      Allows AI agents to retrieve todos with optional filtering.
      Useful for understanding current task state and planning next actions.
    x-mcp-hints:
      use_case: "User asks to see incomplete tasks"
      example_query: { completed: false, limit: 10 }
```

The auto-generation approach requires **curation**—review generated tools, enhance descriptions for AI understanding, and group related operations using OpenAPI tags. Companies like Xata use Kubb to auto-generate from OpenAPI, then manually refine tool descriptions.

### Phase 4: Hierarchical Navigation Tools

While Resources provide explicit navigation, Tools enable intelligent exploration:

```python
@mcp.tool()
def search_documentation(
    query: str,
    category: str = None,
    depth: int = 3,
    max_results: int = 10
) -> list[dict]:
    """Search through documentation with hierarchical context.
    
    Returns results with breadcrumb paths showing document location
    in the hierarchy.
    """
    results = []
    root = DOCS_ROOT / category if category else DOCS_ROOT
    
    for file in root.rglob("*.md"):
        if matches_query(file, query):
            relative = file.relative_to(DOCS_ROOT)
            breadcrumbs = list(relative.parts[:-1])
            
            results.append({
                "title": extract_title(file),
                "path": str(relative),
                "uri": f"docs://{'/'.join(relative.parts[:-1])}/{relative.stem}",
                "breadcrumbs": breadcrumbs,
                "category": breadcrumbs[0] if breadcrumbs else "root",
                "excerpt": extract_excerpt(file, query)
            })
            
            if len(results) >= max_results:
                break
    
    return results

@mcp.tool()
def get_table_of_contents(path: str = "") -> dict:
    """Generate hierarchical table of contents.
    
    Returns nested structure showing full documentation hierarchy
    with document counts at each level.
    """
    def build_tree(directory):
        tree = {"name": directory.name, "type": "category", "children": []}
        
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                tree["children"].append(build_tree(item))
            elif item.suffix == ".md":
                tree["children"].append({
                    "name": item.stem,
                    "type": "document",
                    "uri": f"docs://{item.relative_to(DOCS_ROOT).with_suffix('')}"
                })
        
        return tree
    
    start_path = DOCS_ROOT / path if path else DOCS_ROOT
    return build_tree(start_path)

@mcp.tool()
def navigate_to(target: str, context: str = None) -> dict:
    """Navigate to specific location in documentation hierarchy.
    
    Provides context about current location, available children,
    and navigation options.
    """
    parts = target.strip('/').split('/')
    current_path = DOCS_ROOT / '/'.join(parts)
    
    return {
        "current": {
            "path": target,
            "type": "category" if current_path.is_dir() else "document",
            "uri": f"docs://{target}"
        },
        "breadcrumbs": [{"name": p, "uri": f"docs://{'/'.join(parts[:i+1])}"} 
                       for i, p in enumerate(parts)],
        "children": [{"name": c.name, "type": "category" if c.is_dir() else "document"}
                    for c in current_path.iterdir()] if current_path.is_dir() else [],
        "parent": f"docs://{'/'.join(parts[:-1])}" if len(parts) > 1 else "docs://"
    }
```

These tools enable AI agents to understand documentation structure, search across hierarchy levels, and provide contextual navigation hints.

### Phase 5: Markdown Enhancement with Metadata

Parse frontmatter to enable metadata-based navigation:

```python
import yaml
from typing import TypedDict

class DocMetadata(TypedDict):
    title: str
    category: str
    tags: list[str]
    order: int
    parent: str | None

def parse_markdown_with_metadata(file_path: Path) -> tuple[DocMetadata, str]:
    """Extract YAML frontmatter and markdown content."""
    content = file_path.read_text()
    
    if content.startswith('---'):
        _, frontmatter, body = content.split('---', 2)
        metadata = yaml.safe_load(frontmatter)
        return metadata, body.strip()
    
    return {}, content

@mcp.tool()
def search_by_metadata(
    tags: list[str] = None,
    category: str = None,
    parent: str = None
) -> list[dict]:
    """Search documentation by metadata fields.
    
    Enables tag-based discovery and category filtering
    independent of file system structure.
    """
    results = []
    
    for file in DOCS_ROOT.rglob("*.md"):
        metadata, _ = parse_markdown_with_metadata(file)
        
        if tags and not any(t in metadata.get('tags', []) for t in tags):
            continue
        if category and metadata.get('category') != category:
            continue
        if parent and metadata.get('parent') != parent:
            continue
            
        results.append({
            "title": metadata.get('title', file.stem),
            "path": str(file.relative_to(DOCS_ROOT)),
            "uri": f"docs://{file.relative_to(DOCS_ROOT).with_suffix('')}",
            "metadata": metadata
        })
    
    return sorted(results, key=lambda r: r['metadata'].get('order', 999))
```

Metadata enables alternative hierarchies—documents can be organized by filesystem structure AND by tags/categories simultaneously.

### Phase 6: Configuration Management

**Support multiple configuration sources** for flexibility:

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class SourceConfig(BaseModel):
    path: Path
    category: str
    label: str
    recursive: bool = True
    include_patterns: list[str] = ["*.md", "*.mdx"]
    exclude_patterns: list[str] = ["node_modules", ".git", "_*"]

class ServerConfig(BaseSettings):
    docs_root: Path = Field(default="./docs")
    sources: list[SourceConfig] = []
    max_depth: int = 10
    enable_search: bool = True
    cache_ttl: int = 3600
    openapi_specs: list[Path] = []
    
    class Config:
        env_prefix = "MCP_DOCS_"
        env_file = ".env"

# Load configuration
config = ServerConfig()

# Apply sources configuration
for source in config.sources:
    register_source(source)

# Load OpenAPI specs
for spec_path in config.openapi_specs:
    integrate_openapi_spec(spec_path)
```

**Configuration file example** (`.mcp-docs.yaml`):
```yaml
sources:
  - path: ./docs/guides
    category: guides
    label: User Guides
    recursive: true
  - path: ./docs/api
    category: api-reference
    label: API Reference
    recursive: true
  - path: ./openapi
    category: api
    label: REST API
    format: openapi

openapi_specs:
  - ./specs/api-v1.yaml
  - ./specs/api-v2.yaml

taxonomy:
  guides:
    label: Guides
    children:
      getting-started: Getting Started
      tutorials: Tutorials
  api-reference:
    label: API Reference
    children:
      rest-api: REST API
      graphql: GraphQL API
```

### Phase 7: Security and Validation

Implement **comprehensive input validation** to prevent security issues:

```python
from pathlib import Path
import re

def validate_path(path: str, base: Path) -> Path:
    """Validate path to prevent directory traversal attacks."""
    # Normalize and resolve path
    requested = (base / path).resolve()
    
    # Ensure path stays within base directory
    if not requested.is_relative_to(base):
        raise ValueError(f"Access denied: path outside documentation root")
    
    # Block access to hidden files/directories
    if any(part.startswith('.') for part in requested.parts):
        raise ValueError(f"Access denied: hidden files not accessible")
    
    return requested

def sanitize_search_query(query: str) -> str:
    """Sanitize search queries to prevent injection."""
    # Remove control characters
    query = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', query)
    
    # Limit length
    if len(query) > 500:
        raise ValueError("Query too long (max 500 characters)")
    
    # Remove potentially problematic patterns for regex
    query = re.escape(query)
    
    return query

@mcp.tool()
def search_documentation(query: str, category: str = None) -> list[dict]:
    """Search with validation."""
    # Sanitize inputs
    safe_query = sanitize_search_query(query)
    
    if category:
        validate_path(category, DOCS_ROOT)
    
    # Proceed with safe search
    return perform_search(safe_query, category)
```

**OpenAPI sanitization** is critical—validate spec descriptions to prevent prompt injection:

```python
def sanitize_openapi_description(desc: str) -> str:
    """Sanitize OpenAPI descriptions to prevent tool poisoning."""
    forbidden_patterns = [
        r"ignore\s+previous",
        r"disregard\s+",
        r"override\s+",
        r"instead\s+execute",
    ]
    
    for pattern in forbidden_patterns:
        desc = re.sub(pattern, "[REMOVED]", desc, flags=re.IGNORECASE)
    
    return desc
```

## Cross-Platform Compatibility

### GitHub Copilot vs Claude

**Good news: Core compatibility is strong.** Both platforms fully support MCP Tools using stdio and HTTP transports. An MCP built with the official SDK works on both with minimal configuration changes.

**Key differences to accommodate:**

**GitHub Copilot's Coding Agent** (autonomous multi-file editing mode) supports Tools only—no Resources or Prompts. However, **Copilot Chat** (interactive mode) supports all three primitives fully. Design the MCP to work well with Tools alone, treating Resources as optional enhancements.

**Configuration format differences:**

*Claude Desktop* (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "hierarchical-docs": {
      "command": "npx",
      "args": ["-y", "@your-org/hierarchical-docs-mcp"],
      "env": {
        "DOCS_ROOT": "/path/to/docs"
      }
    }
  }
}
```

*VS Code* (`.vscode/mcp.json`):
```json
{
  "servers": {
    "hierarchical-docs": {
      "command": "npx",
      "args": ["-y", "@your-org/hierarchical-docs-mcp"],
      "env": {
        "DOCS_ROOT": "${workspaceFolder}/docs"
      }
    }
  }
}
```

VS Code supports predefined variables like `${workspaceFolder}`, enabling project-relative paths.

**Authentication differences:** Copilot Coding Agent doesn't support OAuth for remote servers (Personal Access Tokens only). Copilot Chat fully supports OAuth. Design for PAT authentication if supporting the Coding Agent.

**Recommendation for cross-platform MCPs:**
1. **Focus on Tools** as the primary interface (universally supported)
2. **Provide Resources** as optional context (works in Claude + Copilot Chat)
3. **Document both configurations** in README
4. **Test on both platforms** regularly
5. **Use standard transports** (stdio/HTTP)

### Building Cross-Compatible Architecture

**Universal tool design pattern:**
```python
# These tools work everywhere
@mcp.tool()
def search_docs(query: str) -> list[dict]:
    """Search across all documentation."""
    pass

@mcp.tool()
def get_document(path: str) -> str:
    """Retrieve specific document content."""
    pass

@mcp.tool()
def list_sections(category: str = None) -> list[dict]:
    """List available documentation sections."""
    pass

# Resources provide enhanced navigation (Claude + Copilot Chat only)
@mcp.resource("docs://{category}/{section}")
def browse_section(category: str, section: str) -> str:
    """Browse documentation hierarchy."""
    pass
```

This hybrid approach ensures core functionality works universally while providing enhanced features where supported.

## Deployment Strategy

### Development Setup

**Local testing with Claude Desktop:**
1. Install server: `npm install -g @your-org/hierarchical-docs-mcp`
2. Configure Claude Desktop (see config above)
3. Restart Claude Desktop
4. Test with: "List all documentation categories"

**VS Code testing:**
1. Add to `.vscode/mcp.json`
2. Reload VS Code
3. Use Copilot Chat: "@hierarchical-docs search for authentication"

**MCP Inspector for debugging:**
```bash
npx @modelcontextprotocol/inspector npx -y @your-org/hierarchical-docs-mcp
```

Opens web UI to interactively test tools, view JSON-RPC messages, and debug errors.

### Production Deployment

**Option 1: NPM Package (Recommended for open-source)**

Package.json:
```json
{
  "name": "@your-org/hierarchical-docs-mcp",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "hierarchical-docs-mcp": "./build/index.js"
  },
  "files": ["build", "README.md"],
  "scripts": {
    "build": "tsc",
    "prepare": "npm run build"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.6.0"
  },
  "keywords": ["mcp", "documentation", "hierarchical", "openapi"]
}
```

Users install with: `npm install -g @your-org/hierarchical-docs-mcp`

**Option 2: Python Package (PyPI)**

pyproject.toml:
```toml
[project]
name = "hierarchical-docs-mcp"
version = "1.0.0"
dependencies = [
    "mcp[cli]>=1.0.0",
    "fastmcp>=2.0.0",
    "pyyaml>=6.0"
]

[project.scripts]
hierarchical-docs-mcp = "hierarchical_docs_mcp.main:main"
```

Users install with: `uvx hierarchical-docs-mcp` or `pip install hierarchical-docs-mcp`

**Option 3: Desktop Extension (.mcpb)**

One-click installation for Claude Desktop users:
```bash
npm install -g @anthropic-ai/mcpb
mcpb pack
# Distributes: hierarchical-docs-mcp.mcpb
```

**Option 4: Docker (for remote deployment)**

Dockerfile:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "hierarchical_docs_mcp.http_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

Deploy to cloud platforms (AWS, Azure, GCP) for team-wide access via HTTP transport.

### Publishing to GitHub MCP Registry

GitHub maintains an official registry for verified MCP servers:
1. Publish to npm/PyPI
2. Submit PR to https://github.com/mcp
3. Provide manifest with description, capabilities, configuration options
4. Users discover via VS Code Extensions view (`@mcp` filter)

## Project Structure

**Recommended organization for TypeScript:**
```
hierarchical-docs-mcp/
├── src/
│   ├── index.ts                 # Entry point
│   ├── server.ts                # Server initialization
│   ├── config.ts                # Configuration management
│   ├── handlers/
│   │   ├── tools.ts             # Tool request handlers
│   │   ├── resources.ts         # Resource handlers
│   │   └── prompts.ts           # Prompt handlers
│   ├── services/
│   │   ├── markdown.ts          # Markdown parsing
│   │   ├── openapi.ts           # OpenAPI integration
│   │   ├── search.ts            # Search engine
│   │   └── hierarchy.ts         # Tree traversal
│   └── utils/
│       ├── validation.ts        # Input validation
│       ├── cache.ts             # Caching layer
│       └── logger.ts            # Logging
├── docs/                        # Sample documentation
├── specs/                       # OpenAPI specs
├── tests/
├── package.json
├── tsconfig.json
└── README.md
```

**For Python:**
```
hierarchical_docs_mcp/
├── hierarchical_docs_mcp/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── server.py                # Server setup
│   ├── config.py                # Configuration
│   ├── tools/
│   │   ├── search.py
│   │   ├── navigation.py
│   │   └── metadata.py
│   ├── resources/
│   │   ├── documents.py
│   │   └── categories.py
│   └── services/
│       ├── markdown_parser.py
│       ├── openapi_loader.py
│       └── hierarchy_builder.py
├── docs/
├── specs/
├── tests/
├── pyproject.toml
└── README.md
```

## Complete Tool Set for Hierarchical Documentation

**Core Navigation Tools:**
- `list_categories()` - Top-level category enumeration
- `list_sections(category)` - Second-level sections
- `get_table_of_contents(path?)` - Full hierarchy tree
- `navigate_to(path)` - Navigate with context (breadcrumbs, children, parent)

**Search and Discovery:**
- `search_documentation(query, category?, depth?)` - Full-text search with hierarchy context
- `search_by_metadata(tags?, category?)` - Metadata-based discovery
- `find_related(document_path)` - Related documents based on tags/links
- `search_code_examples(language?, framework?)` - Code snippet search

**Content Access:**
- `get_document(path)` - Retrieve full document content
- `get_document_section(path, section_heading)` - Extract specific section
- `get_code_snippet(path, snippet_id)` - Extract code blocks

**OpenAPI-Specific:**
- `list_api_endpoints(tag?)` - List API operations
- `get_endpoint_docs(operation_id)` - Detailed endpoint documentation
- `get_schema_definition(schema_name)` - Data model documentation
- `search_api_operations(query)` - Search across API operations

**Resource URIs:**
- `docs://` - Root (category list)
- `docs://{category}` - Category contents
- `docs://{category}/{section}` - Section contents
- `docs://{category}/{section}/{document}` - Document content
- `api://{tag}/{operation_id}` - API endpoint from OpenAPI

## Implementation Roadmap

**Week 1-2: Foundation**
- Set up FastMCP project structure
- Implement basic file system traversal
- Create core navigation tools (list_categories, navigate_to)
- Add markdown parsing with frontmatter support
- Implement path validation and security

**Week 3-4: Hierarchical Features**
- Build resource URI templates for multi-level navigation
- Implement get_table_of_contents with full tree structure
- Add search_documentation with breadcrumb context
- Create metadata-based search and filtering
- Add caching layer for performance

**Week 5-6: OpenAPI Integration**
- Integrate FastMCP's OpenAPI loader
- Implement OpenAPI → Resource mapping
- Add API endpoint tools (list, search, get details)
- Create schema documentation resources
- Enhance OpenAPI descriptions for AI clarity

**Week 7-8: Cross-Platform Support**
- Test with Claude Desktop (all features)
- Test with VS Code + Copilot Chat (all features)
- Test with Copilot Coding Agent (tools only)
- Create configuration examples for both platforms
- Document platform-specific behaviors

**Week 9-10: Polish and Release**
- Comprehensive testing and debugging
- Write detailed README with examples
- Create sample documentation set
- Package for npm/PyPI
- Submit to GitHub MCP Registry
- Create .mcpb Desktop Extension

## Key Recommendations

**Architecture decisions:**
1. **Use FastMCP (Python)** for rapid development with excellent ergonomics
2. **Separate Resources (navigation) from Tools (search/actions)** for clear mental model
3. **Use URI templates** for dynamic hierarchical navigation
4. **Support both filesystem and metadata-based organization** for flexibility
5. **Cache aggressively** but invalidate intelligently for performance

**OpenAPI integration:**
1. **Auto-generate from specs** but always curate for AI usability
2. **Use tags for hierarchical organization** of endpoints
3. **Enhance descriptions** with capability language and use cases
4. **Map GET endpoints to Resources**, actions to Tools
5. **Sanitize specs** to prevent prompt injection

**Cross-platform strategy:**
1. **Design Tools-first** (universal compatibility)
2. **Add Resources as enhancements** (Claude + Copilot Chat)
3. **Test on both platforms** throughout development
4. **Document configuration** for Claude Desktop and VS Code
5. **Use standard authentication** (PAT for maximum compatibility)

**Security priorities:**
1. **Validate all paths** to prevent directory traversal
2. **Sanitize search queries** to prevent injection
3. **Review OpenAPI descriptions** for malicious content
4. **Use allowlists** for accessible directories
5. **Log access** for audit trails

## Success Criteria

Your hierarchical documentation MCP should enable users to:
- **"Show me all API documentation"** → Lists categories with document counts
- **"Navigate to authentication guides"** → Provides breadcrumbs, children, and content
- **"Search for OAuth examples"** → Returns results with hierarchical context
- **"What endpoints are available for users?"** → Lists OpenAPI operations with descriptions
- **"Get the schema for the User model"** → Returns OpenAPI schema documentation
- **"List all guides about deployment"** → Metadata-based discovery across hierarchy

The system should work seamlessly in Claude Desktop (full features), VS Code with Copilot Chat (full features), and provide core functionality in Copilot Coding Agent (tools only).

## Conclusion

Building an open-source hierarchical documentation MCP is **achievable in 8-10 weeks** using existing tools and patterns. The MCP ecosystem provides mature frameworks (FastMCP), proven architectural patterns (Official Filesystem Server), and production-ready OpenAPI integration. 

**The recommended approach**: Start with FastMCP for the framework, adopt Official Filesystem hierarchical patterns, integrate OpenAPI using auto-generation with curation, and design Tools-first for universal compatibility with Claude and GitHub Copilot.

The resulting MCP will provide AI agents with structured, hierarchical access to documentation that combines the best of filesystem organization, metadata-based discovery, and automatic API documentation from OpenAPI specs—all through a clean, secure interface compatible with major AI development tools.
