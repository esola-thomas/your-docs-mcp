---
paths:
  - "docs_mcp/security/**"
---

# Security Module Rules

- Validate ALL inputs at system boundaries — never trust caller data
- Use `pathlib.Path.resolve()` for all path operations to prevent traversal
- Test for directory traversal patterns: `../`, `..%2F`, `..%252F`, encoded variants
- Sanitize all query inputs before processing (SQL injection, command injection)
- Include attack pattern tests in corresponding test files
- Audit log all security-relevant operations via `docs_mcp.utils.logger`
- Hidden files (dotfiles) must be excluded from document scanning by default
- Path validation must be the first operation before any file access
- Raise specific security exceptions (not generic Exception)
- Never expose internal file paths or stack traces in error responses
