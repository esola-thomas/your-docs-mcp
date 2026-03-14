# Documentation MCP Server

> Turn your documentation into an intelligent, AI-accessible knowledge base

Give AI assistants like Claude, ChatGPT, and Copilot structured access to your documentation through the Model Context Protocol (MCP). Navigate hierarchical docs, search semantically, generate PDFs, and browse via web interface—all from a single server.

## ⚡ Quick Start (60 seconds)

```bash
# Install from PyPI
pip install your-docs-mcp

# Point to your docs folder
export DOCS_ROOT=/path/to/your/docs

# Start MCP server + web interface
your-docs-server
```

**That's it!** Your docs are now:
- ✅ Accessible to AI assistants via MCP
- ✅ Browseable at http://localhost:8123
- ✅ Searchable with full-text and metadata filters
- ✅ Ready for PDF generation

## 🎯 What Can You Do?

### For AI Assistants
Once connected, ask your AI:
- *"Show me the getting started guide"*
- *"List all API endpoints for user management"*
- *"Search for authentication documentation"*
- *"Generate a PDF of all documentation"*

### For Humans
- Browse documentation in your browser at `http://localhost:8123`
- Search with semantic understanding (with `[vector]` extra)
- Generate PDF releases with custom branding
- Access documentation via REST API

## 📦 Installation

### From PyPI (Recommended)

**Basic install** (keyword search only):
```bash
pip install your-docs-mcp
```

**With semantic search** (CPU-optimized, recommended):
```bash
pip install "your-docs-mcp[vector]" --extra-index-url https://download.pytorch.org/whl/cpu
```

**With PDF generation**:
```bash
pip install "your-docs-mcp[pdf]"

# Requires system dependencies
# Ubuntu/Debian: sudo apt install pandoc texlive-xetex texlive-latex-extra
# macOS: brew install pandoc basictex
```

**All features**:
```bash
pip install "your-docs-mcp[vector,pdf]" --extra-index-url https://download.pytorch.org/whl/cpu
```

### From Source

```bash
git clone https://github.com/esola-thomas/your-docs-mcp
cd your-docs-mcp
pip install -e ".[vector,pdf]" --extra-index-url https://download.pytorch.org/whl/cpu
```

## 🔧 Setup for AI Assistants

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "docs": {
      "command": "your-docs-mcp",
      "env": {
        "DOCS_ROOT": "/absolute/path/to/your/docs"
      }
    }
  }
}
```

**VS Code** (create `.vscode/mcp.json`):
```json
{
  "servers": {
    "docs": {
      "command": "your-docs-mcp",
      "env": {
        "DOCS_ROOT": "${workspaceFolder}/docs"
      }
    }
  }
}
```

**Other MCP Clients**: Use the `your-docs-mcp` command with `DOCS_ROOT` environment variable.

## 🛠️ Available MCP Tools

Once connected, AI assistants can use these tools:

| Tool | Description |
|------|-------------|
| `search_documentation` | Full-text search with relevance scoring and hierarchical context |
| `navigate_to` | Navigate to specific docs by URI (e.g., `docs://guides/quickstart`) |
| `get_table_of_contents` | Get complete documentation hierarchy |
| `get_document` | Retrieve full document content with metadata |
| `search_by_tags` | Filter documentation by tags (e.g., `[api, authentication]`) |
| `get_all_tags` | List all available tags across documentation |
| `generate_pdf_release` | Generate PDF documentation with custom branding |

## 📄 Supported Documentation Formats

**Markdown with YAML frontmatter**:
```markdown
---
title: Getting Started Guide
tags: [guide, quickstart]
category: guides
order: 1
---

# Getting Started

Your content here...
```

**OpenAPI 3.x Specifications** (`.yaml`, `.json`):
```yaml
openapi: 3.0.3
info:
  title: My API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
```

## 📊 Key Features

- **🗂️ Hierarchical Navigation**: Unlimited nesting depth, automatic breadcrumbs
- **🔍 Intelligent Search**: Full-text + semantic search (with vector extra)
- **📝 Markdown & OpenAPI**: Parse markdown with frontmatter + OpenAPI specs
- **🌐 Web Interface**: Browser-based documentation access (same tools as AI)
- **📑 PDF Generation**: Create professional PDF releases with branding
- **🔒 Security**: Path validation, query sanitization, audit logging
- **⚡ Performance**: Smart caching with automatic invalidation
- **🔌 Cross-Platform**: Works with Claude Desktop, VS Code, any MCP client

## 🌐 Web Interface & REST API

### Access the Web UI

```bash
your-docs-server  # Starts MCP + web server
# Or
your-docs-web     # Web server only (no MCP)
```

Open **http://localhost:8123** in your browser.

**Features**:
- 🔍 Search with relevance scoring and highlighted excerpts
- 📚 Browse hierarchical table of contents
- 🏷️ Filter by tags
- 📖 View formatted documents
- 📊 Real-time stats

### REST API

**Endpoints**:
```bash
GET  /api/health              # Server status
POST /api/search              # Search docs
POST /api/navigate            # Navigate to URI
POST /api/toc                 # Table of contents
POST /api/search-by-tags      # Tag search
POST /api/document            # Get document
POST /api/pdf-generate        # Generate PDF
```

**Example**:
```bash
curl "http://localhost:8123/api/search?query=authentication"
curl -X POST "http://localhost:8123/api/pdf-generate" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Docs", "subtitle": "v1.0", "version": "1.0.0"}'
```

