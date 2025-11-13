# Data Model: Hierarchical Documentation MCP Server

**Feature**: Hierarchical Documentation MCP Server  
**Date**: November 4, 2025  
**Purpose**: Define entities, relationships, and validation rules from feature specification

## Core Entities

### 1. DocumentationSource

Represents a configured location containing documentation files.

**Attributes**:
- `path`: Path - Absolute or workspace-relative path to documentation directory
- `category`: str - Logical category name for grouping (e.g., "guides", "api-reference")
- `label`: str - Human-readable display name
- `recursive`: bool - Whether to traverse subdirectories (default: True)
- `include_patterns`: list[str] - File patterns to include (default: ["*.md", "*.mdx"])
- `exclude_patterns`: list[str] - Patterns to exclude (default: ["node_modules", ".git", "_*"])
- `format_type`: Literal["markdown", "openapi"] - Source format type

**Validation Rules**:
- `path` MUST exist and be readable (FR-023, FR-026)
- `category` MUST be unique across all sources (FR-024)
- `include_patterns` and `exclude_patterns` MUST be valid glob patterns (FR-027)
- `path` MUST be validated for security (no traversal outside allowed directories) (FR-028)

**Relationships**:
- Has many → `Document` (contained documents)
- Has many → `Category` (root-level categories within this source)

**State**: Immutable after configuration load

---

### 2. Document

Individual markdown file with optional frontmatter metadata.

**Attributes**:
- `file_path`: Path - Absolute file system path
- `relative_path`: Path - Path relative to documentation root
- `uri`: str - MCP resource URI (e.g., "docs://guides/security/authentication")
- `title`: str - Document title (from frontmatter or filename)
- `content`: str - Markdown content (cached)
- `frontmatter`: dict[str, Any] - Parsed YAML frontmatter metadata
- `tags`: list[str] - Tags from frontmatter (default: [])
- `category`: Optional[str] - Category from frontmatter
- `order`: int - Sort order from frontmatter (default: 999)
- `parent`: Optional[str] - Parent document reference from frontmatter
- `last_modified`: datetime - File modification timestamp
- `size_bytes`: int - File size for memory management

**Validation Rules**:
- `file_path` MUST be within allowed documentation root (FR-028, FR-031)
- `file_path` MUST NOT be hidden file (starting with '.') (FR-029)
- `file_path` MUST end with '.md' or '.mdx' (FR-008)
- `content` MUST be valid UTF-8 encoded text
- `frontmatter` MUST be valid YAML if present, else empty dict (FR-007, FR-010, FR-046)
- `uri` MUST follow pattern `docs://[category]/[section]/[document]` (FR-002)

**Relationships**:
- Belongs to → `DocumentationSource` (source location)
- Belongs to → `Category` (hierarchical parent)
- Has many → `SearchResult` (when matched in searches)

**State Transitions**:
- Created → when file discovered during source scanning
- Modified → when file change detected via file watching (FR-041)
- Invalidated → when cache entry expires (FR-040)

**Derived Properties**:
```python
@property
def breadcrumbs(self) -> list[str]:
    """Generate breadcrumb path from root to document"""
    return list(self.relative_path.parts[:-1])

@property
def excerpt(self, max_length: int = 200) -> str:
    """First N characters of content, excluding frontmatter"""
    # Extract first paragraph after frontmatter
```

---

### 3. Category

Logical grouping of documentation at any hierarchy level.

**Attributes**:
- `name`: str - Category name (directory name or frontmatter category)
- `label`: str - Human-readable display name
- `uri`: str - MCP resource URI (e.g., "docs://guides" or "docs://guides/security")
- `parent_uri`: Optional[str] - Parent category URI
- `depth`: int - Hierarchy depth (0 = root)
- `child_categories`: list[str] - URIs of child categories
- `child_documents`: list[str] - URIs of contained documents
- `document_count`: int - Total documents in this category and descendants
- `source_category`: str - Reference to DocumentationSource category

**Validation Rules**:
- `name` MUST be valid directory name (no special chars, no '..')
- `depth` MUST be <= configured max_depth (default: 10) (FR-001)
- `uri` MUST follow pattern `docs://[category]` or `docs://[category]/[section]` (FR-002)
- `parent_uri` MUST exist if specified (referential integrity)

**Relationships**:
- Belongs to → `DocumentationSource` (source location)
- Has one → `Category` (parent, nullable for root)
- Has many → `Category` (children)
- Has many → `Document` (contained documents)

**State**: Dynamic - updated when documents added/removed

