# Feature Specification: Hierarchical Documentation MCP Server

**Feature Branch**: `001-hierarchical-docs-mcp`  
**Created**: November 4, 2025  
**Status**: Draft  
**Input**: Building a Hierarchical Documentation MCP: Complete Implementation Guide - An open-source MCP supporting hierarchical documentation traversal with markdown and OpenAPI support for AI assistants

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI-Assisted Documentation Navigation (Priority: P1)

A developer uses an AI coding assistant (Claude Desktop or GitHub Copilot) to query project documentation. They ask "Show me the authentication guide" and the AI assistant navigates the hierarchical documentation structure to find and present the relevant content with context about its location (breadcrumbs, related sections).

**Why this priority**: Core value proposition - enables AI agents to understand and navigate documentation structure rather than relying on keyword search alone. This is the minimum viable capability.

**Independent Test**: Can be fully tested by configuring a local documentation directory, connecting an AI assistant to the MCP server, and asking natural language questions about documentation topics. Delivers immediate value by improving documentation discovery.

**Acceptance Scenarios**:

1. **Given** a documentation set organized in nested folders, **When** user asks AI assistant "What authentication methods are available?", **Then** AI assistant uses the MCP to navigate to authentication documentation and presents the content with hierarchical context (e.g., "Found in Guides > Security > Authentication")

2. **Given** documentation with category folders (guides, tutorials, api-reference), **When** user asks "List all available guides", **Then** AI assistant queries the MCP and returns a categorized list showing the documentation structure

3. **Given** markdown files with YAML frontmatter containing tags and metadata, **When** user asks "Show me all tutorials about deployment", **Then** AI assistant searches by metadata and returns matching documents with their locations in the hierarchy

---

### User Story 2 - API Documentation Discovery from OpenAPI Specs (Priority: P1)

A developer working on API integration asks their AI assistant "What endpoints are available for user management?". The AI assistant queries the MCP server which has loaded OpenAPI specifications, and presents available endpoints with their descriptions, parameters, and response schemas in a structured format.

**Why this priority**: Critical for API-first projects where documentation is maintained as OpenAPI specs. Enables AI assistants to understand REST APIs without manual conversion. Equal priority to P1 as it serves a distinct but equally important use case.

**Independent Test**: Can be tested independently by providing an OpenAPI specification file, configuring the MCP to load it, and asking the AI assistant questions about API operations. Delivers value for API documentation scenarios.

**Acceptance Scenarios**:

1. **Given** an OpenAPI 3.0 specification defining REST endpoints, **When** user asks "How do I create a new user?", **Then** AI assistant locates the relevant POST endpoint, presents the operation description, required parameters, request body schema, and success response format

2. **Given** OpenAPI specs with tagged operations (e.g., "Users", "Authentication", "Billing"), **When** user asks "Show all user-related endpoints", **Then** AI assistant returns all operations tagged with "Users" organized hierarchically

3. **Given** OpenAPI schema definitions for data models, **When** user asks "What fields does the User object have?", **Then** AI assistant retrieves and presents the schema with field names, types, descriptions, and validation rules

---

### User Story 3 - Cross-Platform Compatibility (Priority: P2)

A development team uses multiple AI tools - some developers use Claude Desktop while others use VS Code with GitHub Copilot. They configure the same MCP server to work with both platforms, and all team members can query documentation using their preferred AI assistant without compatibility issues.

**Why this priority**: Ensures broad adoption and prevents vendor lock-in. While valuable, it depends on the core navigation capabilities being implemented first (P1 stories).

**Independent Test**: Can be tested by configuring the MCP server in both Claude Desktop configuration and VS Code MCP configuration, then verifying that the same documentation queries work in both environments. Delivers value for teams using heterogeneous AI tooling.

**Acceptance Scenarios**:

1. **Given** an MCP server configured for local execution, **When** developer adds configuration to Claude Desktop config file, **Then** Claude can successfully list documentation categories and navigate content

2. **Given** the same MCP server, **When** developer adds configuration to VS Code .vscode/mcp.json with workspace-relative paths, **Then** GitHub Copilot Chat can query the same documentation

3. **Given** MCP server running as remote HTTP service, **When** both Claude Desktop and VS Code are configured with the remote server URL, **Then** both AI assistants can access documentation with proper authentication

---

### User Story 4 - Multi-Source Documentation Aggregation (Priority: P3)

A large project has documentation scattered across multiple locations: markdown guides in the `/docs` folder, API specifications in `/specs/openapi`, and additional tutorials in a separate repository. The developer configures the MCP server to aggregate all these sources into a unified hierarchical view, and the AI assistant can search and navigate across all sources seamlessly.