## 📑 PDF Generation

Generate professional PDF documentation releases:

```bash
# Via MCP (ask your AI assistant):
"Generate a PDF of all documentation titled 'Product Docs' version 1.0"

# Via REST API:
curl -X POST "http://localhost:8123/api/pdf-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Documentation",
    "subtitle": "Complete Technical Guide",
    "author": "Your Team",
    "version": "1.0.0",
    "confidential": false
  }'

# Via command line script:
DOCS_ROOT=/path/to/docs ./scripts/generate-docs-pdf.sh \
  --title "My Docs" \
  --subtitle "Technical Guide" \
  --author "Team Name" \
  1.0.0
```

**PDF Features**:
- 📚 Automatic table of contents with page numbers
- 🎨 Custom branding (title, subtitle, author, owner)
- 🔒 Confidential markings (watermark, headers/footers)
- 🔗 Preserves document hierarchy and navigation
- 📄 Professional LaTeX rendering via Pandoc

**Requirements** (system packages):
```bash
# Ubuntu/Debian
sudo apt install pandoc texlive-xetex texlive-latex-extra

# macOS
brew install pandoc basictex
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
DOCS_ROOT=/path/to/docs                    # Documentation root directory

# Optional
MCP_DOCS_CACHE_TTL=3600                    # Cache TTL in seconds
MCP_DOCS_SEARCH_LIMIT=10                   # Max search results
MCP_DOCS_OPENAPI_SPECS=/path/to/spec.yaml # OpenAPI spec paths (comma-separated)

# Web Server (for your-docs-server)
MCP_DOCS_ENABLE_WEB_SERVER=true            # Enable web interface
MCP_DOCS_WEB_HOST=127.0.0.1               # Web server host
MCP_DOCS_WEB_PORT=8123                     # Web server port
MCP_DOCS_CORS_ORIGINS=*                    # Allowed CORS origins (comma-separated, default: *)

# Logging
LOG_LEVEL=INFO                             # DEBUG, INFO, WARNING, ERROR
```

### Multi-Source Configuration

For complex setups, create `.mcp-docs.yaml`:

```yaml
sources:
  - path: ./docs
    category: guides
    label: User Guides
    recursive: true

  - path: ./api-specs
    category: api
    label: API Reference
    format_type: openapi

cache:
  ttl: 3600
  max_memory_mb: 500

security:
  allow_hidden_files: false
  audit_logging: true
```

### Running Modes

```bash
# 1. MCP Server + Web Interface (recommended)
your-docs-server

# 2. MCP Server only (for AI clients)
your-docs-mcp

# 3. Web Server only (no MCP)
your-docs-web
```

## 🔒 Security Features

- ✅ **Path Validation**: Prevents directory traversal attacks
- ✅ **Hidden Files Exclusion**: `.` files excluded by default
- ✅ **Query Sanitization**: Search queries sanitized against injection
- ✅ **Audit Logging**: All file access logged for security review

## 🧪 Development

### Setup

```bash
git clone https://github.com/esola-thomas/your-docs-mcp
cd your-docs-mcp
pip install -e ".[dev,vector,pdf]" --extra-index-url https://download.pytorch.org/whl/cpu
```

### Testing

```bash
pytest                              # Run all tests
pytest -m unit                      # Unit tests only
pytest --cov=docs_mcp              # With coverage
```

### Code Quality

```bash
ruff check docs_mcp                 # Linting
mypy docs_mcp                       # Type checking
pytest --cov=docs_mcp --cov-report=html  # Coverage report
```

### Project Structure

```
docs_mcp/
├── models/          # Data models (Document, Category, OpenAPI)
├── handlers/        # MCP protocol handlers (tools, resources)
├── services/        # Core logic (markdown, search, hierarchy)
├── security/        # Security validation and sanitization
└── utils/           # Logging and utilities
```

## 📚 Example: Try It Now

This repo includes sample docs in the `docs/` folder:

```bash
# Clone and test
git clone https://github.com/esola-thomas/your-docs-mcp
cd your-docs-mcp
export DOCS_ROOT=$(pwd)/docs
your-docs-server
```

The sample docs demonstrate:
- ✅ Hierarchical structure with nested categories
- ✅ Markdown with YAML frontmatter
- ✅ OpenAPI specification integration
- ✅ Best practices for organization

## 💡 Tips & Best Practices

**Document Organization**:
```
docs/
├── README.md           # Overview (processed first)
├── guides/
│   ├── README.md       # Category overview
│   ├── quickstart.md
│   └── advanced.md
└── api/
    ├── README.md
    └── reference.md
```

**Frontmatter**:
```yaml
---
title: Clear, Descriptive Title
tags: [category, topic, level]
category: guides  # Maps to directory structure
order: 1          # Controls display order
---
```

**For Best Results**:
- Use descriptive titles in frontmatter
- Tag documents consistently
- Organize by topic in subdirectories
- Include README.md in each category
- Keep documents focused and modular

## 🤝 Contributing

Contributions welcome! See [Contributing Guide](docs/development/contributing.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Homepage**: https://github.com/esola-thomas/your-docs-mcp
- **Documentation**: [docs/](docs/)
- **Issues**: https://github.com/esola-thomas/your-docs-mcp/issues
- **MCP Spec**: https://modelcontextprotocol.io
- **PyPI**: https://pypi.org/project/your-docs-mcp/

---

**Questions?** Open an [issue](https://github.com/esola-thomas/your-docs-mcp/issues) or check the [documentation](docs/).
