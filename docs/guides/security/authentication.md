---
title: Authentication and Security
tags: [security, authentication, guide]
category: guides
parent: getting-started
order: 2
---

# Authentication and Security

## Overview

The Hierarchical Documentation MCP server implements multiple security layers to protect your documentation and prevent unauthorized access.

## Path Validation

All file system access is validated to prevent directory traversal attacks:

- Paths are resolved to absolute paths and checked against allowed directories
- Hidden files (starting with `.`) are automatically excluded
- Symbolic links are followed but validated against allowed directories

## Query Sanitization

Search queries and user input are sanitized to prevent:

- Injection attacks
- Malformed regex patterns
- Excessive resource consumption

## Remote Deployment

When deploying the MCP server as a remote HTTP service, use API token authentication:

```yaml
# .mcp-docs.yaml
authentication:
  enabled: true
  type: token
  tokens:
    - name: development
      value: ${MCP_AUTH_TOKEN}
```

## Best Practices

1. Never expose the MCP server directly to the internet without authentication
2. Use workspace-relative paths in configuration to prevent absolute path leaks
3. Regularly review security audit logs for suspicious activity
4. Keep the server and dependencies updated