**Why this priority**: Addresses complex real-world scenarios but requires core functionality to be working first. Lower priority because single-source navigation already delivers significant value.

**Independent Test**: Can be tested by configuring multiple documentation source paths in the MCP configuration, then verifying that queries return results from all configured sources with proper categorization. Delivers value for large projects with distributed documentation.

**Acceptance Scenarios**:

1. **Given** multiple documentation source paths configured (e.g., `./docs`, `./api-specs`, `./external/wiki`), **When** user asks "Show all available documentation", **Then** AI assistant presents a unified hierarchy showing all sources with clear labels indicating origin

2. **Given** overlapping category names across different sources (e.g., both have "Tutorials"), **When** user navigates to "Tutorials", **Then** AI assistant presents merged content with source attribution

3. **Given** documentation sources with different formats (markdown in one, OpenAPI in another), **When** user searches across all content, **Then** results include matches from all format types with appropriate context

---

### User Story 5 - Secure Documentation Access with Path Validation (Priority: P2)

A developer configures the MCP server with a documentation root directory. When the AI assistant queries documentation, the server validates all path requests to prevent directory traversal attacks, blocks access to hidden files (starting with `.`), and only serves files from allowed directories. Malicious or malformed queries are rejected with clear error messages.

**Why this priority**: Security is critical for any file-system access tool, especially one exposed to AI agents. Must be implemented before production use but can follow initial prototyping.

**Independent Test**: Can be tested by attempting various malicious path patterns (e.g., `../../etc/passwd`, `~/.ssh/id_rsa`) and verifying they are blocked, while legitimate documentation paths work correctly. Delivers essential security guarantees.

**Acceptance Scenarios**:

1. **Given** MCP server configured with documentation root `/home/user/project/docs`, **When** AI assistant attempts to access `../../etc/passwd`, **Then** server blocks the request and returns an error indicating path is outside allowed directory

2. **Given** documentation directory containing hidden files (`.git`, `.env`), **When** AI assistant queries for files, **Then** hidden files are not listed or accessible

3. **Given** documentation containing both markdown and binary files, **When** AI assistant queries content, **Then** only allowed file types (markdown, YAML, JSON) are accessible with proper content validation

---

### Edge Cases

- **Empty documentation directories**: What happens when a configured category folder exists but contains no markdown files? System should return empty list with clear indication rather than error.

- **Malformed YAML frontmatter**: How does system handle markdown files with invalid YAML in frontmatter? System should gracefully fall back to treating the file as plain markdown without metadata.

- **Very large documentation sets**: How does system perform when documentation exceeds 10GB with thousands of files? System should implement caching and pagination to handle large sets efficiently (cache timeout: 1 hour).

- **Concurrent AI queries**: How does system handle multiple AI assistants querying simultaneously? System should support at least 10 concurrent queries without performance degradation.

- **Missing OpenAPI required fields**: What happens when OpenAPI spec is incomplete or invalid? System should validate specs on load and provide clear error messages indicating which fields are missing.

- **Circular symbolic links in docs**: How does system handle symlinks that create cycles? System should detect and break cycles to prevent infinite traversal loops.

- **Unicode and special characters in filenames**: How are non-ASCII characters handled in file paths and content? System should properly handle UTF-8 encoding throughout.

- **Documentation updates while server is running**: Should changes to files be reflected immediately or after cache expiration? System should detect file changes and invalidate relevant cache entries, with configurable refresh intervals.

- **OpenAPI spec version mismatches**: How does system handle OpenAPI 2.0 (Swagger) vs 3.0 vs 3.1? System should support OpenAPI 3.x primarily, with clear error for unsupported versions.

- **AI assistant disconnection mid-query**: What happens if the AI client disconnects during a long search operation? System should implement proper timeout handling and cleanup of abandoned queries.

## Requirements *(mandatory)*

### Functional Requirements

**Navigation & Hierarchy**

- **FR-001**: System MUST support hierarchical navigation of documentation organized in nested directory structures, with unlimited depth
- **FR-002**: System MUST provide URI-based addressing for documentation resources following the pattern `docs://[category]/[section]/[document]`
- **FR-003**: System MUST return breadcrumb navigation context showing the path from root to current document location
- **FR-004**: System MUST list available child items (subdirectories and documents) when navigating to a category level
- **FR-005**: System MUST provide parent navigation capability to move up the hierarchy

**Markdown Support**

