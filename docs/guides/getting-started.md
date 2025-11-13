---
title: Getting Started Guide
tags: [guide, quickstart, setup]
category: guides
order: 1
---

# Getting Started with Hierarchical Documentation MCP

This guide will help you set up and configure the Hierarchical Documentation MCP server for use with AI assistants like Claude Desktop or GitHub Copilot.

## Installation

Install the package using pip:

```bash
pip install hierarchical-docs-mcp
```

Or install from source:

```bash
git clone https://github.com/esola-thomas/Markdown-MCP
cd Markdown-MCP
pip install -e .
```

## Quick Setup

1. Configure your documentation root directory:

```bash
export DOCS_ROOT=/path/to/your/docs
```

2. Start the MCP server:

```bash
hierarchical-docs-mcp
```

3. Configure your AI assistant to connect to the server (see platform-specific guides below).

## Next Steps

- Read the [Authentication Guide](security/authentication.md) to secure your documentation
- Learn about [OpenAPI integration](#) for API documentation
- Explore [advanced configuration](#) options