**Derived Properties**:
```python
@property
def breadcrumbs(self) -> list[dict]:
    """Generate breadcrumb navigation to this category"""
    parts = self.uri.replace("docs://", "").split("/")
    return [
        {"name": part, "uri": f"docs://{'/'.join(parts[:i+1])}"}
        for i, part in enumerate(parts)
    ]

@property
def is_root(self) -> bool:
    return self.depth == 0
```

---

### 4. OpenAPISpecification

API documentation spec defining endpoints and schemas.

**Attributes**:
- `file_path`: Path - Path to OpenAPI spec file
- `version`: str - OpenAPI version (e.g., "3.0.0", "3.1.0")
- `title`: str - API title from info.title
- `description`: str - API description from info.description
- `tags`: list[dict] - Tag definitions for grouping operations
- `operations`: dict[str, APIOperation] - Keyed by operationId
- `schemas`: dict[str, dict] - Schema definitions from components.schemas
- `base_uri`: str - Base URI for this API (e.g., "api://")
- `validated`: bool - Whether spec passed validation
- `validation_errors`: list[str] - Errors from validation (empty if valid)

**Validation Rules**:
- `file_path` MUST exist and be readable
- `version` MUST be "3.0.x" or "3.1.x" (FR-011)
- Spec MUST pass `openapi-spec-validator` validation (FR-016)
- `operations` MUST have unique operationId values
- Descriptions MUST be sanitized for prompt injection (FR-032)

**Relationships**:
- Has many → `APIOperation` (defined endpoints)

**State**: Immutable after loading and validation

---

### 5. APIOperation

Individual endpoint from OpenAPI spec.

**Attributes**:
- `operation_id`: str - Unique operation identifier
- `method`: str - HTTP method (GET, POST, PUT, DELETE, etc.)
- `path`: str - URL path with parameters (e.g., "/users/{id}")
- `uri`: str - MCP resource URI (e.g., "api://users/getUser")
- `tag`: Optional[str] - OpenAPI tag for grouping
- `summary`: str - Short description
- `description`: str - Detailed description (sanitized)
- `parameters`: list[dict] - Path, query, header parameters
- `request_body`: Optional[dict] - Request body schema
- `responses`: dict[str, dict] - Response definitions by status code
- `deprecated`: bool - Whether operation is deprecated (default: False)

**Validation Rules**:
- `operation_id` MUST be unique within spec (FR-012)
- `method` MUST be valid HTTP method
- `path` MUST start with '/'
- `uri` MUST follow pattern `api://[tag]/[operationId]` (FR-013)
- `description` MUST be sanitized (FR-032)

**Relationships**:
- Belongs to → `OpenAPISpecification` (parent spec)
- References → schemas (via $ref in request_body, responses)

**Derived Properties**:
```python
@property
def full_description(self) -> str:
    """Combines summary and description for AI consumption"""
    return f"{self.summary}\n\n{self.description}" if self.description else self.summary

@property
def required_parameters(self) -> list[dict]:
    """Filters to only required parameters"""
    return [p for p in self.parameters if p.get("required", False)]
```

---

### 6. SearchResult

Match from a search query.

**Attributes**:
- `document_uri`: str - URI of matched document
- `title`: str - Document title
- `excerpt`: str - Content excerpt showing match context
- `breadcrumbs`: list[str] - Hierarchical path to document
- `category`: str - Top-level category
- `relevance_score`: float - Match quality score (0.0 to 1.0)
- `match_type`: Literal["full_text", "metadata", "title"] - How document matched
- `highlighted_excerpt`: str - Excerpt with match highlighted (e.g., **term**)

**Validation Rules**:
- `document_uri` MUST reference existing document (FR-019)
- `relevance_score` MUST be between 0.0 and 1.0
- `excerpt` MUST be truncated to reasonable length (max 500 chars)

**Relationships**:
- References → `Document` (matched document)

**State**: Ephemeral - created per query, not persisted

**Derived Properties**:
```python
@property
def breadcrumb_string(self) -> str:
    """Human-readable breadcrumb path"""
    return " > ".join(self.breadcrumbs)
```

---

### 7. NavigationContext

Current position in documentation hierarchy.

**Attributes**:
- `current_uri`: str - Current location URI
- `current_type`: Literal["root", "category", "document"] - Type of current item
- `parent_uri`: Optional[str] - Parent location URI (None if at root)
- `breadcrumbs`: list[dict] - Full path from root to current
- `children`: list[dict] - Available child items (categories or documents)
- `sibling_count`: int - Number of items at same level
- `navigation_options`: dict[str, str] - Available navigation commands