- **FR-006**: System MUST parse markdown files and extract content for AI assistant consumption
- **FR-007**: System MUST parse YAML frontmatter in markdown files to extract metadata (title, tags, category, order, parent)
- **FR-008**: System MUST support markdown files with extensions `.md` and `.mdx`
- **FR-009**: System MUST preserve code blocks and formatting when presenting markdown content to AI assistants
- **FR-010**: System MUST gracefully handle markdown files without frontmatter by falling back to filename-based titles

**OpenAPI Integration**

- **FR-011**: System MUST load and parse OpenAPI 3.x specification files (YAML and JSON formats)
- **FR-012**: System MUST expose API endpoints from OpenAPI specs as queryable documentation resources
- **FR-013**: System MUST organize API operations hierarchically by OpenAPI tags (e.g., `api://[tag]/[operationId]`)
- **FR-014**: System MUST extract and present operation descriptions, parameters, request schemas, and response schemas from OpenAPI specs
- **FR-015**: System MUST handle OpenAPI schema definitions ($ref references) and resolve them when presenting data models
- **FR-016**: System MUST validate OpenAPI specifications on load and report validation errors clearly

**Search & Discovery**

- **FR-017**: System MUST provide full-text search across all markdown content with relevance ranking
- **FR-018**: System MUST support metadata-based search by tags, categories, and custom frontmatter fields
- **FR-019**: System MUST return search results with hierarchical context (breadcrumbs) showing document location
- **FR-020**: System MUST support filtering searches by category or documentation source
- **FR-021**: System MUST limit search results to a configurable maximum (default: 10 results per query)
- **FR-022**: System MUST provide a table of contents operation that returns the complete documentation hierarchy tree

**Configuration**

- **FR-023**: System MUST support configuration via environment variables for documentation root path
- **FR-024**: System MUST support configuration via YAML/JSON files for multiple documentation sources
- **FR-025**: System MUST allow configuration of multiple OpenAPI specification files to load
- **FR-026**: System MUST support both absolute and workspace-relative paths in configuration
- **FR-027**: System MUST support per-source configuration of file inclusion/exclusion patterns

**Security**

- **FR-028**: System MUST validate all file path requests to prevent directory traversal attacks (e.g., blocking `../` patterns)
- **FR-029**: System MUST restrict access to hidden files and directories (those starting with `.`)
- **FR-030**: System MUST sanitize search queries to prevent injection attacks
- **FR-031**: System MUST enforce that all resolved file paths remain within configured documentation root directories
- **FR-032**: System MUST sanitize OpenAPI descriptions to prevent prompt injection attacks in AI assistants
- **FR-033**: System MUST log all file access attempts for security audit purposes

**Cross-Platform Compatibility**

- **FR-034**: System MUST support stdio transport for local AI assistant integration (Claude Desktop, VS Code)
- **FR-035**: System MUST support HTTP transport for remote server deployment with team-wide access
- **FR-036**: System MUST provide configuration examples for both Claude Desktop and VS Code MCP integration
- **FR-037**: System MUST function with AI assistants that support only tool-based interactions (no resources)
- **FR-038**: System MUST provide authentication support for remote deployments (minimum: API token authentication)

**Performance & Caching**

- **FR-039**: System MUST implement caching for parsed markdown and OpenAPI content to improve query response times
- **FR-040**: System MUST support configurable cache TTL (time-to-live), with default of 1 hour
- **FR-041**: System MUST detect file system changes and invalidate relevant cache entries
- **FR-042**: System MUST handle documentation sets up to 10GB in size with acceptable performance
- **FR-043**: System MUST support at least 10 concurrent AI assistant queries without performance degradation

**Error Handling**

- **FR-044**: System MUST return clear error messages when documentation files are not found
- **FR-045**: System MUST return clear error messages when OpenAPI specifications are invalid
- **FR-046**: System MUST gracefully handle malformed markdown or YAML frontmatter without crashing
- **FR-047**: System MUST provide timeout protection for long-running search operations (default: 30 seconds)

### Key Entities

- **Documentation Source**: Represents a configured location containing documentation files (local directory path, inclusion/exclusion patterns, category label, format type)

- **Document**: Individual markdown file with optional frontmatter metadata (file path, title, content, tags, category, hierarchical position)

- **Category**: Logical grouping of documentation at any hierarchy level (name, parent category, child categories, contained documents, depth level)

- **OpenAPI Specification**: API documentation spec defining endpoints and schemas (file path, version, tags, operations, schema definitions)

- **API Operation**: Individual endpoint from OpenAPI spec (operation ID, HTTP method, path, tag, parameters, request body, responses, description)

- **Search Result**: Match from a search query (document reference, excerpt with matched content, breadcrumb path, relevance score)

- **Navigation Context**: Current position in documentation hierarchy (current path, parent path, child items, breadcrumbs, available navigation options)

- **Cache Entry**: Cached parsed content for performance (resource URI, parsed content, timestamp, TTL, file modification time)

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Performance Metrics**

- **SC-001**: AI assistants can retrieve specific documentation sections in under 2 seconds for documentation sets up to 1GB
- **SC-002**: Search operations return results in under 3 seconds for queries across documentation sets containing up to 5,000 documents
- **SC-003**: System supports 10 concurrent AI assistant queries with response time degradation not exceeding 20%
- **SC-004**: Navigation operations (list categories, get breadcrumbs) complete in under 500 milliseconds

**Functionality Metrics**

- **SC-005**: AI assistants successfully locate requested documentation on first attempt in 90% of queries when the content exists
- **SC-006**: Search results include hierarchical context (breadcrumbs) showing document location for 100% of results
- **SC-007**: OpenAPI endpoints are successfully parsed and queryable for 95% of valid OpenAPI 3.x specifications
- **SC-008**: System prevents 100% of directory traversal attempts through path validation

**Compatibility Metrics**

- **SC-009**: MCP server successfully integrates with Claude Desktop with zero configuration errors following documented setup
- **SC-010**: MCP server successfully integrates with VS Code GitHub Copilot with zero configuration errors following documented setup
- **SC-011**: Same MCP configuration works in both Claude Desktop and VS Code with only transport-specific changes (config file location)

**Usability Metrics**

- **SC-012**: Developers can configure basic MCP server (single documentation source) in under 5 minutes following quickstart guide
- **SC-013**: Error messages clearly indicate the problem and suggest resolution for 100% of common configuration errors (missing path, invalid spec, permission denied)
- **SC-014**: AI assistants receive properly formatted documentation content that preserves markdown code blocks and structure for 100% of documents

**Scalability Metrics**

- **SC-015**: System handles documentation sets up to 10GB without crashes or memory exhaustion
- **SC-016**: Cache reduces repeated query response time by at least 70% compared to uncached queries
- **SC-017**: System processes documentation directories containing 10,000+ files without exceeding 1GB memory usage

**Security Metrics**

- **SC-018**: System blocks 100% of attempted directory traversal attacks (tested with standard attack patterns)
- **SC-019**: Security audit logs capture all file access attempts with timestamp and query details for 100% of operations
- **SC-020**: OpenAPI description sanitization removes or escapes 100% of tested prompt injection patterns

## Assumptions

**Format Support**
- Initial release focuses on markdown (`.md`, `.mdx`) and OpenAPI 3.x only. Additional formats (reStructuredText, AsciiDoc) can be added in future versions based on demand.
- YAML frontmatter follows common conventions (title, tags, category, order, parent fields). Non-standard fields are preserved but not used for system operations.

**Deployment Model**
- System supports both personal developer use (local stdio) and team use (remote HTTP server). No multi-tenant isolation is implemented initially - shared servers assume trusted users.
- Default deployment model is single repository/project focus. Multi-repository aggregation is supported through configuration but requires manual path setup.

**Access Model**
- System provides read-only access to documentation. No write operations (document editing, creation, deletion) through the MCP interface.
- Authentication for remote servers uses standard API token mechanism. OAuth and other advanced authentication methods can be added in future versions.

**Performance Assumptions**
- Documentation sets assumed to be primarily text-based (markdown, YAML, JSON). Binary files are excluded from search and parsing.
- Cache assumes file system modification timestamps are reliable for invalidation. Networks file systems with timestamp synchronization issues may require manual cache clearing.

**OpenAPI Assumptions**
- OpenAPI specifications follow standard OpenAPI 3.0 or 3.1 format. Older Swagger 2.0 specs should be upgraded using standard conversion tools before use.
- API endpoints in OpenAPI specs are assumed to be documented with descriptions suitable for AI consumption. Minimal or missing descriptions reduce AI assistant effectiveness.

**Cross-Platform Assumptions**
- AI assistants (Claude, Copilot) implement the Model Context Protocol specification correctly according to official standards.
- Local file system access patterns (paths, permissions) follow POSIX conventions on Linux/macOS and Windows conventions on Windows.

**Concurrency Assumptions**
- Concurrent query support assumes independent read operations. No coordination needed between multiple AI assistants querying simultaneously.
- File system changes during operation are eventually consistent through cache invalidation, not immediate.