**Validation Rules**:
- `current_uri` MUST be valid docs:// or api:// URI (FR-002, FR-013)
- `parent_uri` MUST exist if not at root (FR-005)
- `children` items MUST have valid URIs

**Relationships**:
- References → `Category` or `Document` (current location)
- References → `Category` (parent, if applicable)

**State**: Ephemeral - created per navigation query

**Derived Properties**:
```python
@property
def can_navigate_up(self) -> bool:
    """Whether parent navigation is possible"""
    return self.parent_uri is not None

@property
def can_navigate_down(self) -> bool:
    """Whether child navigation is possible"""
    return len(self.children) > 0
```

---

### 8. CacheEntry

Cached parsed content for performance.

**Attributes**:
- `key`: str - Cache key (usually URI or file path)
- `value`: Any - Cached data (parsed markdown, search results, etc.)
- `cached_at`: datetime - When entry was cached
- `ttl`: int - Time-to-live in seconds (default from config: 3600)
- `file_mtime`: Optional[datetime] - File modification time (for invalidation)
- `size_bytes`: int - Approximate memory size of cached value

**Validation Rules**:
- `ttl` MUST be positive integer (FR-040)
- Cache MUST respect configured max memory usage
- Entries MUST be invalidated when source files change (FR-041)

**State Transitions**:
- Created → when data first cached
- Accessed → on cache hit (updates LRU position)
- Invalidated → when TTL expires or file changes
- Evicted → when cache reaches memory limit (LRU eviction)

**Derived Properties**:
```python
@property
def is_expired(self) -> bool:
    """Check if entry has exceeded TTL"""
    return (datetime.utcnow() - self.cached_at).total_seconds() > self.ttl

@property
def is_stale(self) -> bool:
    """Check if source file has been modified"""
    if self.file_mtime is None:
        return False
    current_mtime = get_file_mtime(self.key)
    return current_mtime > self.file_mtime
```

---

## Entity Relationships Diagram

```
DocumentationSource (1) ----< (N) Category
                     |
                     +-------< (N) Document
                     
Category (1) ----< (N) Category (parent-child)
         |
         +-------< (N) Document

OpenAPISpecification (1) ----< (N) APIOperation

Document ----< SearchResult (ephemeral)
Category ----< NavigationContext (ephemeral)

CacheEntry --> Document, Category, SearchResult (any)
```

---

## Data Flow Patterns

### Document Loading Flow
```
1. Source configured → DocumentationSource created
2. Scan directory → Document instances created
3. Parse frontmatter → Metadata extracted
4. Build hierarchy → Category tree constructed
5. Cache entries → Parsed content cached
6. Register URIs → Resource mappings created
```

### Search Query Flow
```
1. Query received → Sanitize input
2. Search index → Find matching documents
3. Score results → Calculate relevance
4. Enrich context → Add breadcrumbs
5. Create SearchResults → Return to AI agent
```

### Navigation Flow
```
1. URI received → Validate and parse
2. Resolve location → Find Category or Document
3. Build context → Get parent, children
4. Create NavigationContext → Return with options
```

### Cache Invalidation Flow
```
1. File change detected → Watchdog event
2. Identify affected entries → By file path or URI
3. Invalidate entries → Remove from cache
4. Next access → Re-parse and re-cache
```

---

## Validation Summary

**Security Validations** (Priority: Critical):
- All file paths validated before access (FR-028, FR-031)
- Hidden files blocked (FR-029)
- Search queries sanitized (FR-030)
- OpenAPI descriptions sanitized (FR-032)

**Data Integrity Validations**:
- YAML frontmatter parsing with error handling (FR-046)
- OpenAPI spec validation before loading (FR-016)
- URI format validation for all resources (FR-002, FR-013)
- Referential integrity for parent-child relationships

**Performance Validations**:
- Cache TTL enforcement (FR-040)
- File change detection (FR-041)
- Memory usage monitoring (FR-042, FR-043)
- Timeout protection for long operations (FR-047)

---

## Testing Considerations

**Unit Tests Required**:
- Each entity's validation rules
- Derived property calculations
- State transition logic
- Relationship consistency

**Integration Tests Required**:
- End-to-end document loading with hierarchy
- Cache invalidation with file watching
- Cross-entity queries (search across categories)
- Security validation with attack patterns

**Performance Tests Required**:
- Large document set loading (10k docs)
- Cache hit/miss ratios
- Memory usage under load
- Concurrent access patterns
